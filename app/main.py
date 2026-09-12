"""
FastAPI Application Entry Point for AadhaarVoice.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.db.session import init_db
from app.api.auth import router as auth_router
from app.api.identity import router as identity_router
from app.api.voice import router as voice_router
from app.api.audit import router as audit_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="""
# 🇮🇳 AadhaarVoice: AI-Powered Biometric Voice Authentication & Deepfake Defense System

An AI-based research and hackathon prototype exploring:
- **Voice Biometrics**: 192-dimensional acoustic speaker embeddings and cosine verification.
- **Deepfake & Anti-Spoofing**: Forensic neural vocoder detection, micro-jitter analysis, spectral flatness.
- **Synthetic Voice Cloning**: Resonant formant acoustic synthesis matching target pitch and vocal characteristics.
- **Digital Identity Security**: Verhoeff checksum algorithm for 12-digit demo Aadhaar IDs (VIDs) & field encryption.
- **Tamper-Evident Audit Ledger**: Blockchain-style SHA-256 hash chaining of all verification events.

> ⚠️ **Disclaimer:** Educational prototype. Uses synthetic demo identifiers and never connects to real Aadhaar/UIDAI databases.
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register API routers
app.include_router(auth_router)
app.include_router(identity_router)
app.include_router(voice_router)
app.include_router(audit_router)


@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint for Docker container and orchestrator."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
    }


@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Serves the interactive web portal."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "AadhaarVoice API is running. Visit /docs for OpenAPI specifications."}
