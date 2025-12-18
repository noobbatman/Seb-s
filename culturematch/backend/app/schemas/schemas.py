from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


# ============ Auth Schemas ============

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str
    exp: datetime


# ============ User Schemas ============

class UserBase(BaseModel):
    """Base user fields."""
    email: EmailStr
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """User response with additional fields."""
    id: UUID
    spotify_connected: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfile(UserResponse):
    """Full user profile with vibe answers."""
    vibe_answers: dict = {}


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


# ============ Vibe Check Schemas ============

class VibeAnswer(BaseModel):
    """Single vibe check answer."""
    question_id: str
    answer: str


class VibeCheckSubmit(BaseModel):
    """Submit vibe check answers."""
    answers: List[VibeAnswer]


# ============ Media Schemas ============

class MediaItemBase(BaseModel):
    """Base media item fields."""
    external_id: str = Field(..., min_length=1)
    media_type: str = Field(..., pattern="^(movie|artist|track|album)$")
    title: str = Field(..., min_length=1)
    image_url: Optional[str] = None
    extra_data: Optional[dict] = None
    
    class Config:
        str_strip_whitespace = True


class MediaItemCreate(MediaItemBase):
    """Create a media item."""
    pass


class MediaItemResponse(MediaItemBase):
    """Media item response."""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Interaction Schemas ============

class InteractionCreate(BaseModel):
    """Create a user interaction."""
    media: MediaItemCreate
    interaction_type: str = Field(..., pattern="^(logged|top4|anthem|favorite)$")
    rating: Optional[float] = Field(None, ge=0.5, le=5)
    review_text: Optional[str] = None


class InteractionResponse(BaseModel):
    """User interaction response."""
    id: UUID
    media: MediaItemResponse
    interaction_type: str
    rating: Optional[float]
    review_text: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Match Schemas ============

class MatchResponse(BaseModel):
    """Match response."""
    id: UUID
    matched_user: UserResponse
    compatibility_score: float
    shared_items: List[MediaItemResponse] = []
    icebreaker_prompt: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class MovieSearchResult(BaseModel):
    """Movie search result from TMDB."""
    id: str
    title: str
    image_url: Optional[str] = None
    release_date: Optional[str] = None
    overview: Optional[str] = None
    vote_average: Optional[float] = None


class ArtistSearchResult(BaseModel):
    """Artist search result from Spotify."""
    id: str
    name: str
    image_url: Optional[str] = None
    genres: Optional[List[str]] = None
    popularity: Optional[int] = None


class TrackSearchResult(BaseModel):
    """Track search result from Spotify."""
    id: str
    name: str
    artist: Optional[str] = None
    album: Optional[str] = None
    image_url: Optional[str] = None
    preview_url: Optional[str] = None


class MatchAction(BaseModel):
    """Accept or reject a match."""
    action: str = Field(..., pattern="^(accept|reject)$")


# ============ Message Schemas ============

class MessageCreate(BaseModel):
    """Create a message."""
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    """Message response."""
    id: UUID
    sender_id: UUID
    content: str
    is_system_message: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Search Schemas ============

class MovieSearchResult(BaseModel):
    """TMDB movie search result."""
    id: int
    title: str
    overview: Optional[str] = None
    poster_path: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    genres: List[str] = []


class ArtistSearchResult(BaseModel):
    """Spotify artist search result."""
    id: str
    name: str
    image_url: Optional[str] = None
    genres: List[str] = []
    popularity: Optional[int] = None


class TrackSearchResult(BaseModel):
    """Spotify track search result."""
    id: str
    name: str
    artist: str
    album: str
    image_url: Optional[str] = None
    preview_url: Optional[str] = None
