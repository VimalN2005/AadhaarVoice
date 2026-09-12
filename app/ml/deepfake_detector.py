"""
Deepfake and Synthetic Voice Detection Module (Anti-Spoofing).
Analyzes audio for forensic signatures of neural vocoders, voice cloners, and TTS:
1. Micro-jitter and pitch unnatural smoothness
2. High-frequency spectral cutoff and phase discontinuities
3. Spectral flatness and artificial noise floor
4. Formant transition irregularities and spectral flux
"""

from typing import Dict, Any
import numpy as np
from app.ml.feature_extractor import (
    extract_all_features,
    compute_stft,
)
from app.core.config import settings


def detect_deepfake(signal: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
    """
    Performs forensic anti-spoofing and deepfake analysis on an audio signal.
    Returns probability score of AI synthesis, classification, and detailed forensic markers.
    """
    if len(signal) < sample_rate * 0.2:  # Less than 200ms
        return {
            "is_synthetic": False,
            "synthetic_probability": 0.1,
            "risk_level": "LOW",
            "forensic_breakdown": {
                "pitch_naturalness": 0.9,
                "high_frequency_artifact_score": 0.1,
                "spectral_flatness_score": 0.1,
                "temporal_flux_score": 0.2,
            },
            "verdict": "REAL_HUMAN",
            "recommendation": "Audio duration too short for definitive forensic inspection."
        }

    feats = extract_all_features(signal, sample_rate)
    stft = compute_stft(signal)
    magnitude = np.abs(stft)

    # 1. Pitch Jitter analysis: Human vocal cords exhibit micro-perturbations (0.005 - 0.040).
    # Vocoders and linear predictive synthesis often produce robotic flat pitch (jitter < 0.003)
    # or hyper-jitter artifacts (> 0.08).
    jitter = feats["pitch_jitter"]
    if jitter < 0.0035:
        jitter_penalty = 0.85  # Overly smooth robotic synthesizer
    elif jitter > 0.065:
        jitter_penalty = 0.70  # Vocoder phase concatenation artifact
    elif 0.007 <= jitter <= 0.035:
        jitter_penalty = 0.10  # Natural human range
    else:
        jitter_penalty = 0.35

    # 2. Spectral Flatness & Background noise consistency
    # Neural vocoders often introduce synthetic silence or uniform frequency distributions
    flatness = feats["spectral_flatness"]
    if flatness > 0.08:
        flatness_penalty = 0.80  # Unnatural white noise / vocoder buzz
    elif flatness < 0.0002:
        flatness_penalty = 0.75  # Over-clamped synthetic zero-floor
    else:
        flatness_penalty = 0.15

    # 3. High-frequency roll-off & cutoff analysis
    # Neural TTS often has an aggressive anti-aliasing cutoff or abnormal high-frequency harmonics
    n_freq_bins = magnitude.shape[1]
    low_band_power = np.mean(magnitude[:, : int(n_freq_bins * 0.4)])
    high_band_power = np.mean(magnitude[:, int(n_freq_bins * 0.75) :])
    ratio = (high_band_power / (low_band_power + 1e-9))
    if ratio < 0.0005:
        high_freq_penalty = 0.70  # Abrupt artificial low-pass filter
    elif ratio > 0.45:
        high_freq_penalty = 0.75  # High-frequency robotic distortion
    else:
        high_freq_penalty = 0.15

    # 4. Spectral Flux (temporal transition continuity)
    flux = np.sqrt(np.mean(np.diff(magnitude, axis=0) ** 2)) if len(magnitude) > 1 else 0.0
    if flux < 0.005:
        flux_penalty = 0.75  # Static unnatural robotic timbre
    else:
        flux_penalty = 0.20

    # Weighted composite forensic score
    weights = [0.35, 0.25, 0.25, 0.15]
    synthetic_score = float(
        weights[0] * jitter_penalty +
        weights[1] * flatness_penalty +
        weights[2] * high_freq_penalty +
        weights[3] * flux_penalty
    )

    threshold = settings.DEEPFAKE_DETECTION_THRESHOLD
    is_synthetic = bool(synthetic_score >= threshold)

    if synthetic_score >= 0.80:
        risk_level = "CRITICAL"
        verdict = "SYNTHETIC_DEEPFAKE"
        recommendation = "Reject immediately: High confidence neural vocoder / synthetic clone detected."
    elif synthetic_score >= threshold:
        risk_level = "HIGH"
        verdict = "POTENTIAL_SPOOF"
        recommendation = "Reject transaction: Suspicious acoustic artifacts detected."
    elif synthetic_score >= threshold - 0.20:
        risk_level = "MEDIUM"
        verdict = "SUSPICIOUS"
        recommendation = "Step-up authentication required: Request secondary liveness biometric challenge."
    else:
        risk_level = "LOW"
        verdict = "NATURAL_HUMAN"
        recommendation = "Biometric acoustic dynamics consistent with authentic human vocal production."

    return {
        "is_synthetic": is_synthetic,
        "synthetic_probability": round(synthetic_score, 4),
        "synthetic_score_percent": round(synthetic_score * 100, 2),
        "risk_level": risk_level,
        "verdict": verdict,
        "forensic_breakdown": {
            "pitch_unnaturalness": round(jitter_penalty, 3),
            "spectral_flatness_anomaly": round(flatness_penalty, 3),
            "high_frequency_anomaly": round(high_freq_penalty, 3),
            "spectral_flux_stagnation": round(flux_penalty, 3),
            "measured_jitter": round(jitter, 5),
            "measured_flatness": round(flatness, 5),
        },
        "recommendation": recommendation,
    }
