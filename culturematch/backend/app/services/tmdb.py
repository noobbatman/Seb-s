import httpx
from typing import Optional, List
from app.core.config import get_settings

settings = get_settings()


class TMDBService:
    """Service for interacting with The Movie Database API."""
    
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
    
    def __init__(self):
        self.api_key = settings.tmdb_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    async def search_movies(self, query: str, page: int = 1) -> List[dict]:
        """Search for movies by title."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search/movie",
                headers=self.headers,
                params={"query": query, "page": page},
            )
            response.raise_for_status()
            data = response.json()
            
            movies = []
            for movie in data.get("results", []):
                movies.append({
                    "id": movie["id"],
                    "title": movie["title"],
                    "overview": movie.get("overview"),
                    "poster_path": f"{self.IMAGE_BASE_URL}{movie['poster_path']}" if movie.get("poster_path") else None,
                    "release_date": movie.get("release_date"),
                    "vote_average": movie.get("vote_average"),
                })
            
            return movies
    
    async def get_movie_details(self, movie_id: int) -> Optional[dict]:
        """Get detailed information about a movie."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/movie/{movie_id}",
                headers=self.headers,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            movie = response.json()
            
            return {
                "id": movie["id"],
                "title": movie["title"],
                "overview": movie.get("overview"),
                "poster_path": f"{self.IMAGE_BASE_URL}{movie['poster_path']}" if movie.get("poster_path") else None,
                "release_date": movie.get("release_date"),
                "vote_average": movie.get("vote_average"),
                "genres": [g["name"] for g in movie.get("genres", [])],
                "runtime": movie.get("runtime"),
                "tagline": movie.get("tagline"),
            }
    
    async def get_trending_movies(self, time_window: str = "week") -> List[dict]:
        """Get trending movies."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/trending/movie/{time_window}",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            
            movies = []
            for movie in data.get("results", [])[:10]:
                movies.append({
                    "id": movie["id"],
                    "title": movie["title"],
                    "poster_path": f"{self.IMAGE_BASE_URL}{movie['poster_path']}" if movie.get("poster_path") else None,
                    "vote_average": movie.get("vote_average"),
                })
            
            return movies


# Singleton instance
tmdb_service = TMDBService()
