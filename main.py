"""
Rhône Risk Policy Analysis API
FastAPI microservice for automated cyber insurance policy analysis
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import webhook, analysis
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Starting Rhône Risk Policy Analysis API")
    logger.info(f"📋 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔑 Anthropic API configured: {'Yes' if settings.ANTHROPIC_API_KEY else 'No'}")

    # Create required directories
    os.makedirs("temp", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    yield

    logger.info("👋 Shutting down Policy Analysis API")


app = FastAPI(
    title="Rhône Risk Policy Analysis API",
    description="""
    Automated cyber insurance policy analysis microservice.

    ## Features
    - Webhook integration for policy upload notifications
    - PDF text extraction and parsing
    - Claude-powered policy analysis using Rhône Risk's proprietary scoring methodology
    - Branded PDF report generation
    - Async callback delivery

    ## Integration
    This service is designed to integrate with your existing SaaS platform via webhooks.
    See the /docs endpoint for full API documentation.
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(webhook.router, prefix="/webhook", tags=["Webhooks"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API info"""
    return {
        "service": "Rhône Risk Policy Analysis API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
