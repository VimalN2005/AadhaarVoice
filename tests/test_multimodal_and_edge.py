"""
Unit and Integration Tests for Multi-Modal Lip-Sync Liveness and Edge-AI 1KB Verification.
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.ml.multimodal_lipsync import get_multimodal_detector, MultiModalLipSyncDetector
from app.core.cancellable_biometrics import generate_citizen_salt
from app.core.security import encrypt_field
from app.ml.voice_biometrics import serialize_embedding
from app.db.session import SessionLocal
from app.db.models import VoiceProfile


client = TestClient(app)


def test_multimodal_genuine_live_speech():
    detector = get_multimodal_detector()
    res = detector.generate_synthetic_scenario("genuine_live")
    assert res["liveness_verified"] is True
    assert res["verdict"] == "LIVENESS_VERIFIED"
    assert res["correlation_score"] >= 0.55
    assert abs(res["estimated_lag_ms"]) <= 120.0
    assert res["risk_level"] == "LOW"


def test_multimodal_speaker_replay_attack():
    detector = get_multimodal_detector()
    res = detector.generate_synthetic_scenario("speaker_replay_spoof")
    assert res["liveness_verified"] is False
    assert res["verdict"] == "SPOOF_REPLAY_ATTACK"
    assert res["risk_level"] == "CRITICAL"
    assert "Replay Attack" in res["reasoning"]


def test_multimodal_silent_mime_spoof():
    detector = get_multimodal_detector()
    res = detector.generate_synthetic_scenario("silent_mime_spoof")
    assert res["liveness_verified"] is False
    assert res["verdict"] == "SPOOF_SILENT_MIME"
    assert res["risk_level"] == "CRITICAL"


def test_multimodal_deepfake_desync_spoof():
    detector = get_multimodal_detector()
    res = detector.generate_synthetic_scenario("deepfake_desync_spoof")
    assert res["liveness_verified"] is False
    assert res["verdict"] == "SPOOF_AUDIOVISUAL_DESYNC"


def test_multimodal_api_simulate():
    response = client.post("/api/multimodal/simulate-scenario", json={"scenario": "genuine_live"})
    assert response.status_code == 200
    data = response.json()
    assert data["liveness_verified"] is True
    assert data["verdict"] == "LIVENESS_VERIFIED"

    # Test replay spoof via API
    resp_replay = client.post("/api/multimodal/simulate-scenario", json={"scenario": "speaker_replay_spoof"})
    assert resp_replay.status_code == 200
    assert resp_replay.json()["verdict"] == "SPOOF_REPLAY_ATTACK"


def test_edge_vector_verification_api():
    # Setup dummy enrolled profile
    demo_vid = "000088889999"
    db = SessionLocal()
    existing = db.query(VoiceProfile).filter(VoiceProfile.demo_vid == demo_vid).first()
    if existing:
        db.delete(existing)
        db.commit()

    dummy_emb = np.random.randn(192).astype(np.float32)
    dummy_emb /= np.linalg.norm(dummy_emb)

    profile = VoiceProfile(
        demo_vid=demo_vid,
        full_name_encrypted=encrypt_field("Edge Test Citizen"),
        embedding_hash="dummyhash",
        embedding_json=serialize_embedding(dummy_emb),
    )
    db.add(profile)
    db.commit()
    db.close()

    # Match request with same vector
    payload = {
        "demo_vid": demo_vid,
        "edge_vector": dummy_emb.tolist(),
        "client_compression": "1KB_ORTHONORMAL_HASH",
        "client_processing_time_ms": 18.5,
    }
    response = client.post("/api/multimodal/verify-edge-vector", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["verified"] is True
    assert res_data["similarity_score"] >= 0.95
    assert res_data["bandwidth_metrics"]["rural_2g_compatible"] is True
    assert res_data["bandwidth_metrics"]["edge_vector_payload_kb"] < 1.0
