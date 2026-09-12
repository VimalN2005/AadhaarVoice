"""
Unit Tests for Voice Biometrics and Cosine Matching.
"""

import numpy as np
import pytest
from app.ml.voice_biometrics import (
    generate_voice_embedding,
    compute_cosine_similarity,
    verify_speaker,
    serialize_embedding,
    deserialize_embedding,
)
from app.ml.voice_cloner import synthesize_formant_speech


def test_embedding_shape_and_norm():
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    sig = 0.5 * np.sin(2 * np.pi * 180 * t).astype(np.float32)

    emb = generate_voice_embedding(sig, sr)
    assert len(emb) == 192
    norm = np.linalg.norm(emb)
    assert pytest.approx(norm, rel=1e-3) == 1.0


def test_biometric_speaker_discrimination():
    # Speaker 1: Male pitch ~130 Hz
    spk1_a = synthesize_formant_speech("Hello identity access confirm", pitch_f0=130.0, is_cloned_vocoder=False)
    spk1_b = synthesize_formant_speech("Aadhaar verify secure login phrase", pitch_f0=130.0, is_cloned_vocoder=False)

    # Speaker 2: Female pitch ~230 Hz
    spk2 = synthesize_formant_speech("Hello identity access confirm", pitch_f0=230.0, is_cloned_vocoder=False)

    emb1_a = generate_voice_embedding(spk1_a)
    emb1_b = generate_voice_embedding(spk1_b)
    emb2 = generate_voice_embedding(spk2)

    sim_same = compute_cosine_similarity(emb1_a, emb1_b)
    sim_diff = compute_cosine_similarity(emb1_a, emb2)

    # Same speaker similarity must be significantly higher than different speaker
    assert sim_same > sim_diff
    assert sim_diff < 0.80


def test_serialize_deserialize_embedding():
    emb = np.random.randn(192).astype(np.float32)
    emb = emb / np.linalg.norm(emb)

    s = serialize_embedding(emb)
    recovered = deserialize_embedding(s)

    assert len(recovered) == 192
    np.testing.assert_allclose(emb, recovered, atol=1e-5)
