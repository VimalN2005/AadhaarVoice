"""
Unit and Integration Tests for 1:N Biometric Vector Search & Explainable AI (XAI) Forensics.
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.ml.vector_search import BiometricVectorIndex
from app.ml.forensic_xai import ForensicXAI
from app.ml.audio_processor import write_wav_bytes


@pytest.fixture
def client():
    return TestClient(app)


def test_vector_index_initialization_and_shape():
    idx = BiometricVectorIndex(embedding_dim=192, default_population_size=500)
    assert idx.embeddings.shape == (500, 192)
    assert len(idx.citizen_vids) == 500

    # Verify unit norm L2 = 1.0
    norms = np.linalg.norm(idx.embeddings, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-4)


def test_vector_1_to_n_search_and_duplicate_detection():
    idx = BiometricVectorIndex(embedding_dim=192, default_population_size=1000)

    # Test Duplicate Query (Existing enrolled vector with small noise)
    target_vector = idx.embeddings[10].copy()
    probe_duplicate = target_vector + np.random.normal(0, 0.02, 192).astype(np.float32)

    res_dup = idx.search_1_to_n(probe_duplicate, top_k=5)
    assert res_dup["is_duplicate_detected"] is True
    assert res_dup["status"] == "DUPLICATE_IDENTITY_PREVENTED"
    assert res_dup["search_latency_ms"] < 25.0  # Sub-millisecond to low ms
    assert res_dup["top_candidates"][0]["demo_vid"] == idx.citizen_vids[10]
    assert res_dup["top_candidates"][0]["cosine_similarity"] > 0.85

    # Test Unique Citizen Query (Orthogonal random vector)
    orthogonal_probe = np.random.randn(192).astype(np.float32)
    orthogonal_probe /= np.linalg.norm(orthogonal_probe)

    res_unique = idx.search_1_to_n(orthogonal_probe, top_k=5)
    assert res_unique["is_duplicate_detected"] is False
    assert res_unique["status"] == "UNIQUE_CITIZEN_VERIFIED"


def test_vector_scalability_benchmark():
    idx = BiometricVectorIndex(embedding_dim=192, default_population_size=500)
    curve = idx.benchmark_scalability_curve()
    assert len(curve) == 5
    for entry in curve:
        assert "population_size" in entry
        assert "ann_latency_ms" in entry
        assert "linear_latency_ms" in entry
        assert "speedup" in entry
        assert entry["ann_latency_ms"] < 20.0


def test_forensic_xai_spectrogram_heatmap():
    xai = ForensicXAI(sample_rate=16000)

    # Synthetic tone with abrupt high-frequency cutoff
    t = np.linspace(0, 1.5, int(16000 * 1.5), endpoint=False)
    synthetic_signal = 0.5 * np.sin(2 * np.pi * 300 * t) + 0.3 * np.sin(2 * np.pi * 700 * t)

    res = xai.generate_spectrogram_heatmap(synthetic_signal, n_time_bins=64, n_freq_bins=64)
    assert res["n_time_bins"] == 64
    assert res["n_freq_bins"] == 64
    assert len(res["spectrogram_grid"]) == 64
    assert len(res["spectrogram_grid"][0]) == 64
    assert isinstance(res["bounding_boxes"], list)
    assert "forensic_explanation" in res


def test_api_biometrics_vector_search_endpoints(client):
    # 1. Index stats
    stats_res = client.get("/api/biometrics/index-stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["status"] == "ONLINE"
    assert stats["embedding_dimensions"] == 192
    assert stats["total_enrolled_citizens"] >= 1000

    # 2. Scalability benchmark curve
    bench_res = client.get("/api/biometrics/stress-test-benchmark")
    assert bench_res.status_code == 200
    bench_data = bench_res.json()
    assert len(bench_data["benchmark_results"]) >= 3

    # 3. 1:N Deduplicate default endpoint
    dedup_res = client.post("/api/biometrics/deduplicate-1-to-n", data={"top_k": 5})
    assert dedup_res.status_code == 200
    dedup_data = dedup_res.json()
    assert "search_latency_ms" in dedup_data
    assert "is_duplicate_detected" in dedup_data
    assert len(dedup_data["top_candidates"]) == 5

    # 4. XAI Spectrogram endpoint
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    sig = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    wav_bytes = write_wav_bytes(sig, sample_rate=sr)

    xai_res = client.post(
        "/api/biometrics/xai-spectrogram",
        files={"audio_file": ("test.wav", wav_bytes, "audio/wav")}
    )
    assert xai_res.status_code == 200
    xai_data = xai_res.json()
    assert "spectrogram_grid" in xai_data
    assert len(xai_data["spectrogram_grid"]) == 64
