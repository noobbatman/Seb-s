from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core import get_settings
from app.api import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: Pre-load the embedding model
    if not settings.debug:
        from app.services.vector import get_embedding_model
        print("🧠 Pre-loading embedding model...")
        get_embedding_model()
        print("✅ Embedding model loaded!")
    yield
    # Shutdown: cleanup if needed
    print("👋 Shutting down CultureMatch API...")


app = FastAPI(
    title="CultureMatch API",
    description="Dating app that matches users based on cultural compatibility - movies & music taste",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration - MUST be before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "http://127.0.0.1:3000",
        "localhost:3000",
        "127.0.0.1:3000",
        "*",  # Allow all origins in dev (since we're local)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "app": "CultureMatch API",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """Health check for container orchestration."""
    return {"status": "healthy"}
