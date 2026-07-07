"""AI Startup Boardroom — FastAPI application entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routes.meetings import router as meetings_router
from routes.documents import router as documents_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="AI Startup Boardroom",
    description=(
        "An Executive AI Board that collaborates like a real company's "
        "leadership team to evaluate startup ideas."
    ),
    version="1.0.0",
)

# CORS — allow the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(meetings_router)
app.include_router(documents_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "AI Startup Boardroom",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/api/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "gemini_configured": bool(settings.GOOGLE_API_KEY),
        "pro_model": settings.PRO_MODEL,
        "flash_model": settings.FLASH_MODEL,
    }
