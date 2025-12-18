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
        self._use_mock_mode: bool = False
        
        if not self.client_id or not self.client_secret:
            print(f"❌ Spotify credentials missing! Using mock mode.")
            self._use_mock_mode = True
        else:
            print(f"🎵 Spotify service initialized (ID: {self.client_id[:8]}..., Secret: {self.client_secret[:8]}...)")
    
    async def _get_client_credentials_token(self) -> str:
        """Get access token using Client Credentials Flow (for app-level requests)."""
        if self._access_token:
            return self._access_token
        
        if self._use_mock_mode:
            print("⚠️  Using mock Spotify token (credentials invalid)")
            self._access_token = "mock_token_for_development"
            return self._access_token
        
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
        
        print(f"🔐 Spotify auth attempt:")
        print(f"   Client ID length: {len(self.client_id)}")
        print(f"   Client Secret length: {len(self.client_secret)}")
        print(f"   Auth header (first 20 chars): {auth_base64[:20]}...")
        
        response = None
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.AUTH_URL,
                    headers={
                        "Authorization": f"Basic {auth_base64}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data={"grant_type": "client_credentials"},
                )
                print(f"✅ Spotify response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                self._access_token = data["access_token"]
                return data["access_token"]
            except Exception as e:
                print(f"❌ Spotify auth error: {e}")
                if response:
                    print(f"   Status: {response.status_code}")
                    print(f"   Body: {response.text[:200]}")
                print("⚠️  Falling back to mock mode")
                self._use_mock_mode = True
                self._access_token = "mock_token_fallback"
                return self._access_token
    
    async def search_artists(self, query: str, limit: int = 10) -> List[dict]:
        """Search for artists by name."""
        if self._use_mock_mode:
            return self._mock_search_artists(query, limit)
        
        token = await self._get_client_credentials_token()
        
        # If still in mock mode after getting token, use mock
        if self._use_mock_mode:
            return self._mock_search_artists(query, limit)
        
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
                # Use image only if available and not empty - prefer larger images
                image_url = None
                if artist.get("images"):
                    # Get the largest image (they're sorted by size)
                    for img in artist["images"]:
                        if img.get("url") and len(img.get("url", "")) > 0:
                            image_url = img.get("url")
                            break
                
                artists.append({
                    "id": artist["id"],
                    "name": artist["name"],
                    "image_url": image_url,
                    "genres": artist.get("genres", []),
                    "popularity": artist.get("popularity"),
                })
            
            return artists
    
    def _mock_search_artists(self, query: str, limit: int = 10) -> List[dict]:
        """Mock artist search for development."""
        mock_artists = {
            "weeknd": [
                {"id": "1Xyo4u8uIOU6aqB0H0Jqo3", "name": "The Weeknd", "image_url": None, "genres": ["hip hop", "r&b", "pop"], "popularity": 94},
                {"id": "5p1vPsD9hzBzHu8VbVbHjx", "name": "The Weeknd ft. Daft Punk", "image_url": None, "genres": ["electronic", "hip hop"], "popularity": 75},
            ],
            "drake": [
                {"id": "39NQY1jJ60uYao5LSUK3My", "name": "Drake", "image_url": None, "genres": ["hip hop", "rap", "pop"], "popularity": 92},
            ],
            "ariana": [
                {"id": "66CXWjxzNUsdJxJ2JdwvnR", "name": "Ariana Grande", "image_url": None, "genres": ["pop", "r&b"], "popularity": 90},
            ],
            "bad bunny": [
                {"id": "4q3ewBCX7eYZXvRNVzvm0v", "name": "Bad Bunny", "image_url": None, "genres": ["trap latino", "reggaeton"], "popularity": 95},
            ],
            "taylor": [
                {"id": "06HL4z0CvFAxyc27GXpf02", "name": "Taylor Swift", "image_url": None, "genres": ["pop", "country pop"], "popularity": 96},
            ],
        }
        
        query_lower = query.lower()
        for key in mock_artists:
            if key in query_lower:
                return mock_artists[key][:limit]
        
        # Default mock result
        return [{
            "id": "mock_" + query[:8],
            "name": f"{query}",
            "image_url": None,
            "genres": ["unknown"],
            "popularity": 50,
        }]
    
    async def search_tracks(self, query: str, limit: int = 10) -> List[dict]:
        """Search for tracks by name."""
        if self._use_mock_mode:
            return self._mock_search_tracks(query, limit)
        
        token = await self._get_client_credentials_token()
        
        # If still in mock mode after getting token, use mock
        if self._use_mock_mode:
            return self._mock_search_tracks(query, limit)
        
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
                # Use album image only if available and not empty
                image_url = None
                album_images = track.get("album", {}).get("images", [])
                if album_images:
                    for img in album_images:
                        if img.get("url") and len(img.get("url", "")) > 0:
                            image_url = img.get("url")
                            break
                
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
    
    def _mock_search_tracks(self, query: str, limit: int = 10) -> List[dict]:
        """Mock track search for development."""
        mock_tracks = {
            "blinding": [
                {"id": "0VjIjW4GlUZAMYd2vXMwbN", "name": "Blinding Lights", "artist": "The Weeknd", "album": "After Hours", "image_url": None, "preview_url": None},
            ],
            "levitating": [
                {"id": "0dHEbKZeRqBvjXZ4aWi9iO", "name": "Levitating", "artist": "Dua Lipa", "album": "Future Nostalgia", "image_url": None, "preview_url": None},
            ],
            "shape of you": [
                {"id": "7qiZfU4dY1lsylvNEJlljt", "name": "Shape of You", "artist": "Ed Sheeran", "album": "÷", "image_url": None, "preview_url": None},
            ],
            "bad guy": [
                {"id": "2takcwFFpFHSY8zcFmPbGp", "name": "bad guy", "artist": "Billie Eilish", "album": "When We All Fall Asleep Where Do We Go", "image_url": None, "preview_url": None},
            ],
        }
        
        query_lower = query.lower()
        for key in mock_tracks:
            if key in query_lower:
                return mock_tracks[key][:limit]
        
        # Default mock result
        return [{
            "id": "mock_track_" + query[:8],
            "name": f"{query}",
            "artist": "Unknown Artist",
            "album": "Unknown Album",
            "image_url": None,
            "preview_url": None,
        }]
    
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
