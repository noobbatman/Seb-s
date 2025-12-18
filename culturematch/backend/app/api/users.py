from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.core import get_db, get_current_user_id
from app.models import User, MediaItem, UserInteraction
from app.schemas import (
    UserResponse,
    UserProfile,
    UserUpdate,
    VibeCheckSubmit,
    InteractionCreate,
    InteractionResponse,
    MediaItemResponse,
)
from app.services import update_user_vibe_vector, matching_service

router = APIRouter(prefix="/users", tags=["Users"])


# Vibe check questions configuration
VIBE_CHECK_QUESTIONS = [
    {
        "id": "subtitles",
        "question": "Subtitles when watching foreign films?",
        "options": [
            {"value": "on", "label": "Always on, I like reading"},
            {"value": "off", "label": "Dubbed if possible"},
        ],
        "stage": 1,
    },
    {
        "id": "concert_position",
        "question": "Where do you stand at concerts?",
        "options": [
            {"value": "mosh_pit", "label": "In the mosh pit 🤘"},
            {"value": "front_row", "label": "Front row, center"},
            {"value": "balcony", "label": "Balcony with a drink"},
        ],
        "stage": 1,
    },
    {
        "id": "movie_length",
        "question": "How do you feel about long movies (3+ hours)?",
        "options": [
            {"value": "love", "label": "Love epics, the longer the better"},
            {"value": "depends", "label": "Depends on the movie"},
            {"value": "short", "label": "Keep it under 2 hours"},
        ],
        "stage": 2,
    },
    {
        "id": "music_discovery",
        "question": "How do you discover new music?",
        "options": [
            {"value": "algorithm", "label": "Spotify/algorithm recommendations"},
            {"value": "friends", "label": "Friends share with me"},
            {"value": "deep_dive", "label": "I dig through crates (physical or digital)"},
        ],
        "stage": 2,
    },
    {
        "id": "rewatchability",
        "question": "Re-watching movies you love?",
        "options": [
            {"value": "comfort", "label": "Love comfort rewatches"},
            {"value": "new_only", "label": "Always chasing something new"},
        ],
        "stage": 3,
    },
    {
        "id": "live_music",
        "question": "How important is live music to you?",
        "options": [
            {"value": "essential", "label": "Essential - I go to shows all the time"},
            {"value": "occasional", "label": "Occasional - for special artists"},
            {"value": "rare", "label": "Rarely - prefer recorded music"},
        ],
        "stage": 3,
    },
]


@router.get("/vibe-check/questions")
async def get_vibe_check_questions():
    """Get all vibe check questions for the onboarding quiz."""
    return {
        "questions": VIBE_CHECK_QUESTIONS,
        "total_stages": 3,
    }


@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get current user's full profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    updates: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update current user's profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/me/vibe-check")
async def submit_vibe_check(
    vibe_data: VibeCheckSubmit,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Submit vibe check quiz answers and regenerate vibe vector."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store answers as JSON
    answers_dict = {a.question_id: a.answer for a in vibe_data.answers}
    user.vibe_answers = answers_dict  # type: ignore[assignment]
    await db.commit()
    
    # Generate vibe_vector from answers using embedding model
    await update_user_vibe_vector(db, UUID(user_id))
    
    return {"message": "Vibe check submitted successfully", "answers": answers_dict}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Get another user's public profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/me/interactions", response_model=List[InteractionResponse])
async def get_my_interactions(
    interaction_type: str = Query(None, pattern="^(logged|top4|anthem|favorite)$"),
    media_type: str = Query(None, pattern="^(movie|artist|track|album)$"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get current user's interactions with optional filters."""
    query = select(UserInteraction).where(UserInteraction.user_id == user_id)
    query = query.options(selectinload(UserInteraction.media))
    
    if interaction_type:
        query = query.where(UserInteraction.interaction_type == interaction_type)
    
    if media_type:
        query = query.join(MediaItem).where(MediaItem.media_type == media_type)
    
    result = await db.execute(query)
    interactions = result.scalars().all()
    
    return interactions


@router.get("/{user_id}/top4", response_model=List[InteractionResponse])
async def get_user_top4(
    user_id: UUID,
    media_type: str = Query(None, pattern="^(movie|artist|track|album)$"),
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Get a user's Top 4 favorites."""
    query = (
        select(UserInteraction)
        .join(MediaItem)
        .where(
            UserInteraction.user_id == user_id,
            UserInteraction.interaction_type == "top4"
        )
    )
    query = query.options(selectinload(UserInteraction.media))
    
    if media_type:
        query = query.where(MediaItem.media_type == media_type)
    
    result = await db.execute(query)
    interactions = result.scalars().all()
    
    return interactions
