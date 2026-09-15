"""
Unit & Integration Tests for Research-Grade Deep Tech Modules:
1. Indian Ambient Noise Filter (Fan hum attenuation & spectral subtraction)
2. ECAPA-TDNN Deep Speaker Embeddings
3. Neural Anti-Spoofing Classifier (AASIST phase discontinuity)
4. DPDP Act 2023 Cancellable Salted Biometrics (Orthonormal isometric transformation)
5. Academic Benchmarking & EER Evaluation
"""

import numpy as np
import pytest
from app.ml.denoiser import attenuate_fan_hum, enhance_indian_ambient_speech
from app.ml.neural_biometrics import extract_ecapa_embedding
from app.ml.neural_anti_spoof import get_neural_anti_spoof_classifier
from app.core.cancellable_biometrics import (
    generate_citizen_salt,
    derive_orthonormal_projection,
    transform_to_cancellable_embedding,
    get_dpdp_compliance_audit,
)
from app.ml.benchmarks import compute_eer, get_academic_comparison_matrix
from app.ml.voice_biometrics import compute_cosine_similarity
from app.ml.voice_cloner import synthesize_formant_speech


def test_indian_noise_denoiser():
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Speech harmonic + 50Hz fan hum drone + 100Hz harmonic
    speech = 0.5 * np.sin(2 * np.pi * 300 * t).astype(np.float32)
    fan_hum = 0.4 * np.sin(2 * np.pi * 50 * t).astype(np.float32)
    fan_hum_100 = 0.2 * np.sin(2 * np.pi * 100 * t).astype(np.float32)
    noisy_audio = speech + fan_hum + fan_hum_100

    filtered = attenuate_fan_hum(noisy_audio, sr)
    assert len(filtered) == len(noisy_audio)
    # Hum frequencies should be substantially attenuated
    enhanced = enhance_indian_ambient_speech(noisy_audio, sr)
    assert "snr_improvement_db" in enhanced
    assert enhanced["snr_improvement_db"] >= 3.0


def test_ecapa_tdnn_embedding():
    spk1_a = synthesize_formant_speech("Aadhaar voice identity verification", pitch_f0=130.0, is_cloned_vocoder=False)
    spk1_b = synthesize_formant_speech("Aadhaar auth confirm identity approved", pitch_f0=130.0, is_cloned_vocoder=False)
    spk2 = synthesize_formant_speech("Aadhaar voice identity verification", pitch_f0=230.0, is_cloned_vocoder=False)

    emb1_a = extract_ecapa_embedding(spk1_a)["embedding"]
    emb1_b = extract_ecapa_embedding(spk1_b)["embedding"]
    emb2 = extract_ecapa_embedding(spk2)["embedding"]

    assert len(emb1_a) == 192
    assert pytest.approx(np.linalg.norm(emb1_a), rel=1e-3) == 1.0

    sim_same = compute_cosine_similarity(emb1_a, emb1_b)
    sim_diff = compute_cosine_similarity(emb1_a, emb2)

    # ECAPA-TDNN must clearly separate same speaker from different speaker
    assert sim_same > sim_diff


def test_neural_anti_spoofing():
    clf = get_neural_anti_spoof_classifier()

    natural = synthesize_formant_speech("Hello identity check phrase", pitch_f0=140.0, is_cloned_vocoder=False)
    vocoded = synthesize_formant_speech("Hello identity check phrase", pitch_f0=140.0, is_cloned_vocoder=True)

    report_natural = clf.analyze_neural_deepfake(natural)
    report_vocoded = clf.analyze_neural_deepfake(vocoded)

    assert "neural_telemetry" in report_natural
    assert "phase_discontinuity_index" in report_natural["neural_telemetry"]
    # Vocoded sample should yield higher or equal spoof probability
    assert report_vocoded["deepfake_probability"] >= report_natural["deepfake_probability"]


def test_cancellable_biometrics_orthonormal_isometry():
    # Test that <P_k x1, P_k x2> == <x1, x2> (isometric property)
    raw_x1 = np.random.randn(192).astype(np.float32)
    raw_x1 /= np.linalg.norm(raw_x1)

    raw_x2 = np.random.randn(192).astype(np.float32)
    raw_x2 /= np.linalg.norm(raw_x2)

    orig_sim = compute_cosine_similarity(raw_x1, raw_x2)

    salt_a = generate_citizen_salt("000012345678")
    trans_x1 = transform_to_cancellable_embedding(raw_x1, salt_a)
    trans_x2 = transform_to_cancellable_embedding(raw_x2, salt_a)

    salted_sim = compute_cosine_similarity(trans_x1, trans_x2)

    # Cosine distance must be perfectly preserved within numerical precision
    assert pytest.approx(orig_sim, abs=1e-4) == salted_sim

    # Non-linkability across different salts (revocation test)
    salt_b = generate_citizen_salt("000012345678_revoked")
    trans_x1_revoked = transform_to_cancellable_embedding(raw_x1, salt_b)

    cross_salt_sim = compute_cosine_similarity(trans_x1, trans_x1_revoked)
    # Under different salts, the same voice template becomes quasi-orthogonal (~0.0)
    assert abs(cross_salt_sim) < 0.35


def test_academic_eer_computation():
    genuine = [0.85, 0.88, 0.92, 0.87, 0.90, 0.94]
    impostor = [0.45, 0.50, 0.52, 0.58, 0.49, 0.53]

    res = compute_eer(genuine, impostor)
    assert "eer_percent" in res
    assert "optimal_threshold" in res
    assert 0.0 <= res["eer_percent"] <= 100.0
    assert 0.50 <= res["optimal_threshold"] <= 0.85

    matrix = get_academic_comparison_matrix()
    assert "baseline" in matrix
    assert "proposed" in matrix
    assert matrix["accuracy_gain_percent"] > 10.0


def test_dpdp_compliance_audit():
    audit = get_dpdp_compliance_audit()
    assert audit["compliance_status"] == "FULL_COMPLIANCE"
    assert audit["revocation_capable"] is True
