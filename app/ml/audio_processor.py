"""
Audio Preprocessing and Signal Conditioning Module.
Handles:
- WAV parsing and byte stream decoding
- Stereo to mono conversion
- Resampling to 16 kHz
- Pre-emphasis filtering (0.97)
- Voice Activity Detection (VAD) & silence trimming
- Amplitude normalization
- WAV serialization
"""

import io
import struct
import wave
from typing import Tuple
import numpy as np
from scipy import signal
from app.core.config import settings


def read_wav_bytes(audio_bytes: bytes) -> Tuple[np.ndarray, int]:
    """
    Decodes audio bytes from WAV format into a normalized float32 numpy array and sample rate.
    Handles mono/stereo and various bit depths (16-bit PCM, 24-bit, 32-bit float).
    """
    try:
        with io.BytesIO(audio_bytes) as bio:
            with wave.open(bio, "rb") as wf:
                num_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                sample_rate = wf.getframerate()
                num_frames = wf.getnframes()
                raw_frames = wf.readframes(num_frames)

        if sample_width == 2:  # 16-bit PCM
            data = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
        elif sample_width == 1:  # 8-bit PCM
            data = (np.frombuffer(raw_frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        elif sample_width == 3:  # 24-bit PCM
            # Convert 3-byte ints to 32-bit ints
            total_samples = len(raw_frames) // 3
            samples = []
            for i in range(total_samples):
                sub = raw_frames[i * 3 : (i + 1) * 3]
                val = int.from_bytes(sub, byteorder="little", signed=True)
                samples.append(val)
            data = np.array(samples, dtype=np.float32) / 8388608.0
        elif sample_width == 4:  # 32-bit float or int
            try:
                data = np.frombuffer(raw_frames, dtype=np.float32)
            except Exception:
                data = np.frombuffer(raw_frames, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            raise ValueError(f"Unsupported WAV sample width: {sample_width}")

        # Stereo to mono conversion
        if num_channels > 1:
            data = data.reshape(-1, num_channels)
            data = np.mean(data, axis=1)

        return data, sample_rate

    except Exception as e:
        # Fallback for headerless / raw PCM or corrupted container
        if len(audio_bytes) >= 2:
            num_samples = len(audio_bytes) // 2
            data = np.frombuffer(audio_bytes[:num_samples * 2], dtype=np.int16).astype(np.float32) / 32768.0
            return data, settings.SAMPLE_RATE
        raise ValueError(f"Failed to decode audio bytes: {str(e)}")


def write_wav_bytes(data: np.ndarray, sample_rate: int = 16000) -> bytes:
    """
    Encodes a normalized float32 numpy array into standard 16-bit PCM mono WAV bytes.
    """
    clipped = np.clip(data, -1.0, 1.0)
    int16_data = (clipped * 32767.0).astype(np.int16)

    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(int16_data.tobytes())
    return bio.getvalue()


def resample_audio(data: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    """
    Resamples audio data from orig_sr to target_sr using Fourier method or linear interpolation.
    """
    if orig_sr == target_sr or len(data) == 0:
        return data

    target_length = int(round(len(data) * target_sr / orig_sr))
    resampled = signal.resample(data, target_length)
    return resampled.astype(np.float32)


def apply_preemphasis(data: np.ndarray, alpha: float = 0.97) -> np.ndarray:
    """
    Applies pre-emphasis filter y[t] = x[t] - alpha * x[t-1]
    to amplify high frequencies and eliminate DC bias.
    """
    if len(data) <= 1:
        return data
    return np.append(data[0], data[1:] - alpha * data[:-1])


def voice_activity_detection(
    data: np.ndarray,
    sample_rate: int = 16000,
    frame_ms: int = 25,
    energy_threshold_factor: float = 0.08
) -> np.ndarray:
    """
    Energy-based Voice Activity Detection (VAD).
    Trims silent regions before and after active speech frames.
    """
    if len(data) == 0:
        return data

    frame_size = int(sample_rate * (frame_ms / 1000.0))
    if frame_size <= 0 or len(data) < frame_size:
        return data

    num_frames = len(data) // frame_size
    energies = []
    for i in range(num_frames):
        frame = data[i * frame_size : (i + 1) * frame_size]
        energy = np.sqrt(np.mean(frame ** 2) + 1e-12)
        energies.append(energy)

    energies = np.array(energies)
    max_energy = np.max(energies)
    threshold = max(max_energy * energy_threshold_factor, 0.005)

    active_indices = np.where(energies > threshold)[0]
    if len(active_indices) == 0:
        return data

    start_idx = max(0, (active_indices[0] - 1) * frame_size)
    end_idx = min(len(data), (active_indices[-1] + 2) * frame_size)
    return data[start_idx:end_idx]


def preprocess_audio(audio_bytes: bytes, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    """
    Full preprocessing pipeline:
    1. Read and decode WAV bytes
    2. Convert stereo to mono
    3. Resample to target_sr (16000 Hz)
    4. Apply VAD silence trimming
    5. Amplitude normalize to peak 1.0
    """
    raw_data, orig_sr = read_wav_bytes(audio_bytes)
    data = resample_audio(raw_data, orig_sr, target_sr)
    data = voice_activity_detection(data, target_sr)

    # Peak normalization
    peak = np.max(np.abs(data))
    if peak > 1e-6:
        data = data / peak

    return data.astype(np.float32), target_sr
