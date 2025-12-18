// User types
export interface User {
  id: string;
  email: string;
  display_name: string | null;
  bio: string | null;
  avatar_url: string | null;
  spotify_connected: boolean;
  created_at: string;
}

export interface UserProfile extends User {
  top_movies: MediaItem[];
  top_artists: MediaItem[];
  anthem: MediaItem | null;
  vibe_answers: Record<string, string> | null;
}

// Auth types
export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  display_name?: string;
}

// Media types
export interface MediaItem {
  id: string;
  external_id: string;
  media_type: 'movie' | 'artist' | 'track' | 'album';
  title: string;
  image_url: string | null;
  extra_data: Record<string, unknown> | null;
}

export interface MediaSearchResult {
  id: string;
  title?: string;
  name?: string;
  image_url: string | null;
  year?: number;
  artist?: string;
  album?: string;
  genres?: string[];
  release_date?: string;
  overview?: string;
  popularity?: number;
  preview_url?: string;
}

export interface UserInteraction {
  id: string;
  media: MediaItem;
  interaction_type: 'logged' | 'top4' | 'anthem' | 'favorite';
  rating: number | null;
  review_text: string | null;
  created_at: string;
}

// Match types
export interface Match {
  id: string;
  matched_user: User;
  compatibility_score: number;
  shared_items: SharedItem[];
  icebreaker_prompt: string | null;
  status: 'pending' | 'accepted' | 'rejected' | 'matched';
  created_at: string;
}

export interface SharedItem {
  media: MediaItem;
  user_a_rating: number | null;
  user_b_rating: number | null;
}

export interface PotentialMatch {
  user: User;
  compatibility_score: number;
  shared_items: SharedItem[];
  icebreaker_prompt: string;
}

// Chat types
export interface Message {
  id: string;
  match_id: string;
  sender_id: string;
  content: string;
  is_system_message: boolean;
  created_at: string;
}

// Vibe check types
export interface VibeQuestion {
  id: string;
  question: string;
  options: VibeOption[];
}

export interface VibeOption {
  value: string;
  label: string;
  emoji?: string;
}

export interface VibeAnswer {
  question_id: string;
  answer: string;
}

// API response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface ApiError {
  detail: string;
}
