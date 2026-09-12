"""
Integration Tests for FastAPI Endpoints using TestClient.
"""

import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.verhoeff import generate_demo_aadhaar
from app.ml.voice_cloner import synthesize_formant_speech
from app.ml.audio_processor import write_wav_bytes


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def sample_wav_bytes():
    sig = synthesize_formant_speech("Authentication test phrase for identity verify", pitch_f0=135.0, is_cloned_vocoder=False)
    return write_wav_bytes(sig)


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_generate_and_validate_demo_vid(client):
    gen_res = client.get("/api/identity/generate-demo-vid")
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert "demo_vid" in gen_data
    assert len(gen_data["demo_vid"]) == 12

    val_res = client.post("/api/identity/validate-vid", json={"vid": gen_data["demo_vid"]})
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["valid"] is True


def test_voice_enroll_and_verify_pipeline(client, sample_wav_bytes):
    # 1. Generate unique demo VID
    vid = generate_demo_aadhaar(prefix="0000")

    # 2. Enroll Voice Profile
    files = {"audio_file": ("enroll.wav", io.BytesIO(sample_wav_bytes), "audio/wav")}
    data = {"demo_vid": vid, "full_name": "Test Citizen Vimal"}

    enroll_res = client.post("/api/voice/enroll", data=data, files=files)
    assert enroll_res.status_code == 200
    enroll_data = enroll_res.json()
    assert enroll_data["success"] is True
    assert enroll_data["embedding_dimensions"] == 192

    # 3. Verify Voice with same speaker
    verify_files = {"audio_file": ("verify.wav", io.BytesIO(sample_wav_bytes), "audio/wav")}
    verify_data = {"demo_vid": vid}

    verify_res = client.post("/api/voice/verify", data=verify_data, files=verify_files)
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["verified"] is True
    assert v_data["status"] == "AUTHENTICATED"
    assert v_data["biometric_score"]["similarity_percent"] >= 80.0


def test_detect_deepfake_endpoint(client, sample_wav_bytes):
    files = {"audio_file": ("test.wav", io.BytesIO(sample_wav_bytes), "audio/wav")}
    res = client.post("/api/voice/detect-deepfake", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "analysis" in data
    assert "audio_metrics" in data


def test_voice_clone_endpoint(client):
    payload = {
        "text": "Testing voice clone output generation",
        "target_pitch_hz": 150.0,
        "simulate_deepfake": True
    }
    res = client.post("/api/voice/clone", json=payload)
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"
    assert len(res.content) > 1000


def test_audit_logs_and_integrity(client):
    logs_res = client.get("/api/audit/logs")
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert isinstance(logs, list)

    integ_res = client.get("/api/audit/verify-integrity")
    assert integ_res.status_code == 200
    integ = integ_res.json()
    assert integ["status"] == "VALID"
