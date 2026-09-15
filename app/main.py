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
from app.api.benchmarks import router as benchmarks_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="""
# 🇮🇳 AadhaarVoice: Research-Grade Biometric Voice Identity & Deepfake Defense Platform

An AI-based deep tech research platform featuring:
- **Speaker Recognition**: Pretrained ECAPA-TDNN (192-dim deep SE-TDNN) alongside Handcrafted Baseline.
- **Deepfake & Anti-Spoofing Defense**: AASIST-inspired phase discontinuity and formant transition classification.
- **Indian Ambient Noise Suppression**: Multi-band spectral subtraction & 50Hz/100Hz fan hum filtering.
- **DPDP Act 2023 Compliance**: Cancellable Salted Biometric hashing & zero raw audio storage.
- **Academic Benchmarking**: Live EER computation, FAR vs FRR curves, and CPU latency profiling.
- **Tamper-Evident Audit Ledger**: Blockchain-style SHA-256 hash chaining.

> ⚠️ **Disclaimer:** Educational prototype using synthetic demo identifiers (0000-XXXX-XXXX). Not affiliated with UIDAI.
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
app.include_router(benchmarks_router)


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
