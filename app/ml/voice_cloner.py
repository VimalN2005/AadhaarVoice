"""
Voice Cloning and Speech Synthesis Module.
Generates synthetic speech modeled after the speaker's pitch, timbre, and formant characteristics.
Produces playable WAV audio for interactive demos and anti-spoofing testing.
"""

import math
import numpy as np
from scipy import signal
from app.ml.audio_processor import write_wav_bytes


# Formant frequency presets for vowel phonetics (F1, F2, F3 in Hz)
VOWEL_FORMANTS = {
    "a": (730.0, 1090.0, 2440.0),
    "e": (530.0, 1840.0, 2480.0),
    "i": (270.0, 2290.0, 3010.0),
    "o": (570.0, 840.0, 2410.0),
    "u": (300.0, 870.0, 2240.0),
    "neutral": (500.0, 1500.0, 2500.0),
}


def synthesize_formant_speech(
    text: str,
    pitch_f0: float = 140.0,
    sample_rate: int = 16000,
    speaking_rate: float = 1.0,
    is_cloned_vocoder: bool = True
) -> np.ndarray:
    """
    Synthesizes acoustic speech using resonant formant filtering tuned to speaker's fundamental pitch.
    If `is_cloned_vocoder` is True, injects synthetic vocoder harmonics and low-jitter characteristics
    typical of neural TTS models.
    """
    words = text.strip().lower().split()
    if not words:
        words = ["aadhaar", "voice", "verified"]

    audio_segments = []

    # Map words to phonetic approximations
    for word in words:
        # Determine vowel sound
        vowel_key = "neutral"
        for char in word:
            if char in VOWEL_FORMANTS:
                vowel_key = char
                break
        f1_base, f2_base, f3_base = VOWEL_FORMANTS[vowel_key]
        # Vocal tract length acoustic scaling
        vocal_scale = (pitch_f0 / 140.0) ** 0.35
        f1, f2, f3 = f1_base * vocal_scale, f2_base * vocal_scale, f3_base * vocal_scale
        # Duration based on word length
        duration = max(0.20, min(0.60, len(word) * 0.08 / speaking_rate))
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)

        # Glottal pulse excitation generator
        # If cloned/vocoded, pitch is artificially ultra-stable (low micro-jitter)
        # If natural simulation, adds subtle vibrato/jitter
        if is_cloned_vocoder:
            pitch_contour = pitch_f0 * np.ones_like(t)
        else:
            vibrato = 1.5 * np.sin(2 * np.pi * 5.5 * t)
            jitter_noise = np.random.normal(0, 0.008 * pitch_f0, len(t))
            pitch_contour = pitch_f0 + vibrato + jitter_noise

        phase = np.cumsum(2 * np.pi * pitch_contour / sample_rate)
        # Pulse waveform (Rosenberg glottal pulse approximation)
        glottal = signal.sawtooth(phase, width=0.7)

        # Formant resonator filters (2nd order bandpass biquads)
        def apply_resonator(sig, f_res, bandwidth=80.0):
            r = np.exp(-np.pi * bandwidth / sample_rate)
            theta = 2 * np.pi * f_res / sample_rate
            b = [1.0 - r, 0, -(1.0 - r)]
            a = [1.0, -2.0 * r * np.cos(theta), r * r]
            return signal.lfilter(b, a, sig)

        vocal_out = (
            apply_resonator(glottal, f1, 90.0) * 1.0 +
            apply_resonator(glottal, f2, 110.0) * 0.6 +
            apply_resonator(glottal, f3, 140.0) * 0.3
        )

        # Envelope window (attack, sustain, decay)
        attack_len = int(n_samples * 0.15)
        decay_len = int(n_samples * 0.20)
        sustain_len = n_samples - attack_len - decay_len
        env = np.concatenate([
            np.linspace(0, 1, attack_len),
            np.ones(sustain_len),
            np.linspace(1, 0, decay_len)
        ])
        if len(env) < n_samples:
            env = np.pad(env, (0, n_samples - len(env)), mode="constant")
        else:
            env = env[:n_samples]

        word_audio = vocal_out * env

        # Add brief inter-word silence
        silence_samples = int(sample_rate * 0.08)
        word_audio = np.pad(word_audio, (0, silence_samples), mode="constant")
        audio_segments.append(word_audio)

    full_audio = np.concatenate(audio_segments) if audio_segments else np.zeros(sample_rate)

    # Normalize amplitude
    max_val = np.max(np.abs(full_audio))
    if max_val > 1e-6:
        full_audio = (full_audio / max_val) * 0.90

    return full_audio.astype(np.float32)


def clone_speaker_voice(
    text: str,
    target_pitch_f0: float = 140.0,
    sample_rate: int = 16000,
    is_vocoded_deepfake: bool = True
) -> bytes:
    """
    Clones voice using speaker's acoustic profile and generates WAV bytes.
    """
    audio_data = synthesize_formant_speech(
        text=text,
        pitch_f0=target_pitch_f0,
        sample_rate=sample_rate,
        is_cloned_vocoder=is_vocoded_deepfake
    )
    return write_wav_bytes(audio_data, sample_rate=sample_rate)
