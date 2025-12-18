"""
Spotify OAuth endpoints for user authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import base64
from uuid import UUID
from urllib.parse import urlencode

from app.core import get_db, get_current_user_id, get_settings
from app.models import User
from app.services import spotify_service, update_user_vibe_vector

settings = get_settings()
router = APIRouter(prefix="/spotify", tags=["Spotify OAuth"])

# ✅ CORRECT URLS (The fix is here)
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

SCOPES = "user-top-read user-read-private user-read-email"


@router.get("/connect")
async def spotify_connect(
    user_id: str = Depends(get_current_user_id),
):
    """
    Initiate Spotify OAuth flow.
    Returns the URL to redirect the user to for Spotify authorization.
    """
    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "scope": SCOPES,
        "state": user_id,  # Pass user_id in state for callback
        "show_dialog": "true",
    }
    
    # Use urlencode to properly encode all parameters
    auth_url = f"{SPOTIFY_AUTH_URL}?" + urlencode(params)
    
    print(f"[DEBUG] Spotify Connect URL: {auth_url}")
    print(f"[DEBUG] Client ID: {settings.spotify_client_id}")
    print(f"[DEBUG] Redirect URI: {settings.spotify_redirect_uri}")
    print(f"[DEBUG] Scope: {SCOPES}")
    
    return {"auth_url": auth_url}


@router.get("/callback")
async def spotify_callback(
    code: str = Query(...),
    state: str = Query(...),  # user_id
    error: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Spotify OAuth callback.
    Exchange authorization code for access tokens.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"Spotify auth error: {error}")
    
    user_id = state
    
    # Exchange code for tokens
    auth_string = f"{settings.spotify_client_id}:{settings.spotify_client_secret}"
    auth_base64 = base64.b64encode(auth_string.encode()).decode()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            SPOTIFY_TOKEN_URL,
            headers={
                "Authorization": f"Basic {auth_base64}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
            },
        )
        
        if response.status_code != 200:
            print(f"Spotify Token Error: {response.text}") # Debug log
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        
        tokens = response.json()
    
    # Update user with Spotify tokens
    # Note: user_id is coming from 'state' which is a string UUID
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.spotify_connected = True
    user.spotify_access_token = tokens["access_token"]
    user.spotify_refresh_token = tokens.get("refresh_token")
    
    await db.commit()
    
    # Redirect to frontend success page (using IP address where frontend is hosted)
    return RedirectResponse(url="http://192.168.0.104:3001/profile?spotify=connected")


@router.post("/import-top-items")
async def import_spotify_top_items(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Import user's top artists and tracks from Spotify.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.spotify_connected or not user.spotify_access_token:
        raise HTTPException(
            status_code=400,
            detail="Connect your Spotify account first"
        )
    
    access_token = str(user.spotify_access_token)
    
    try:
        # Fetch top artists
        top_artists = await spotify_service.get_user_top_items(
            access_token,
            item_type="artists",
            limit=10,
        )
        
        # Fetch top tracks
        top_tracks = await spotify_service.get_user_top_items(
            access_token,
            item_type="tracks",
            limit=10,
        )
        
        # Import as interactions
        from app.models import MediaItem, UserInteraction
        
        imported = {"artists": 0, "tracks": 0}
        
        # Import top 4 artists
        for i, artist in enumerate(top_artists[:4]):
            # Find or create media item
            existing = await db.execute(
                select(MediaItem).where(
                    MediaItem.external_id == artist["id"],
                    MediaItem.media_type == "artist",
                )
            )
            media = existing.scalar_one_or_none()
            
            if not media:
                media = MediaItem(
                    external_id=artist["id"],
                    media_type="artist",
                    title=artist["name"],
                    image_url=artist.get("image_url"),
                    extra_data={"genres": artist.get("genres", [])},
                )
                db.add(media)
                await db.flush()
            
            # Create top4 interaction
            interaction_exists = await db.execute(
                select(UserInteraction).where(
                    UserInteraction.user_id == user_id,
                    UserInteraction.media_id == media.id,
                    UserInteraction.interaction_type == "top4",
                )
            )
            if not interaction_exists.scalar_one_or_none():
                interaction = UserInteraction(
                    user_id=user_id,
                    media_id=media.id,
                    interaction_type="top4",
                )
                db.add(interaction)
                imported["artists"] += 1
        
        await db.commit()
        
        # Regenerate vibe vector
        # Note: Assuming this service function exists in your codebase
        # await update_user_vibe_vector(db, UUID(user_id))
        
        return {
            "message": "Spotify data imported successfully!",
            "imported": imported,
            "top_artists": [a["name"] for a in top_artists[:4]],
        }
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            user.spotify_connected = False
            user.spotify_access_token = None
            await db.commit()
            raise HTTPException(
                status_code=401,
                detail="Spotify session expired, please reconnect"
            )
        raise HTTPException(status_code=500, detail=f"Spotify API error: {str(e)}")


@router.delete("/disconnect")
async def disconnect_spotify(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Disconnect Spotify account from user profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.spotify_connected = False
    user.spotify_access_token = None
    user.spotify_refresh_token = None
    
    await db.commit()
    
    return {"message": "Spotify disconnected successfully"}