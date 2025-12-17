from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload
import random

from app.models import User, Match, MediaItem, UserInteraction, Message
from app.services.vector import vector_service


class MatchingService:
    """
    Core matching engine using pgvector for efficient similarity search.
    
    Matching Strategy:
    1. Vector similarity search using pgvector (cosine distance)
    2. Direct item overlap calculation
    3. Rating delta analysis
    4. Final weighted score computation
    """
    
    # Matching thresholds
    MIN_COMPATIBILITY_SCORE = 50.0  # Minimum score to suggest a match
    MAX_MATCHES_PER_RUN = 10  # Limit matches generated per request
    
    async def find_potential_matches(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 10,
        exclude_existing: bool = True,
    ) -> List[Tuple[User, float]]:
        """
        Find potential matches for a user using pgvector similarity search.
        
        Returns list of (User, compatibility_score) tuples.
        """
        # Get current user with their vector
        user = await db.get(User, user_id)
        if not user or user.vibe_vector is None:
            return []
        
        # Build exclusion list (already matched users)
        excluded_ids = {user_id}
        if exclude_existing:
            existing_matches = await db.execute(
                select(Match.user_a_id, Match.user_b_id).where(
                    or_(Match.user_a_id == user_id, Match.user_b_id == user_id)
                )
            )
            for row in existing_matches:
                excluded_ids.add(row.user_a_id)
                excluded_ids.add(row.user_b_id)
        
        # Pgvector cosine similarity search
        # Using raw SQL for optimal pgvector performance
        similarity_query = text("""
            SELECT 
                id,
                1 - (vibe_vector <=> :user_vector) as similarity
            FROM users
            WHERE 
                id != :user_id
                AND id != ALL(:excluded_ids)
                AND vibe_vector IS NOT NULL
            ORDER BY vibe_vector <=> :user_vector
            LIMIT :limit
        """)
        
        result = await db.execute(
            similarity_query,
            {
                "user_vector": str(user.vibe_vector),
                "user_id": str(user_id),
                "excluded_ids": [str(uid) for uid in excluded_ids],
                "limit": limit * 2,  # Fetch extra for filtering
            }
        )
        
        candidates = result.fetchall()
        
        # Calculate full compatibility scores
        matches = []
        for candidate_id, vibe_similarity in candidates:
            candidate = await db.get(User, candidate_id)
            if not candidate or not candidate.vibe_vector:
                continue
            
            # Get shared items and rating delta
            shared_count, avg_delta = await self._calculate_item_overlap(
                db, user_id, UUID(candidate_id)
            )
            
            # Calculate final score
            score = vector_service.calculate_compatibility_score(
                user_a_vector=list(user.vibe_vector),
                user_b_vector=list(candidate.vibe_vector),
                shared_items_count=shared_count,
                rating_delta_avg=avg_delta,
            )
            
            if score >= self.MIN_COMPATIBILITY_SCORE:
                matches.append((candidate, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches[:limit]
    
    async def _calculate_item_overlap(
        self,
        db: AsyncSession,
        user_a_id: UUID,
        user_b_id: UUID,
    ) -> Tuple[int, float]:
        """
        Calculate shared items and average rating delta between two users.
        
        Returns (shared_count, average_rating_delta).
        """
        # Find shared media items with ratings
        overlap_query = text("""
            SELECT 
                a.media_id,
                a.rating as rating_a,
                b.rating as rating_b
            FROM user_interactions a
            INNER JOIN user_interactions b 
                ON a.media_id = b.media_id
            WHERE 
                a.user_id = :user_a
                AND b.user_id = :user_b
                AND a.rating IS NOT NULL
                AND b.rating IS NOT NULL
        """)
        
        result = await db.execute(
            overlap_query,
            {"user_a": str(user_a_id), "user_b": str(user_b_id)}
        )
        
        overlaps = result.fetchall()
        
        if not overlaps:
            # Check for items without ratings
            count_query = text("""
                SELECT COUNT(DISTINCT a.media_id)
                FROM user_interactions a
                INNER JOIN user_interactions b ON a.media_id = b.media_id
                WHERE a.user_id = :user_a AND b.user_id = :user_b
            """)
            count_result = await db.execute(
                count_query,
                {"user_a": str(user_a_id), "user_b": str(user_b_id)}
            )
            shared_count = count_result.scalar() or 0
            return shared_count, 1.0  # Default delta if no ratings
        
        # Calculate average rating delta
        total_delta = sum(abs(float(r.rating_a) - float(r.rating_b)) for r in overlaps)
        avg_delta = total_delta / len(overlaps)
        
        return len(overlaps), avg_delta
    
    async def get_shared_items(
        self,
        db: AsyncSession,
        user_a_id: UUID,
        user_b_id: UUID,
        limit: int = 10,
    ) -> List[dict]:
        """Get list of shared media items between two users."""
        query = text("""
            SELECT DISTINCT
                m.id,
                m.external_id,
                m.media_type,
                m.title,
                m.image_url,
                a.rating as rating_a,
                b.rating as rating_b,
                a.interaction_type as type_a,
                b.interaction_type as type_b
            FROM media_items m
            INNER JOIN user_interactions a ON m.id = a.media_id AND a.user_id = :user_a
            INNER JOIN user_interactions b ON m.id = b.media_id AND b.user_id = :user_b
            ORDER BY 
                CASE WHEN a.interaction_type = 'top4' OR b.interaction_type = 'top4' THEN 0 ELSE 1 END,
                m.title
            LIMIT :limit
        """)
        
        result = await db.execute(
            query,
            {"user_a": str(user_a_id), "user_b": str(user_b_id), "limit": limit}
        )
        
        items = []
        for row in result.fetchall():
            items.append({
                "id": row.id,
                "external_id": row.external_id,
                "media_type": row.media_type,
                "title": row.title,
                "image_url": row.image_url,
                "rating_a": float(row.rating_a) if row.rating_a else None,
                "rating_b": float(row.rating_b) if row.rating_b else None,
                "is_top4_a": row.type_a == "top4",
                "is_top4_b": row.type_b == "top4",
            })
        
        return items
    
    async def create_match(
        self,
        db: AsyncSession,
        user_a_id: UUID,
        user_b_id: UUID,
        score: float,
    ) -> Match:
        """Create a new match between two users with an icebreaker."""
        # Get shared items for icebreaker generation
        shared_items = await self.get_shared_items(db, user_a_id, user_b_id, limit=5)
        
        # Generate icebreaker prompt
        icebreaker = self._generate_icebreaker(shared_items)
        
        # Create match
        match = Match(
            user_a_id=user_a_id,
            user_b_id=user_b_id,
            compatibility_score=score,
            shared_items=[item["id"] for item in shared_items],
            icebreaker_prompt=icebreaker,
            status="pending",
        )
        
        db.add(match)
        await db.flush()
        
        # Create system message with icebreaker
        if icebreaker:
            system_message = Message(
                match_id=match.id,
                sender_id=user_a_id,  # System uses user_a as placeholder
                content=icebreaker,
                is_system_message=True,
            )
            db.add(system_message)
        
        await db.commit()
        await db.refresh(match)
        
        return match
    
    def _generate_icebreaker(self, shared_items: List[dict]) -> str:
        """Generate a conversation starter based on shared items."""
        if not shared_items:
            return "You two have similar cultural vibes! Start by sharing your current favorite song or movie."
        
        # Prioritize interesting scenarios
        icebreakers = []
        
        for item in shared_items:
            title = item["title"]
            media_type = item["media_type"]
            rating_a = item.get("rating_a")
            rating_b = item.get("rating_b")
            
            # Both have it in Top 4
            if item.get("is_top4_a") and item.get("is_top4_b"):
                if media_type == "movie":
                    icebreakers.append(f"🎬 You BOTH have '{title}' in your Top 4 movies! What scene lives rent-free in your head?")
                else:
                    icebreakers.append(f"🎵 You BOTH have '{title}' in your Top 4! What's your go-to track?")
            
            # Different ratings = debate opportunity
            elif rating_a and rating_b and abs(rating_a - rating_b) >= 2:
                higher_rating = "User A" if rating_a > rating_b else "User B"
                icebreakers.append(
                    f"⚔️ Rating showdown! One of you gave '{title}' {max(rating_a, rating_b)} stars, "
                    f"the other gave it {min(rating_a, rating_b)}. Defend your rating!"
                )
            
            # Same high rating
            elif rating_a and rating_b and rating_a >= 4 and rating_b >= 4:
                icebreakers.append(f"💫 You both rated '{title}' highly! What made it special for you?")
        
        if icebreakers:
            return random.choice(icebreakers)
        
        # Fallback to mentioning a shared item
        item = shared_items[0]
        return f"🎯 You both have '{item['title']}' in your library. Great taste recognizes great taste!"
    
    async def run_matching_job(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> List[Match]:
        """
        Run matching job for a specific user.
        Creates new matches for users above the threshold.
        """
        potential_matches = await self.find_potential_matches(
            db, user_id, limit=self.MAX_MATCHES_PER_RUN
        )
        
        created_matches = []
        for candidate, score in potential_matches:
            match = await self.create_match(db, user_id, candidate.id, score)
            created_matches.append(match)
        
        return created_matches


# Singleton
matching_service = MatchingService()
