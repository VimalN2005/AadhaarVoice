"""
Sample Audio Generator Script.
Generates realistic demo WAV files for offline testing, presentations, and automated verification:
1. authentic_speaker_1.wav (Natural male vocal profile ~130 Hz)
2. authentic_speaker_1_verify.wav (Second sample of Speaker 1 for matching)
3. authentic_speaker_2.wav (Natural female vocal profile ~220 Hz)
4. synthetic_deepfake_clone.wav (Vocoded robotic/deepfake spoof sample of Speaker 1)
"""

from pathlib import Path
import sys

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np
from app.ml.voice_cloner import synthesize_formant_speech
from app.ml.audio_processor import write_wav_bytes

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def generate_all_samples():
    print(f"Generating synthetic audio test suite in: {SAMPLES_DIR}")

    # 1. Speaker 1 - Enrollment sample
    spk1_audio = synthesize_formant_speech(
        text="Aadhaar voice identity verification protocol active my voice is secure",
        pitch_f0=128.0,
        sample_rate=16000,
        is_cloned_vocoder=False
    )
    p1 = SAMPLES_DIR / "authentic_speaker_1.wav"
    p1.write_bytes(write_wav_bytes(spk1_audio))
    print(f"[+] Created: {p1.name} ({len(spk1_audio) / 16000:.2f}s, Pitch: 128 Hz, Natural)")

    # 2. Speaker 1 - Verification sample (slightly modulated cadence)
    spk1_verify_audio = synthesize_formant_speech(
        text="Aadhaar auth confirm identity verification approved",
        pitch_f0=130.0,
        sample_rate=16000,
        speaking_rate=1.05,
        is_cloned_vocoder=False
    )
    p2 = SAMPLES_DIR / "authentic_speaker_1_verify.wav"
    p2.write_bytes(write_wav_bytes(spk1_verify_audio))
    print(f"[+] Created: {p2.name} ({len(spk1_verify_audio) / 16000:.2f}s, Pitch: 130 Hz, Natural)")

    # 3. Speaker 2 - Different person (Higher pitch, different cadence)
    spk2_audio = synthesize_formant_speech(
        text="Identity verification request access confirmed for user two",
        pitch_f0=218.0,
        sample_rate=16000,
        is_cloned_vocoder=False
    )
    p3 = SAMPLES_DIR / "authentic_speaker_2.wav"
    p3.write_bytes(write_wav_bytes(spk2_audio))
    print(f"[+] Created: {p3.name} ({len(spk2_audio) / 16000:.2f}s, Pitch: 218 Hz, Natural)")

    # 4. Synthetic Deepfake Spoof Sample (Trained/cloned on Speaker 1, but synthesized with vocoder artifacts)
    spoof_audio = synthesize_formant_speech(
        text="Aadhaar voice identity verification protocol active my voice is secure",
        pitch_f0=128.0,
        sample_rate=16000,
        is_cloned_vocoder=True  # Injects robotic flat-pitch and vocoder phase artifacts
    )
    p4 = SAMPLES_DIR / "synthetic_deepfake_clone.wav"
    p4.write_bytes(write_wav_bytes(spoof_audio))
    print(f"[+] Created: {p4.name} ({len(spoof_audio) / 16000:.2f}s, Synthetic Vocoder Spoof)")

    print("\nAll demo samples successfully generated and ready for testing!")


if __name__ == "__main__":
    generate_all_samples()
