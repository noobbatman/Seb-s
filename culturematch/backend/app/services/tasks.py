"""
Background tasks for async processing.
"""
from typing import List, Dict, Any, cast
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, UserInteraction, MediaItem
from app.services.vector import vector_service


async def update_user_vibe_vector(db: AsyncSession, user_id: UUID) -> None:
    """
    Regenerate a user's vibe vector based on their current preferences.
    Should be called after:
    - Vibe check submission
    - Adding/removing Top 4 items
    - Significant interaction changes
    """
    user = await db.get(User, user_id)
    if not user:
        return
    
    # Get user's genres from their interactions
    genres = await _get_user_genres(db, user_id)
    
    # Get user's top artists
    artists = await _get_user_items_by_type(db, user_id, "artist")
    
    # Get user's top movies
    movies = await _get_user_items_by_type(db, user_id, "movie")
    
    # Generate combined vector
    vibe_answers = cast(Dict[str, Any], user.vibe_answers) if user.vibe_answers else {}
    vibe_vector = vector_service.generate_user_vibe_vector(
        vibe_answers=vibe_answers,
        genres=genres,
        artists=artists,
        movies=movies,
    )
    
    # Update user - using setattr for SQLAlchemy compatibility
    user.vibe_vector = vibe_vector  # type: ignore[assignment]
    await db.commit()


async def _get_user_genres(db: AsyncSession, user_id: UUID) -> List[str]:
    """Extract all genres from user's media items."""
    query = select(MediaItem.extra_data).join(
        UserInteraction, UserInteraction.media_id == MediaItem.id
    ).where(UserInteraction.user_id == user_id)
    
    result = await db.execute(query)
    
    genres: set[str] = set()
    for (extra_data,) in result:
        if extra_data and "genres" in extra_data:
            genres.update(extra_data["genres"])
    
    return list(genres)[:20]  # Limit to prevent embedding overflow


async def _get_user_items_by_type(
    db: AsyncSession,
    user_id: UUID,
    media_type: str,
    limit: int = 10,
) -> List[str]:
    """Get titles of user's media items by type, prioritizing Top 4."""
    query = (
        select(MediaItem.title, UserInteraction.interaction_type)
        .join(UserInteraction, UserInteraction.media_id == MediaItem.id)
        .where(
            UserInteraction.user_id == user_id,
            MediaItem.media_type == media_type,
        )
        .order_by(
            # Top 4 items first
            (UserInteraction.interaction_type == "top4").desc(),
            # Then by rating
            UserInteraction.rating.desc().nulls_last(),
        )
        .limit(limit)
    )
    
    result = await db.execute(query)
    return [title for title, _ in result]


async def batch_update_vectors(db: AsyncSession, user_ids: List[UUID]) -> int:
    """Update vectors for multiple users (useful for background jobs)."""
    updated = 0
    for user_id in user_ids:
        try:
            await update_user_vibe_vector(db, user_id)
            updated += 1
        except Exception:
            # Log error but continue with others
            pass
    return updated
