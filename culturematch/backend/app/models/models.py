from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any
from uuid import UUID as PyUUID
import uuid

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Numeric, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class User(Base):
    """User model for authentication and profile."""
    
    __tablename__ = "users"
    
    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Spotify OAuth
    spotify_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    spotify_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    spotify_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Matching vectors
    vibe_vector: Mapped[Optional[List[float]]] = mapped_column(Vector(384), nullable=True)
    vibe_answers: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    interactions: Mapped[List["UserInteraction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"


class MediaItem(Base):
    """Media items (Movies, Artists, Tracks, Albums)."""
    
    __tablename__ = "media_items"
    
    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    interactions: Mapped[List["UserInteraction"]] = relationship(back_populates="media")
    
    __table_args__ = (
        UniqueConstraint("external_id", "media_type", name="uq_media_external"),
        CheckConstraint(
            "media_type IN ('movie', 'artist', 'track', 'album')",
            name="ck_media_type"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<MediaItem {self.media_type}: {self.title}>"


class UserInteraction(Base):
    """User interactions with media items."""
    
    __tablename__ = "user_interactions"
    
    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    media_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)
    
    interaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(2, 1), nullable=True)
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="interactions")
    media: Mapped["MediaItem"] = relationship(back_populates="interactions")
    
    __table_args__ = (
        UniqueConstraint("user_id", "media_id", "interaction_type", name="uq_user_media_interaction"),
        CheckConstraint("rating >= 0.5 AND rating <= 5", name="ck_rating_range"),
        CheckConstraint(
            "interaction_type IN ('logged', 'top4', 'anthem', 'favorite')",
            name="ck_interaction_type"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<UserInteraction {self.interaction_type}>"


class Match(Base):
    """Matches between users."""
    
    __tablename__ = "matches"
    
    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_a_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_b_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    compatibility_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    shared_items: Mapped[Optional[List[Any]]] = mapped_column(JSONB, default=list, nullable=True)
    icebreaker_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_a: Mapped["User"] = relationship(foreign_keys=[user_a_id])
    user_b: Mapped["User"] = relationship(foreign_keys=[user_b_id])
    messages: Mapped[List["Message"]] = relationship(back_populates="match", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("user_a_id", "user_b_id", name="uq_match_users"),
        CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'matched')",
            name="ck_match_status"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Match {self.compatibility_score}%>"


class Message(Base):
    """Chat messages between matched users."""
    
    __tablename__ = "messages"
    
    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_system_message: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    match: Mapped["Match"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship()
    
    def __repr__(self) -> str:
        return f"<Message from {self.sender_id}>"
