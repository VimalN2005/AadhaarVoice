"""
Unit Tests for Audio Preprocessor and Feature Extractor.
"""

import numpy as np
import pytest
from app.ml.audio_processor import (
    write_wav_bytes,
    read_wav_bytes,
    preprocess_audio,
    resample_audio,
    voice_activity_detection,
)
from app.ml.feature_extractor import (
    extract_all_features,
    compute_mfcc,
    extract_pitch_f0,
    compute_spectral_features,
)


def test_wav_write_read_roundtrip():
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 440 Hz test tone
    signal = 0.5 * np.sin(2 * np.pi * 440.0 * t).astype(np.float32)

    wav_bytes = write_wav_bytes(signal, sample_rate=sr)
    assert len(wav_bytes) > 0

    read_data, read_sr = read_wav_bytes(wav_bytes)
    assert read_sr == sr
    assert len(read_data) == len(signal)
    # Check numerical fidelity within 16-bit quantization tolerance
    np.testing.assert_allclose(read_data, signal, atol=1e-3)


def test_resample_audio():
    orig_sr = 8000
    target_sr = 16000
    t = np.linspace(0, 0.5, int(orig_sr * 0.5), endpoint=False)
    sig = np.sin(2 * np.pi * 200 * t).astype(np.float32)

    resampled = resample_audio(sig, orig_sr, target_sr)
    assert len(resampled) == int(target_sr * 0.5)


def test_voice_activity_detection():
    sr = 16000
    # 0.5s silence, 1s speech tone, 0.5s silence
    silence = np.zeros(int(sr * 0.5), dtype=np.float32)
    t = np.linspace(0, 1.0, int(sr * 1.0), endpoint=False)
    speech = 0.6 * np.sin(2 * np.pi * 300 * t).astype(np.float32)
    full = np.concatenate([silence, speech, silence])

    trimmed = voice_activity_detection(full, sample_rate=sr)
    assert len(trimmed) < len(full)
    assert len(trimmed) >= len(speech) * 0.8


def test_feature_extraction():
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # Harmonic audio signal
    signal = (0.5 * np.sin(2 * np.pi * 150 * t) + 0.3 * np.sin(2 * np.pi * 300 * t)).astype(np.float32)

    feats = extract_all_features(signal, sr)

    assert "mfcc_mean" in feats
    assert len(feats["mfcc_mean"]) == 40
    assert "pitch_f0_hz" in feats
    # F0 should be close to 150 Hz
    assert 130.0 <= feats["pitch_f0_hz"] <= 170.0
    assert "spectral_centroid_hz" in feats
    assert feats["duration_seconds"] == 1.0
