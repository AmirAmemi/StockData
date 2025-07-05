# main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import List

from config import Settings, get_settings
from routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("bavest-api")

def create_app(settings: Settings = get_settings()) -> FastAPI:
    """
    Create and configure the FastAPI application
    """
    app = FastAPI(
        title="Bavest Financial Data API",
        description="API for accessing and processing financial and alternative data",
        version="0.1.0",
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/", tags=["Health"])
    async def health_check():
        """Root endpoint for health checks"""
        return {"status": "healthy", "service": "Bavest Financial Data API"}

    return app

app = create_app()

if __name__ == "__main__":
    """
    Run the API server directly using uvicorn when script is executed
    """
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        log_level="info"
    )