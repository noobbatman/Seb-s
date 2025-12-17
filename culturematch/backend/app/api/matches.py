from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from uuid import UUID

from app.core import get_db, get_current_user_id
from app.models import User, Match, Message, UserInteraction, MediaItem
from app.schemas import MatchResponse, MatchAction, MessageCreate, MessageResponse
from app.services import matching_service

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.post("/discover")
async def discover_matches(
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Discover and create new matches for the current user.
    Uses pgvector similarity search for efficient matching.
    """
    user = await db.get(User, UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.vibe_vector is None:
        raise HTTPException(
            status_code=400,
            detail="Complete your vibe check first to discover matches"
        )
    
    # Run matching algorithm
    created_matches = await matching_service.run_matching_job(
        db, UUID(user_id)
    )
    
    return {
        "message": f"Found {len(created_matches)} new matches!",
        "matches_created": len(created_matches),
        "match_ids": [str(m.id) for m in created_matches],
    }


@router.get("", response_model=List[MatchResponse])
async def get_my_matches(
    status: str = Query(None, pattern="^(pending|accepted|rejected|matched)$"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get current user's matches."""
    query = select(Match).where(
        or_(Match.user_a_id == user_id, Match.user_b_id == user_id)
    )
    
    if status:
        query = query.where(Match.status == status)
    
    query = query.order_by(Match.compatibility_score.desc())
    
    result = await db.execute(query)
    matches = result.scalars().all()
    
    # Transform to include matched_user instead of user_a/user_b
    response = []
    for match in matches:
        # Determine which user is the "other" user
        matched_user_id = match.user_b_id if str(match.user_a_id) == user_id else match.user_a_id
        user_result = await db.execute(select(User).where(User.id == matched_user_id))
        matched_user = user_result.scalar_one_or_none()
        
        if matched_user:
            # Fetch shared items
            shared_items = await matching_service.get_shared_items(
                db, UUID(user_id), UUID(str(matched_user_id)), limit=5
            )
            
            response.append({
                "id": match.id,
                "matched_user": matched_user,
                "compatibility_score": float(str(match.compatibility_score)),
                "shared_items": shared_items,
                "icebreaker_prompt": match.icebreaker_prompt,
                "status": match.status,
                "created_at": match.created_at,
            })
    
    return response


@router.post("/{match_id}/action")
async def respond_to_match(
    match_id: UUID,
    action: MatchAction,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Accept or reject a match."""
    result = await db.execute(
        select(Match).where(
            Match.id == match_id,
            or_(Match.user_a_id == user_id, Match.user_b_id == user_id),
        )
    )
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if match.status != "pending":
        raise HTTPException(status_code=400, detail="Match already processed")
    
    match.status = "accepted" if action.action == "accept" else "rejected"  # type: ignore[assignment]
    
    # If both users accept, status becomes "matched"
    # This simplified version just sets based on action
    
    await db.commit()
    
    return {"message": f"Match {action.action}ed", "status": match.status}


@router.get("/{match_id}/messages", response_model=List[MessageResponse])
async def get_match_messages(
    match_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get messages for a match."""
    # Verify user is part of this match
    result = await db.execute(
        select(Match).where(
            Match.id == match_id,
            or_(Match.user_a_id == user_id, Match.user_b_id == user_id),
        )
    )
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    query = select(Message).where(Message.match_id == match_id)
    
    if before:
        query = query.where(Message.id < before)
    
    query = query.order_by(Message.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return list(reversed(messages))  # Return in chronological order


@router.post("/{match_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    match_id: UUID,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Send a message in a match chat."""
    # Verify user is part of this match
    result = await db.execute(
        select(Match).where(
            Match.id == match_id,
            or_(Match.user_a_id == user_id, Match.user_b_id == user_id),
            Match.status == "matched",  # Can only message if matched
        )
    )
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found or not yet matched"
        )
    
    message = Message(
        match_id=match_id,
        sender_id=user_id,
        content=message_data.content,
        is_system_message=False,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return message
