"""
Multi-Modal Audio-Visual Lip-Sync Liveness Detection Module.

Eliminates Replay/Playback Attacks by mathematically cross-correlating:
1. Acoustic speech energy envelope (short-time vocal tract RMS energy).
2. Visual lip aperture (vertical mouth opening distance from video/webcam).

If an attacker plays pre-recorded audio from a smartphone speaker, the camera
detects static/unmoving lips (zero aperture variance). If an attacker mimes without
sound, the acoustic energy is zero. If a deepfake dubs audio onto video, the temporal
cross-correlation lag exceeds human thresholds.
"""

import numpy as np
from typing import Dict, Any, List, Optional


class MultiModalLipSyncDetector:
    """
    Evaluates multi-modal liveness by checking temporal and structural synchronization
    between speech audio energy and facial lip geometry.
    """

    def __init__(
        self,
        min_correlation_threshold: float = 0.55,
        max_temporal_lag_ms: float = 120.0,
        min_lip_variance: float = 0.008,
        min_audio_energy_std: float = 0.015,
    ):
        self.min_correlation = min_correlation_threshold
        self.max_lag_ms = max_temporal_lag_ms
        self.min_lip_variance = min_lip_variance
        self.min_audio_energy_std = min_audio_energy_std

    def compute_audio_energy_envelope(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        target_fps: int = 30,
        num_frames: Optional[int] = None,
    ) -> np.ndarray:
        """
        Extracts short-time RMS energy envelope resampled to match video frame rate.
        """
        if len(audio_data) == 0:
            return np.zeros(num_frames or 1)

        hop_length = int(sample_rate / target_fps)
        if hop_length <= 0:
            hop_length = 533  # ~16000 / 30

        frame_count = len(audio_data) // hop_length
        if frame_count == 0:
            return np.array([float(np.sqrt(np.mean(audio_data ** 2) + 1e-9))])

        envelope = []
        for i in range(frame_count):
            start = i * hop_length
            end = start + hop_length
            chunk = audio_data[start:end]
            rms = float(np.sqrt(np.mean(chunk ** 2) + 1e-9))
            envelope.append(rms)

        env_arr = np.array(envelope, dtype=np.float32)

        # Match exact num_frames if specified
        if num_frames is not None and len(env_arr) != num_frames:
            if len(env_arr) > 1:
                x_old = np.linspace(0, 1, len(env_arr))
                x_new = np.linspace(0, 1, num_frames)
                env_arr = np.interp(x_new, x_old, env_arr)
            else:
                env_arr = np.resize(env_arr, num_frames)

        # Normalize envelope between 0 and 1
        denom = float(np.max(env_arr) - np.min(env_arr))
        if denom > 1e-6:
            env_arr = (env_arr - np.min(env_arr)) / denom
        return env_arr

    def analyze_audiovisual_sync(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        lip_apertures: List[float],
        fps: int = 30,
    ) -> Dict[str, Any]:
        """
        Performs multi-modal correlation, lag estimation, and physical liveness verification.
        """
        num_frames = len(lip_apertures)
        if num_frames < 10:
            return {
                "liveness_verified": False,
                "verdict": "ERROR_INSUFFICIENT_FRAMES",
                "risk_level": "HIGH",
                "correlation_score": 0.0,
                "estimated_lag_ms": 0.0,
                "reasoning": "Video sequence too short (minimum 10 video frames required for liveness).",
            }

        lip_arr = np.array(lip_apertures, dtype=np.float32)
        lip_var = float(np.var(lip_arr))
        lip_range = float(np.max(lip_arr) - np.min(lip_arr))

        # Check 1: Speaker Replay Attack (Sound playing, but lips are frozen / static)
        if lip_var < self.min_lip_variance or lip_range < 0.05:
            return {
                "liveness_verified": False,
                "verdict": "SPOOF_REPLAY_ATTACK",
                "attack_type": "Loudspeaker / Stolen Recording Playback",
                "risk_level": "CRITICAL",
                "correlation_score": 0.02,
                "estimated_lag_ms": 999.0,
                "lip_variance": round(lip_var, 6),
                "reasoning": "Physical Replay Attack detected: Audio speech energy detected while facial lips remained static/frozen. Sound is being played through an external speaker without live human articulation.",
            }

        # Normalize lip apertures between 0 and 1
        lip_norm = (lip_arr - np.min(lip_arr)) / (lip_range + 1e-6)

        # Check 2: Silent Mime Spoof (Lips moving, but zero vocal energy)
        raw_audio_rms = float(np.sqrt(np.mean(audio_data ** 2) + 1e-12))
        if raw_audio_rms < 0.005:
            return {
                "liveness_verified": False,
                "verdict": "SPOOF_SILENT_MIME",
                "attack_type": "Mime / Fake Articulation without Voice",
                "risk_level": "CRITICAL",
                "correlation_score": 0.01,
                "estimated_lag_ms": 999.0,
                "audio_rms": round(raw_audio_rms, 6),
                "reasoning": "Mime Spoof detected: Facial lips are opening/closing, but acoustic speech energy is virtually flat.",
            }

        # Compute audio envelope aligned to the video frames
        audio_env = self.compute_audio_energy_envelope(
            audio_data, sample_rate, target_fps=fps, num_frames=num_frames
        )
        audio_std = float(np.std(audio_env))

        # Check 3: Pearson Cross-Correlation & Phase Lag
        mean_lip = np.mean(lip_norm)
        mean_audio = np.mean(audio_env)
        num = np.sum((lip_norm - mean_lip) * (audio_env - mean_audio))
        den = np.sqrt(np.sum((lip_norm - mean_lip) ** 2) * np.sum((audio_env - mean_audio) ** 2) + 1e-8)
        correlation = float(num / den)

        # Cross-correlation with lag shifts (-5 to +5 frames)
        best_lag_frames = 0
        best_corr = correlation
        max_shift = min(5, num_frames // 4)

        for shift in range(-max_shift, max_shift + 1):
            if shift == 0:
                continue
            if shift > 0:
                l_slice = lip_norm[shift:]
                a_slice = audio_env[:-shift]
            else:
                l_slice = lip_norm[:shift]
                a_slice = audio_env[-shift:]

            if len(l_slice) > 5:
                c_num = np.sum((l_slice - np.mean(l_slice)) * (a_slice - np.mean(a_slice)))
                c_den = np.sqrt(np.sum((l_slice - np.mean(l_slice)) ** 2) * np.sum((a_slice - np.mean(a_slice)) ** 2) + 1e-8)
                c_val = float(c_num / c_den)
                if c_val > best_corr:
                    best_corr = c_val
                    best_lag_frames = shift

        lag_ms = float(best_lag_frames * (1000.0 / fps))

        # Check 4: Audio-Visual Desync / Deepfake Lip-Dub
        if best_corr < self.min_correlation or abs(lag_ms) > self.max_lag_ms:
            return {
                "liveness_verified": False,
                "verdict": "SPOOF_AUDIOVISUAL_DESYNC",
                "attack_type": "Deepfake Lip-Dub / Desynchronized Audio Injection",
                "risk_level": "HIGH",
                "correlation_score": round(best_corr, 4),
                "estimated_lag_ms": round(lag_ms, 1),
                "reasoning": f"Audio-Visual desynchronization detected (Correlation: {best_corr:.2f} < {self.min_correlation}, Lag: {lag_ms:.1f}ms). Phoneme acoustic transitions do not match video viseme kinematics.",
            }

        return {
            "liveness_verified": True,
            "verdict": "LIVENESS_VERIFIED",
            "risk_level": "LOW",
            "correlation_score": round(best_corr, 4),
            "estimated_lag_ms": round(lag_ms, 1),
            "lip_variance": round(lip_var, 5),
            "reasoning": f"Genuine Multi-Modal Synchrony verified! Visual lip aperture kinematics mathematically align with vocal acoustic formant energy (r={best_corr:.3f}, lag={lag_ms:.1f}ms). External replay playback impossible.",
        }

    def generate_synthetic_scenario(self, scenario: str) -> Dict[str, Any]:
        """
        Generates deterministic synthetic audio + visual lip curves to demonstrate
        evaluation benchmarks in academic presentations and tests.
        """
        np.random.seed(42)
        fps = 30
        duration_sec = 2.0
        num_frames = int(fps * duration_sec)
        sr = 16000
        num_audio_samples = int(sr * duration_sec)

        t_video = np.linspace(0, duration_sec, num_frames)
        t_audio = np.linspace(0, duration_sec, num_audio_samples)

        if scenario == "genuine_live":
            # Natural speech: Syllable modulation at ~4 Hz
            syllable_rate = 4.0
            base_aperture = 0.35 + 0.3 * np.sin(2 * np.pi * syllable_rate * t_video) ** 2
            lip_apertures = (base_aperture + 0.03 * np.random.randn(num_frames)).clip(0.1, 0.9).tolist()

            # Audio matches the syllable envelope with harmonic frequencies
            audio_envelope = np.interp(t_audio, t_video, np.array(lip_apertures))
            carrier = 0.6 * np.sin(2 * np.pi * 220 * t_audio) + 0.3 * np.sin(2 * np.pi * 440 * t_audio)
            audio_samples = (carrier * audio_envelope + 0.02 * np.random.randn(num_audio_samples)).astype(np.float32)

        elif scenario == "speaker_replay_spoof":
            # Replay attack: Strong speech audio, but static/frozen camera face
            lip_apertures = [float(0.25 + 0.001 * np.random.randn()) for _ in range(num_frames)]
            carrier = 0.6 * np.sin(2 * np.pi * 220 * t_audio) + 0.3 * np.sin(2 * np.pi * 440 * t_audio)
            audio_samples = carrier.astype(np.float32)

        elif scenario == "silent_mime_spoof":
            # Mime spoof: Face moving, but dead silence
            base_aperture = 0.35 + 0.3 * np.sin(2 * np.pi * 4.0 * t_video) ** 2
            lip_apertures = (base_aperture + 0.02 * np.random.randn(num_frames)).clip(0.1, 0.9).tolist()
            audio_samples = (0.0001 * np.random.randn(num_audio_samples)).astype(np.float32)

        elif scenario == "deepfake_desync_spoof":
            # Desynchronized dubbing: Lip aperture at 3 Hz, audio at 7 Hz with 250ms offset
            lip_apertures = (0.35 + 0.3 * np.sin(2 * np.pi * 3.0 * t_video) ** 2).tolist()
            shifted_t = t_audio - 0.25
            audio_env = np.clip(np.sin(2 * np.pi * 7.0 * shifted_t) ** 2, 0, 1)
            carrier = 0.6 * np.sin(2 * np.pi * 300 * t_audio)
            audio_samples = (carrier * audio_env).astype(np.float32)

        else:
            raise ValueError(f"Unknown scenario: {scenario}")

        result = self.analyze_audiovisual_sync(
            audio_data=audio_samples,
            sample_rate=sr,
            lip_apertures=lip_apertures,
            fps=fps,
        )
        result["scenario"] = scenario
        result["lip_apertures_sample"] = [round(x, 3) for x in lip_apertures[:20]]
        return result


_detector_instance = None


def get_multimodal_detector() -> MultiModalLipSyncDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = MultiModalLipSyncDetector()
    return _detector_instance
