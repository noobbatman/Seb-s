from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )
    
    # App
    app_name: str = "CultureMatch API"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql://culturematch:culturematch_secret@localhost:5432/culturematch"
    
    # JWT Auth
    jwt_secret: str = "your-super-secret-jwt-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # Spotify API
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://192.168.0.104:8000/api/spotify/callback"
    
    # TMDB API
    tmdb_api_key: str = ""
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    
    # Vector Embedding Model
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
