# CultureMatch 🎬🎵

> "Letterboxd meets Spotify meets Hinge"

A cross-platform dating application that matches users based on **Cultural Compatibility** - their movies and music taste rather than just physical appearance.

## Philosophy

- **Anti-Swipe**: Matches are suggested based on shared media interests
- **Content-First**: Profiles highlight "Top 4 Favorites," reviews, and listening habits
- **Platform Agnostic**: Fully responsive PWA for both mobile and desktop

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14+, TypeScript, Tailwind CSS, Shadcn/UI |
| Backend | FastAPI, Pydantic, Python 3.11+ |
| Database | PostgreSQL 16 + pgvector |
| APIs | TMDB (Movies), Spotify Web API (Music) |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### 1. Clone & Configure

```bash
cd culturematch
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start with Docker

```bash
docker-compose up -d
```

This will spin up:
- **PostgreSQL** with pgvector at `localhost:5432`
- **FastAPI Backend** at `http://localhost:8000`
- **Next.js Frontend** at `http://localhost:3000`

### 3. Access the App

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- API ReDoc: http://localhost:8000/redoc

## Project Structure

```
culturematch/
├── frontend/          # Next.js 14+ App Router
│   ├── app/           # App Router pages
│   ├── components/    # React components
│   ├── lib/           # Utilities & API client
│   └── styles/        # Global styles
├── backend/           # FastAPI Python
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── core/      # Config, security
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   └── services/  # Business logic
│   └── scripts/       # DB init scripts
└── docker-compose.yml
```

## API Keys Setup

### Spotify
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create an app and get Client ID & Secret
3. Add redirect URI: `http://localhost:8000/api/auth/spotify/callback`

### TMDB
1. Go to [TMDB Settings](https://www.themoviedb.org/settings/api)
2. Request an API key
3. Copy the API Read Access Token (v4 auth)

## License

MIT
