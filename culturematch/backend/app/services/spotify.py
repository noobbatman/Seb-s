import httpx
import base64
from typing import Optional, List
from app.core.config import get_settings

settings = get_settings()


class SpotifyService:
    """Service for interacting with Spotify Web API."""
    
    AUTH_URL = "https://accounts.spotify.com/api/token"
    API_BASE_URL = "https://api.spotify.com/v1"
    
    def __init__(self):
        self.client_id = settings.spotify_client_id
        self.client_secret = settings.spotify_client_secret
        self._access_token: Optional[str] = None
    
    async def _get_client_credentials_token(self) -> str:
        """Get access token using Client Credentials Flow (for app-level requests)."""
        if self._access_token:
            return self._access_token
        
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.AUTH_URL,
                headers={
                    "Authorization": f"Basic {auth_base64}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            return data["access_token"]
    
    async def search_artists(self, query: str, limit: int = 10) -> List[dict]:
        """Search for artists by name."""
        token = await self._get_client_credentials_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE_URL}/search",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": query, "type": "artist", "limit": limit},
            )
            response.raise_for_status()
            data = response.json()
            
            artists = []
            for artist in data.get("artists", {}).get("items", []):
                image_url = artist["images"][0]["url"] if artist.get("images") else None
                artists.append({
                    "id": artist["id"],
                    "name": artist["name"],
                    "image_url": image_url,
                    "genres": artist.get("genres", []),
                    "popularity": artist.get("popularity"),
                })
            
            return artists
    
    async def search_tracks(self, query: str, limit: int = 10) -> List[dict]:
        """Search for tracks by name."""
        token = await self._get_client_credentials_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE_URL}/search",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": query, "type": "track", "limit": limit},
            )
            response.raise_for_status()
            data = response.json()
            
            tracks = []
            for track in data.get("tracks", {}).get("items", []):
                album_images = track.get("album", {}).get("images", [])
                image_url = album_images[0]["url"] if album_images else None
                artists = ", ".join([a["name"] for a in track.get("artists", [])])
                
                tracks.append({
                    "id": track["id"],
                    "name": track["name"],
                    "artist": artists,
                    "album": track.get("album", {}).get("name"),
                    "image_url": image_url,
                    "preview_url": track.get("preview_url"),
                })
            
            return tracks
    
    async def get_artist(self, artist_id: str) -> Optional[dict]:
        """Get artist details by ID."""
        token = await self._get_client_credentials_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE_URL}/artists/{artist_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            artist = response.json()
            
            image_url = artist["images"][0]["url"] if artist.get("images") else None
            return {
                "id": artist["id"],
                "name": artist["name"],
                "image_url": image_url,
                "genres": artist.get("genres", []),
                "popularity": artist.get("popularity"),
                "followers": artist.get("followers", {}).get("total"),
            }
    
    async def get_user_top_items(self, access_token: str, item_type: str = "artists", limit: int = 20) -> List[dict]:
        """Get user's top artists or tracks (requires user OAuth)."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE_URL}/me/top/{item_type}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"limit": limit, "time_range": "medium_term"},
            )
            response.raise_for_status()
            data = response.json()
            
            items = []
            for item in data.get("items", []):
                if item_type == "artists":
                    image_url = item["images"][0]["url"] if item.get("images") else None
                    items.append({
                        "id": item["id"],
                        "name": item["name"],
                        "image_url": image_url,
                        "genres": item.get("genres", []),
                    })
                else:  # tracks
                    album_images = item.get("album", {}).get("images", [])
                    image_url = album_images[0]["url"] if album_images else None
                    items.append({
                        "id": item["id"],
                        "name": item["name"],
                        "artist": ", ".join([a["name"] for a in item.get("artists", [])]),
                        "image_url": image_url,
                    })
            
            return items


# Singleton instance
spotify_service = SpotifyService()
