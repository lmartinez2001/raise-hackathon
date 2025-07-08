"""
FastAPI application with modular router structure.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from settings import Settings
from routes import main, auth, drive

# Initialize settings
settings = Settings()

# Set up insecure transport for development
if settings.environment.lower() in ("dev", "development"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Initialize FastAPI application
app = FastAPI(
    title="Hackathon Backend API",
    description="A modular FastAPI application for Google Drive integration and authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS middleware
allowed_origins = [
    "http://localhost:3000",
    "https://localhost:3000",
]

# Add production domain if specified
if settings.frontend_url:
    allowed_origins.extend(
        [
            settings.frontend_url,
            settings.frontend_url.replace("http://", "https://"),
            settings.frontend_url.replace("https://", "http://"),
        ]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(main.router)
app.include_router(auth.router)
app.include_router(drive.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment.lower() in ("dev", "development"),
        log_level="info",
    )
