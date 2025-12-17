-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(500),
    spotify_connected BOOLEAN DEFAULT FALSE,
    spotify_access_token TEXT,
    spotify_refresh_token TEXT,
    vibe_vector vector(384),  -- Embedding for matching
    vibe_answers JSONB DEFAULT '{}',  -- Raw quiz answers
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Media items (Movies & Music)
CREATE TABLE IF NOT EXISTS media_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(100) NOT NULL,  -- TMDB ID or Spotify ID
    media_type VARCHAR(20) NOT NULL CHECK (media_type IN ('movie', 'artist', 'track', 'album')),
    title VARCHAR(500) NOT NULL,
    image_url VARCHAR(500),
    metadata JSONB DEFAULT '{}',  -- Genres, release year, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(external_id, media_type)
);

-- User interactions with media
CREATE TABLE IF NOT EXISTS user_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    media_id UUID REFERENCES media_items(id) ON DELETE CASCADE,
    interaction_type VARCHAR(20) NOT NULL CHECK (interaction_type IN ('logged', 'top4', 'anthem', 'favorite')),
    rating DECIMAL(2,1) CHECK (rating >= 0.5 AND rating <= 5),
    review_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, media_id, interaction_type)
);

-- Matches between users
CREATE TABLE IF NOT EXISTS matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_a_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user_b_id UUID REFERENCES users(id) ON DELETE CASCADE,
    compatibility_score DECIMAL(5,2) NOT NULL,
    shared_items JSONB DEFAULT '[]',  -- Array of shared media item IDs
    icebreaker_prompt TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'matched')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_a_id, user_b_id)
);

-- Chat messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_system_message BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_interactions_user ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_media ON user_interactions(media_id);
CREATE INDEX IF NOT EXISTS idx_matches_users ON matches(user_a_id, user_b_id);
CREATE INDEX IF NOT EXISTS idx_messages_match ON messages(match_id);
CREATE INDEX IF NOT EXISTS idx_media_external ON media_items(external_id, media_type);

-- Vector similarity index for matching
CREATE INDEX IF NOT EXISTS idx_users_vibe_vector ON users USING ivfflat (vibe_vector vector_cosine_ops) WITH (lists = 100);
