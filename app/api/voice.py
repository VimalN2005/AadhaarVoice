"""
Voice Biometrics, Verification, Deepfake Detection, and Cloning API.
"""

from datetime import datetime, timezone
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import VoiceProfile, VerificationLog, LivenessChallenge
from app.core.config import settings
from app.core.verhoeff import validate_verhoeff, format_aadhaar
from app.core.security import (
    encrypt_field,
    decrypt_field,
    hash_biometric_template,
    compute_audit_hash,
)
from app.ml.audio_processor import preprocess_audio, write_wav_bytes
from app.ml.feature_extractor import extract_all_features
from app.ml.voice_biometrics import (
    generate_voice_embedding,
    verify_speaker,
    serialize_embedding,
    deserialize_embedding,
)
from app.ml.deepfake_detector import detect_deepfake
from app.ml.neural_anti_spoof import get_neural_anti_spoof_classifier
from app.ml.denoiser import enhance_indian_ambient_speech
from app.core.cancellable_biometrics import generate_citizen_salt, shred_audio_buffer
from app.ml.voice_cloner import clone_speaker_voice
from app.ml.liveness import generate_challenge

router = APIRouter(prefix="/api/voice", tags=["Voice Engine"])


class CloneRequestSchema(BaseModel):
    text: str
    demo_vid: Optional[str] = None
    target_pitch_hz: Optional[float] = 140.0
    simulate_deepfake: bool = True


@router.post("/enroll")
async def enroll_voice(
    demo_vid: str = Form(...),
    full_name: str = Form(...),
    phone: Optional[str] = Form(None),
    engine: str = Form("deep_neural"),
    denoise: bool = Form(True),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Enrolls a new voice biometric identity profile.
    - Validates 12-digit demo VID using Verhoeff checksum.
    - Applies Indian ambient noise suppression (fan, traffic hum) if enabled.
    - Extracts 192-dimensional ECAPA-TDNN / Baseline biometric embedding.
    - Encrypts demographic fields and stores irreversible biometric hash.
    - Zeroizes audio memory buffer for DPDP Act 2023 compliance.
    """
    clean_vid = "".join(filter(str.isdigit, demo_vid))
    if len(clean_vid) != 12 or not validate_verhoeff(clean_vid):
        raise HTTPException(
            status_code=400,
            detail="Invalid Aadhaar/VID. Must be a 12-digit number passing the Verhoeff checksum."
        )

    # Check if VID already enrolled
    existing = db.query(VoiceProfile).filter(VoiceProfile.demo_vid == clean_vid).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Voice profile for VID {format_aadhaar(clean_vid, mask=True)} already exists."
        )

    audio_bytes = await audio_file.read()
    if len(audio_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Audio file is empty or corrupted.")

    try:
        signal, sr = preprocess_audio(audio_bytes, target_sr=settings.SAMPLE_RATE)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Audio decoding error: {str(e)}")

    if len(signal) < sr * 0.5:
        raise HTTPException(
            status_code=400,
            detail="Audio sample too short. Please provide at least 1.0 second of clear speech."
        )

    # Indian Ambient Noise Suppression
    snr_gain = 0.0
    if denoise:
        denoise_pkg = enhance_indian_ambient_speech(signal, sr)
        signal = denoise_pkg["enhanced_audio"]
        snr_gain = denoise_pkg["snr_improvement_db"]

    # Extract features and 192-dim embedding (ECAPA-TDNN or Baseline)
    feats = extract_all_features(signal, sr)
    embedding = generate_voice_embedding(signal, sr, engine=engine)
    embedding_json = serialize_embedding(embedding)
    emb_hash = hash_biometric_template(embedding.tobytes())

    # DPDP Act 2023: Zero raw audio memory retention
    shred_audio_buffer(signal)

    # Create VoiceProfile record
    profile = VoiceProfile(
        demo_vid=clean_vid,
        full_name_encrypted=encrypt_field(full_name),
        phone_encrypted=encrypt_field(phone or ""),
        embedding_hash=emb_hash,
        embedding_json=embedding_json,
        pitch_hz=feats["pitch_f0_hz"],
        sample_duration_seconds=feats["duration_seconds"],
        enrollment_status="ACTIVE",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "success": True,
        "message": "Voice biometric profile enrolled successfully.",
        "profile_id": profile.id,
        "demo_vid": clean_vid,
        "masked_vid": format_aadhaar(clean_vid, mask=True),
        "holder_name": full_name,
        "engine_used": "Proposed ECAPA-TDNN Deep SE-TDNN" if engine == "deep_neural" else "Baseline Handcrafted MFCC",
        "ambient_denoised": denoise,
        "snr_improvement_db": snr_gain,
        "features": {
            "pitch_f0_hz": feats["pitch_f0_hz"],
            "pitch_jitter": feats["pitch_jitter"],
            "spectral_centroid_hz": feats["spectral_centroid_hz"],
            "duration_seconds": feats["duration_seconds"],
        },
        "embedding_dimensions": 192,
        "embedding_sha256": emb_hash,
        "dpdp_act_compliance": {
            "zero_raw_audio_stored": True,
            "statute": "DPDP Act 2023 Sec 8 Safeguards",
        },
    }


@router.post("/verify")
async def verify_voice(
    request: Request,
    demo_vid: str = Form(...),
    challenge_id: Optional[str] = Form(None),
    engine: str = Form("deep_neural"),
    denoise: bool = Form(True),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Performs 1:1 voice biometric authentication against enrolled template:
    1. Preprocesses candidate audio with Indian ambient noise suppression
    2. Deep neural + heuristic anti-spoofing detection (ElevenLabs/XTTS defense)
    3. Cosine similarity matching using selected engine (ECAPA-TDNN vs Baseline)
    4. Dynamic anti-replay challenge verification
    5. Append tamper-evident audit ledger record
    6. Purges raw audio from memory (DPDP Act 2023)
    """
    clean_vid = "".join(filter(str.isdigit, demo_vid))
    profile = db.query(VoiceProfile).filter(VoiceProfile.demo_vid == clean_vid).first()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"No voice biometric profile found for VID {format_aadhaar(clean_vid, mask=True)}."
        )

    audio_bytes = await audio_file.read()
    if len(audio_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Audio file empty or corrupted.")

    signal, sr = preprocess_audio(audio_bytes, target_sr=settings.SAMPLE_RATE)
    if len(signal) < sr * 0.4:
        raise HTTPException(status_code=400, detail="Verification sample too short.")

    # Indian Ambient Noise Suppression
    snr_gain = 0.0
    if denoise:
        denoise_pkg = enhance_indian_ambient_speech(signal, sr)
        signal = denoise_pkg["enhanced_audio"]
        snr_gain = denoise_pkg["snr_improvement_db"]

    # 1. Anti-Spoofing: Baseline Heuristic + Neural AASIST Detection
    baseline_deepfake = detect_deepfake(signal, sr)
    neural_clf = get_neural_anti_spoof_classifier()
    neural_deepfake = neural_clf.analyze_neural_deepfake(signal, sr)

    is_synthetic_flag = baseline_deepfake["is_synthetic"] or neural_deepfake["is_synthetic"]
    max_spoof_prob = max(baseline_deepfake["synthetic_probability"], neural_deepfake["deepfake_probability"])

    # 2. Extract Candidate Embedding & Match
    candidate_embedding = generate_voice_embedding(signal, sr, engine=engine)
    enrolled_embedding = deserialize_embedding(profile.embedding_json)
    match_result = verify_speaker(enrolled_embedding, candidate_embedding)

    # DPDP Act 2023 Memory Zeroization
    shred_audio_buffer(signal)

    # 3. Liveness Check
    challenge_passed = True
    if challenge_id:
        challenge = db.query(LivenessChallenge).filter(
            LivenessChallenge.challenge_id == challenge_id,
            LivenessChallenge.demo_vid == clean_vid,
            LivenessChallenge.is_used == False
        ).first()

        now = datetime.now(timezone.utc)
        if not challenge or challenge.expires_at.replace(tzinfo=timezone.utc) < now:
            challenge_passed = False
        else:
            challenge.is_used = True
            db.commit()

    # Determine final authentication status
    if is_synthetic_flag:
        status_str = "SPOOF_DETECTED"
        verified = False
        failure_reason = "Synthetic/cloned deepfake voice pattern detected by neural anti-spoofing engine."
    elif not match_result["is_match"]:
        status_str = "REJECTED"
        verified = False
        failure_reason = f"Voice similarity ({match_result['display_score_percent']}%) below biometric threshold."
    elif not challenge_passed:
        status_str = "REJECTED"
        verified = False
        failure_reason = "Liveness challenge failed or expired."
    else:
        status_str = "AUTHENTICATED"
        verified = True
        failure_reason = None

    # 4. Tamper-evident Audit Chaining
    last_log = db.query(VerificationLog).order_by(VerificationLog.id.desc()).first()
    prev_hash = last_log.current_hash if last_log else "0" * 64
    now_iso = datetime.now(timezone.utc).isoformat()
    audit_data_str = f"{clean_vid}:{verified}:{match_result['cosine_similarity']}:{max_spoof_prob}"
    current_hash = compute_audit_hash(prev_hash, now_iso, audit_data_str)

    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")[:250]

    log_entry = VerificationLog(
        profile_id=profile.id,
        demo_vid=clean_vid,
        verified=verified,
        similarity_score=match_result["cosine_similarity"],
        deepfake_score=max_spoof_prob,
        is_synthetic=is_synthetic_flag,
        risk_level=neural_deepfake["risk_level"] if neural_deepfake["is_synthetic"] else baseline_deepfake["risk_level"],
        challenge_passed=challenge_passed,
        status=status_str,
        failure_reason=failure_reason,
        ip_address=client_ip,
        client_user_agent=user_agent,
        previous_hash=prev_hash,
        current_hash=current_hash,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return {
        "verified": verified,
        "status": status_str,
        "failure_reason": failure_reason,
        "demo_vid": clean_vid,
        "masked_vid": format_aadhaar(clean_vid, mask=True),
        "holder_name": decrypt_field(profile.full_name_encrypted),
        "engine_used": "Proposed ECAPA-TDNN Deep SE-TDNN" if engine == "deep_neural" else "Baseline Handcrafted MFCC",
        "ambient_denoised": denoise,
        "snr_improvement_db": snr_gain,
        "biometric_score": {
            "similarity_percent": match_result["display_score_percent"],
            "cosine_similarity": match_result["cosine_similarity"],
            "confidence": match_result["confidence"],
            "threshold": match_result["threshold_used"],
        },
        "anti_spoofing": {
            "is_synthetic": is_synthetic_flag,
            "deepfake_probability_percent": round(max_spoof_prob * 100, 2),
            "risk_level": neural_deepfake["risk_level"] if neural_deepfake["is_synthetic"] else baseline_deepfake["risk_level"],
            "verdict": neural_deepfake["verdict"] if neural_deepfake["is_synthetic"] else baseline_deepfake["verdict"],
            "neural_defense": neural_deepfake,
            "heuristic_forensics": baseline_deepfake["forensic_breakdown"],
        },
        "audit": {
            "log_id": log_entry.id,
            "block_hash": current_hash,
            "previous_hash": prev_hash,
            "timestamp": log_entry.timestamp.isoformat(),
        }
    }


@router.post("/detect-deepfake")
async def detect_deepfake_endpoint(audio_file: UploadFile = File(...)):
    """
    Dedicated Anti-Spoofing and Deepfake Analysis endpoint.
    Scans audio file for neural vocoder signatures, phase discontinuities, and unnatural pitch.
    """
    audio_bytes = await audio_file.read()
    if len(audio_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Audio file empty or corrupted.")

    signal, sr = preprocess_audio(audio_bytes, target_sr=settings.SAMPLE_RATE)
    report = detect_deepfake(signal, sr)
    feats = extract_all_features(signal, sr)

    return {
        "analysis": report,
        "audio_metrics": {
            "duration_seconds": feats["duration_seconds"],
            "pitch_f0_hz": feats["pitch_f0_hz"],
            "spectral_centroid_hz": feats["spectral_centroid_hz"],
            "spectral_flatness": feats["spectral_flatness"],
            "zero_crossing_rate": feats["zero_crossing_rate"],
        }
    }


@router.post("/clone")
async def clone_voice_endpoint(req: CloneRequestSchema, db: Session = Depends(get_db)):
    """
    Synthesizes cloned speech adapting the pitch and formant profile of an enrolled speaker.
    Returns standard audio/wav binary stream.
    """
    target_pitch = req.target_pitch_hz or 140.0

    if req.demo_vid:
        clean_vid = "".join(filter(str.isdigit, req.demo_vid))
        profile = db.query(VoiceProfile).filter(VoiceProfile.demo_vid == clean_vid).first()
        if profile and profile.pitch_hz > 50.0:
            target_pitch = profile.pitch_hz

    wav_bytes = clone_speaker_voice(
        text=req.text,
        target_pitch_f0=target_pitch,
        sample_rate=settings.SAMPLE_RATE,
        is_vocoded_deepfake=req.simulate_deepfake
    )

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": 'attachment; filename="cloned_speech.wav"'}
    )


@router.get("/liveness-challenge")
def get_liveness_challenge(demo_vid: str, db: Session = Depends(get_db)):
    """
    Issues a randomized, single-use verbal challenge to defend against replay attacks.
    """
    clean_vid = "".join(filter(str.isdigit, demo_vid))
    challenge_data = generate_challenge(clean_vid, expire_seconds=settings.LIVENESS_EXPIRATION_SECONDS)

    # Store in database
    challenge_rec = LivenessChallenge(
        challenge_id=challenge_data["challenge_id"],
        demo_vid=clean_vid,
        passphrase_text=challenge_data["passphrase_text"],
        passphrase_phonetic=challenge_data["passphrase_phonetic_en"],
        expires_at=datetime.fromisoformat(challenge_data["expires_at"]),
    )
    db.add(challenge_rec)
    db.commit()

    return challenge_data
