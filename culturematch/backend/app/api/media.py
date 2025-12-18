from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List
from uuid import UUID

from app.core import get_db, get_current_user_id
from app.models import MediaItem, UserInteraction
from app.schemas import (
    MediaItemCreate,
    MediaItemResponse,
    InteractionCreate,
    InteractionResponse,
    MovieSearchResult,
    ArtistSearchResult,
    TrackSearchResult,
)
from app.services import tmdb_service, spotify_service, update_user_vibe_vector

router = APIRouter(prefix="/media", tags=["Media"])


# ============ Search Endpoints ============

@router.get("/search/movies", response_model=List[MovieSearchResult])
async def search_movies(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    _: str = Depends(get_current_user_id),  # Require auth
):
    """Search for movies via TMDB API."""
    try:
        results = await tmdb_service.search_movies(q, page)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TMDB API error: {str(e)}")


@router.get("/search/artists", response_model=List[ArtistSearchResult])
async def search_artists(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    _: str = Depends(get_current_user_id),
):
    """Search for artists via Spotify API."""
    try:
        results = await spotify_service.search_artists(q, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify API error: {str(e)}")


@router.get("/search/tracks", response_model=List[TrackSearchResult])
async def search_tracks(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    _: str = Depends(get_current_user_id),
):
    """Search for tracks via Spotify API."""
    try:
        results = await spotify_service.search_tracks(q, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify API error: {str(e)}")


@router.get("/trending/movies")
async def get_trending_movies(
    time_window: str = Query("week", pattern="^(day|week)$"),
    _: str = Depends(get_current_user_id),
):
    """Get trending movies from TMDB."""
    try:
        results = await tmdb_service.get_trending_movies(time_window)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TMDB API error: {str(e)}")


# ============ Interaction Endpoints ============

@router.post("/interactions", response_model=InteractionResponse, status_code=201)
async def create_interaction(
    data: InteractionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Log a media interaction (rating, review, add to Top 4, etc.)."""
    
    # Find or create media item
    result = await db.execute(
        select(MediaItem).where(
            MediaItem.external_id == data.media.external_id,
            MediaItem.media_type == data.media.media_type,
        )
    )
    media = result.scalar_one_or_none()
    
    if not media:
        media = MediaItem(
            external_id=data.media.external_id,
            media_type=data.media.media_type,
            title=data.media.title,
            image_url=data.media.image_url,
            extra_data=data.media.extra_data or {},
        )
        db.add(media)
        await db.flush()  # Get the ID
    
    # Check for existing interaction of same type
    result = await db.execute(
        select(UserInteraction).where(
            UserInteraction.user_id == user_id,
            UserInteraction.media_id == media.id,
            UserInteraction.interaction_type == data.interaction_type,
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing
        if data.rating is not None:
            existing.rating = data.rating  # type: ignore[assignment]
        existing.review_text = data.review_text  # type: ignore[assignment]
        interaction = existing
    else:
        # Validate Top 4 limit
        if data.interaction_type == "top4":
            count_result = await db.execute(
                select(UserInteraction)
                .join(MediaItem)
                .where(
                    UserInteraction.user_id == user_id,
                    UserInteraction.interaction_type == "top4",
                    MediaItem.media_type == data.media.media_type,
                )
            )
            current_top4 = count_result.scalars().all()
            if len(current_top4) >= 4:
                raise HTTPException(
                    status_code=400,
                    detail=f"You already have 4 items in your Top 4 for {data.media.media_type}s"
                )
        
        interaction = UserInteraction(
            user_id=user_id,
            media_id=media.id,
            interaction_type=data.interaction_type,
            rating=data.rating,
            review_text=data.review_text,
        )
        db.add(interaction)
    
    await db.commit()
    await db.refresh(interaction)
    
    # Regenerate vibe vector for significant interactions (Top 4, anthem)
    if data.interaction_type in ("top4", "anthem"):
        await update_user_vibe_vector(db, UUID(user_id))
    
    # Eager load media for response
    await db.refresh(interaction, ["media"])
    
    return interaction


@router.get("/my-interactions", response_model=List[InteractionResponse])
async def get_my_interactions(
    interaction_type: str = Query(None, pattern="^(logged|top4|anthem|favorite)$"),
    media_type: str = Query(None, pattern="^(movie|artist|track|album)$"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get current user's media interactions."""
    query = (
        select(UserInteraction)
        .join(MediaItem)
        .where(UserInteraction.user_id == user_id)
    )
    
    if interaction_type:
        query = query.where(UserInteraction.interaction_type == interaction_type)
    if media_type:
        query = query.where(MediaItem.media_type == media_type)
    
    query = query.order_by(UserInteraction.created_at.desc())
    
    result = await db.execute(query)
    interactions = result.scalars().all()
    
    return interactions


@router.delete("/interactions/{interaction_id}", status_code=204)
async def delete_interaction(
    interaction_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Remove a media interaction."""
    result = await db.execute(
        select(UserInteraction).where(
            UserInteraction.id == interaction_id,
            UserInteraction.user_id == user_id,
        )
    )
    interaction = result.scalar_one_or_none()
    
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    
    await db.delete(interaction)
    await db.commit()
    
    return None
