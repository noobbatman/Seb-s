from typing import List, Optional
from sentence_transformers import SentenceTransformer
from functools import lru_cache
import numpy as np

from app.core.config import get_settings

settings = get_settings()


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load and cache the sentence transformer model."""
    return SentenceTransformer(settings.embedding_model)


class VectorService:
    """Service for generating and comparing vector embeddings."""
    
    def __init__(self):
        self._model: Optional[SentenceTransformer] = None
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._model is None:
            self._model = get_embedding_model()
        return self._model
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()  # type: ignore[union-attr]
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batched for efficiency)."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()  # type: ignore[union-attr]
    
    def generate_user_vibe_vector(
        self,
        vibe_answers: dict,
        genres: List[str],
        artists: List[str],
        movies: List[str],
    ) -> List[float]:
        """
        Generate a combined embedding vector for a user based on their preferences.
        
        This creates a rich representation of the user's cultural taste by combining:
        - Vibe check answers (preferences like "subtitles on/off")
        - Favorite genres (music and movie genres)
        - Top artists
        - Favorite movies
        """
        # Build a descriptive text representation of the user's taste
        components = []
        
        # Vibe answers as natural language
        if vibe_answers:
            vibe_text = self._vibe_answers_to_text(vibe_answers)
            if vibe_text:
                components.append(vibe_text)
        
        # Genres
        if genres:
            components.append(f"Favorite genres: {', '.join(genres)}")
        
        # Artists
        if artists:
            components.append(f"Favorite artists: {', '.join(artists[:10])}")  # Limit to prevent too long
        
        # Movies
        if movies:
            components.append(f"Favorite movies: {', '.join(movies[:10])}")
        
        # Combine all components
        if not components:
            # Return zero vector if no preferences
            return [0.0] * settings.embedding_dimension
        
        combined_text = " | ".join(components)
        return self.generate_embedding(combined_text)
    
    def _vibe_answers_to_text(self, answers: dict) -> str:
        """Convert vibe check answers to natural language for embedding."""
        # Map question IDs to descriptive text
        vibe_mappings = {
            "subtitles": {
                "on": "Prefers watching films with subtitles",
                "off": "Watches films without subtitles",
                "foreign": "Watches foreign films with subtitles",
            },
            "music_discovery": {
                "algorithm": "Discovers music through algorithms and playlists",
                "friends": "Discovers music through friends recommendations",
                "deep_dive": "Actively seeks out and discovers new music",
                "radio": "Discovers music through radio and playlists",
            },
            "movie_night": {
                "theater": "Loves watching movies in the cinema",
                "couch": "Enjoys cozy movie nights at home",
                "outdoor": "Loves outdoor screenings and experiences",
                "marathon": "Loves movie marathons",
            },
            "concert_vibe": {
                "front": "Enjoys being at the front of concerts",
                "middle": "Vibes in the middle section of concerts",
                "back": "Prefers chilling in the back at concerts",
                "vip": "Enjoys VIP concert experiences",
            },
            "genre_mood": {
                "upbeat": "Loves upbeat pop and dance music",
                "chill": "Enjoys lo-fi and chill music",
                "intense": "Loves rock and metal music",
                "nostalgic": "Enjoys throwback and classic music",
            },
            "rewatcher": {
                "always": "Loves rewatching comfort movies",
                "sometimes": "Rewatches really good movies",
                "never": "Always wants to watch something new",
            },
            "soundtrack": {
                "love": "Loves movie soundtracks",
                "some": "Enjoys iconic soundtracks",
                "skip": "Separates music from film experience",
            },
        }
        
        descriptions = []
        for question_id, answer in answers.items():
            if question_id in vibe_mappings:
                mapping = vibe_mappings[question_id]
                if answer in mapping:
                    descriptions.append(mapping[answer])
        
        return " ".join(descriptions)
    
    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def calculate_compatibility_score(
        self,
        user_a_vector: List[float],
        user_b_vector: List[float],
        shared_items_count: int = 0,
        rating_delta_avg: float = 0.0,
    ) -> float:
        """
        Calculate overall compatibility score between two users.
        
        Components:
        - Vibe similarity (cosine similarity of user vectors): 40%
        - Direct matches (shared items): 35%
        - Rating alignment (how similar their ratings are): 25%
        """
        # Vibe similarity (0 to 1)
        vibe_score = self.cosine_similarity(user_a_vector, user_b_vector)
        vibe_score = max(0, vibe_score)  # Ensure non-negative
        
        # Shared items score (logarithmic scale, caps at ~20 items)
        # More shared items = higher score, but diminishing returns
        shared_score = min(1.0, np.log1p(shared_items_count) / np.log1p(20))
        
        # Rating alignment score (lower delta = higher score)
        # Delta of 0 = 1.0, Delta of 2.5 = 0.0
        rating_score = max(0, 1 - (rating_delta_avg / 2.5))
        
        # Weighted combination
        final_score = (
            (vibe_score * 0.40) +
            (shared_score * 0.35) +
            (rating_score * 0.25)
        ) * 100  # Convert to percentage
        
        return round(final_score, 2)


# Singleton instance
vector_service = VectorService()
