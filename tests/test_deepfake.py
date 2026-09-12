"""
Unit Tests for Deepfake and Anti-Spoofing Detection.
"""

import numpy as np
import pytest
from app.ml.deepfake_detector import detect_deepfake
from app.ml.voice_cloner import synthesize_formant_speech


def test_deepfake_detector_on_natural_speech():
    # Natural speech has organic micro-jitter and smooth harmonic decay
    natural_speech = synthesize_formant_speech(
        "Aadhaar identity verification system active",
        pitch_f0=140.0,
        is_cloned_vocoder=False
    )
    report = detect_deepfake(natural_speech)

    assert "is_synthetic" in report
    assert "synthetic_probability" in report
    assert "risk_level" in report
    # Natural speech should have low synthetic probability
    assert report["synthetic_probability"] < 0.65
    assert report["is_synthetic"] is False


def test_deepfake_detector_on_vocoded_spoof():
    # Vocoded deepfake speech has artificially flattened pitch and robotic artifacts
    vocoded_speech = synthesize_formant_speech(
        "Aadhaar identity verification system active",
        pitch_f0=140.0,
        is_cloned_vocoder=True
    )
    report = detect_deepfake(vocoded_speech)

    # Vocoded sample should trigger synthetic detection or higher synthetic probability
    assert report["synthetic_probability"] >= 0.50
    assert report["risk_level"] in ["HIGH", "CRITICAL", "MEDIUM"]
