from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.media import router as media_router
from app.api.matches import router as matches_router
from app.api.spotify import router as spotify_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(media_router)
api_router.include_router(matches_router)
api_router.include_router(spotify_router)
