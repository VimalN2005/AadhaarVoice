"""
Identity and Synthetic Aadhaar Virtual ID (VID) API.
Handles:
- Generation of synthetic 12-digit demo Aadhaar numbers with valid Verhoeff check digits
- Verhoeff validation and checksum verification
- Enrolled identity directory listing (with masked VIDs and decrypted names)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import VoiceProfile
from app.core.verhoeff import (
    generate_demo_aadhaar,
    validate_verhoeff,
    format_aadhaar,
)
from app.core.security import decrypt_field

router = APIRouter(prefix="/api/identity", tags=["Identity & Verhoeff"])


class ValidateVIDRequest(BaseModel):
    vid: str


class EnrolledProfileResponse(BaseModel):
    id: int
    demo_vid: str
    masked_vid: str
    full_name: str
    pitch_hz: float
    sample_duration_seconds: float
    status: str
    created_at: str


@router.get("/generate-demo-vid")
def generate_vid(prefix: str = Query("0000", pattern=r"^\d{4}$")):
    """
    Generates a cryptographically valid synthetic 12-digit Aadhaar/VID
    that satisfies the Verhoeff dihedral group D5 checksum.
    Always uses sandbox demo prefixes (0000 or 9999).
    """
    vid = generate_demo_aadhaar(prefix=prefix)
    return {
        "demo_vid": vid,
        "formatted_vid": format_aadhaar(vid, mask=False),
        "masked_vid": format_aadhaar(vid, mask=True),
        "checksum_valid": True,
        "algorithm": "Verhoeff (D5)",
        "disclaimer": "Synthetic sandbox identifier. Not real Aadhaar/UIDAI biometric data."
    }


@router.post("/validate-vid")
def validate_vid(req: ValidateVIDRequest):
    """
    Verifies that an input 12-digit number satisfies the Verhoeff checksum.
    """
    cleaned = "".join(filter(str.isdigit, req.vid))
    if len(cleaned) != 12:
        return {
            "valid": False,
            "error": "VID must be exactly 12 digits in length",
            "vid": req.vid,
        }

    is_valid = validate_verhoeff(cleaned)
    return {
        "valid": is_valid,
        "vid": cleaned,
        "formatted_vid": format_aadhaar(cleaned, mask=False),
        "algorithm": "Verhoeff",
    }


@router.get("/profiles", response_model=List[EnrolledProfileResponse])
def list_enrolled_profiles(db: Session = Depends(get_db)):
    """
    Returns list of enrolled biometric identity profiles with demographic fields decrypted.
    """
    profiles = db.query(VoiceProfile).order_by(VoiceProfile.created_at.desc()).all()
    results = []
    for p in profiles:
        results.append({
            "id": p.id,
            "demo_vid": p.demo_vid,
            "masked_vid": format_aadhaar(p.demo_vid, mask=True),
            "full_name": decrypt_field(p.full_name_encrypted),
            "pitch_hz": p.pitch_hz,
            "sample_duration_seconds": p.sample_duration_seconds,
            "status": p.enrollment_status,
            "created_at": p.created_at.isoformat() if p.created_at else "",
        })
    return results
