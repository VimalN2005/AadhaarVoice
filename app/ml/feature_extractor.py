"""
Acoustic Feature Extraction Module.
Extracts:
- Short-Time Fourier Transform (STFT)
- Mel Spectrogram & 40-dimensional MFCCs + Deltas
- Fundamental Frequency (F0 / Pitch) via Autocorrelation
- Pitch Jitter & Amplitude Shimmer
- Spectral Centroid, Spectral Flatness, Spectral Roll-off
- Zero Crossing Rate (ZCR)
"""

from typing import Dict, Any, Tuple
import numpy as np
from scipy import fftpack


def hz_to_mel(hz: float) -> float:
    """Converts frequency in Hz to Mel scale."""
    return 2595.0 * np.log10(1.0 + hz / 700.0)


def mel_to_hz(mel: float) -> float:
    """Converts Mel scale value to frequency in Hz."""
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)


def get_mel_filterbank(
    n_filters: int = 40,
    n_fft: int = 512,
    sample_rate: int = 16000,
    low_freq: float = 0.0,
    high_freq: float = None
) -> np.ndarray:
    """
    Constructs triangular Mel-scale filterbank matrix.
    """
    if high_freq is None:
        high_freq = sample_rate / 2.0

    low_mel = hz_to_mel(low_freq)
    high_mel = hz_to_mel(high_freq)
    mel_points = np.linspace(low_mel, high_mel, n_filters + 2)
    hz_points = mel_to_hz(mel_points)
    bin_points = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

    filterbank = np.zeros((n_filters, n_fft // 2 + 1))
    for m in range(1, n_filters + 1):
        f_m_minus = bin_points[m - 1]
        f_m = bin_points[m]
        f_m_plus = bin_points[m + 1]

        for k in range(f_m_minus, f_m):
            if f_m != f_m_minus:
                filterbank[m - 1, k] = (k - f_m_minus) / (f_m - f_m_minus)
        for k in range(f_m, f_m_plus):
            if f_m_plus != f_m:
                filterbank[m - 1, k] = (f_m_plus - k) / (f_m_plus - f_m)

    return filterbank


def compute_stft(
    signal: np.ndarray,
    n_fft: int = 512,
    hop_length: int = 160,
    win_length: int = 400
) -> np.ndarray:
    """
    Computes Short-Time Fourier Transform with Hann window.
    Returns complex spectrogram of shape (n_frames, n_fft // 2 + 1).
    """
    if len(signal) < win_length:
        pad_width = win_length - len(signal)
        signal = np.pad(signal, (0, pad_width), mode="constant")

    window = np.hanning(win_length)
    n_frames = 1 + int((len(signal) - win_length) / hop_length)
    frames = np.zeros((n_frames, win_length))

    for i in range(n_frames):
        start = i * hop_length
        frames[i] = signal[start : start + win_length] * window

    # Zero pad to n_fft
    padded = np.pad(frames, ((0, 0), (0, n_fft - win_length)), mode="constant")
    stft = np.fft.rfft(padded, n=n_fft, axis=1)
    return stft


def compute_mfcc(
    signal: np.ndarray,
    sample_rate: int = 16000,
    n_mfcc: int = 40,
    n_filters: int = 40,
    n_fft: int = 512,
    hop_length: int = 160
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extracts Mel-Frequency Cepstral Coefficients (MFCCs) and Mel-Spectrogram.
    Returns:
        mfcc: shape (n_frames, n_mfcc)
        mel_spectrogram: shape (n_frames, n_filters)
    """
    stft = compute_stft(signal, n_fft=n_fft, hop_length=hop_length)
    power_spec = (np.abs(stft) ** 2) / n_fft

    filterbank = get_mel_filterbank(n_filters, n_fft, sample_rate)
    mel_spec = np.dot(power_spec, filterbank.T)
    mel_spec = np.where(mel_spec == 0, np.finfo(float).eps, mel_spec)
    log_mel_spec = np.log(mel_spec)

    # DCT Type-II
    mfcc = fftpack.dct(log_mel_spec, type=2, axis=1, norm="ortho")[:, :n_mfcc]

    # Cepstral liftering (standard parameter L=22): balances spectral formants against energy dominance
    lift = 1.0 + (22.0 / 2.0) * np.sin(np.pi * np.arange(n_mfcc) / 22.0)
    lift[0] *= 0.05  # Attenuate C0 overall energy term to prioritize vocal tract timbre
    mfcc = mfcc * lift

    return mfcc, mel_spec


def compute_deltas(features: np.ndarray, n: int = 2) -> np.ndarray:
    """
    Computes delta (velocity/acceleration) coefficients along time axis.
    """
    if len(features) < 2 * n + 1:
        return np.zeros_like(features)

    n_frames, n_features = features.shape
    deltas = np.zeros_like(features)
    denominator = 2 * sum(i ** 2 for i in range(1, n + 1))

    padded = np.pad(features, ((n, n), (0, 0)), mode="edge")
    for t in range(n_frames):
        delta = np.zeros(n_features)
        for i in range(1, n + 1):
            delta += i * (padded[t + n + i] - padded[t + n - i])
        deltas[t] = delta / denominator

    return deltas


def extract_pitch_f0(
    signal: np.ndarray,
    sample_rate: int = 16000,
    min_f0: float = 65.0,
    max_f0: float = 400.0
) -> Tuple[float, np.ndarray, float, float]:
    """
    Estimates fundamental frequency (F0) using normalized autocorrelation.
    Also computes pitch Jitter (relative variation) and Shimmer (amplitude variation).
    Returns:
        median_f0: float (Hz)
        f0_contour: array of pitch values across frames
        jitter: float (0.0 to 1.0)
        shimmer: float (0.0 to 1.0)
    """
    if len(signal) < sample_rate * 0.1:  # Need at least 100ms
        return 120.0, np.array([120.0]), 0.01, 0.02

    frame_size = int(sample_rate * 0.04)  # 40ms frame
    hop = int(sample_rate * 0.02)  # 20ms hop
    min_lag = int(sample_rate / max_f0)
    max_lag = int(sample_rate / min_f0)

    f0_values = []
    amplitudes = []

    for start in range(0, len(signal) - frame_size, hop):
        frame = signal[start : start + frame_size]
        if np.std(frame) < 0.01:
            continue  # Silence / unvoiced

        # Autocorrelation
        corr = np.correlate(frame, frame, mode="full")
        corr = corr[len(corr) // 2 :]

        if max_lag < len(corr):
            lag_region = corr[min_lag:max_lag]
            if len(lag_region) > 0 and np.max(lag_region) > 0.3 * corr[0]:
                peak_lag = min_lag + np.argmax(lag_region)
                f0 = sample_rate / peak_lag
                f0_values.append(f0)
                amplitudes.append(np.max(np.abs(frame)))

    if len(f0_values) == 0:
        return 130.0, np.array([130.0]), 0.01, 0.02

    f0_arr = np.array(f0_values)
    median_f0 = float(np.median(f0_arr))

    # Jitter: relative average perturbation of successive fundamental periods
    if len(f0_arr) > 2:
        periods = 1.0 / f0_arr
        period_diffs = np.abs(np.diff(periods))
        jitter = float(np.mean(period_diffs) / (np.mean(periods) + 1e-9))
    else:
        jitter = 0.01

    # Shimmer: relative amplitude perturbation across frames
    if len(amplitudes) > 2:
        amp_arr = np.array(amplitudes)
        amp_diffs = np.abs(np.diff(amp_arr))
        shimmer = float(np.mean(amp_diffs) / (np.mean(amp_arr) + 1e-9))
    else:
        shimmer = 0.02

    return median_f0, f0_arr, float(np.clip(jitter, 0.0, 1.0)), float(np.clip(shimmer, 0.0, 1.0))


def compute_spectral_features(
    signal: np.ndarray,
    sample_rate: int = 16000,
    n_fft: int = 512,
    hop_length: int = 160
) -> Dict[str, float]:
    """
    Computes spectral centroid, spectral flatness, spectral roll-off, and zero crossing rate.
    """
    stft = compute_stft(signal, n_fft=n_fft, hop_length=hop_length)
    magnitude = np.abs(stft)  # (n_frames, n_freq_bins)
    freqs = np.linspace(0, sample_rate / 2.0, n_fft // 2 + 1)

    # Spectral Centroid: weighted average of frequencies
    mag_sum = np.sum(magnitude, axis=1, keepdims=True) + 1e-12
    centroid_per_frame = np.sum(magnitude * freqs, axis=1) / mag_sum.squeeze()
    mean_centroid = float(np.mean(centroid_per_frame))

    # Spectral Flatness: geometric mean / arithmetic mean
    # Adding small epsilon to avoid zero in log
    mag_nonzero = magnitude + 1e-9
    geo_mean = np.exp(np.mean(np.log(mag_nonzero), axis=1))
    arith_mean = np.mean(mag_nonzero, axis=1)
    flatness_per_frame = geo_mean / (arith_mean + 1e-12)
    mean_flatness = float(np.mean(flatness_per_frame))

    # Spectral Roll-off: frequency below which 85% of total power lies
    power = magnitude ** 2
    total_power = np.sum(power, axis=1)
    cumulative_power = np.cumsum(power, axis=1)
    roll_off_freqs = []
    for i in range(len(total_power)):
        thresh = 0.85 * total_power[i]
        idx = np.where(cumulative_power[i] >= thresh)[0]
        roll_off_freqs.append(freqs[idx[0]] if len(idx) > 0 else freqs[-1])
    mean_rolloff = float(np.mean(roll_off_freqs)) if roll_off_freqs else 3000.0

    # Zero Crossing Rate (ZCR)
    zero_crossings = np.sum(np.abs(np.diff(np.signbit(signal).astype(int))))
    zcr = float(zero_crossings / (len(signal) + 1e-9))

    return {
        "spectral_centroid_hz": round(mean_centroid, 2),
        "spectral_flatness": round(mean_flatness, 4),
        "spectral_rolloff_hz": round(mean_rolloff, 2),
        "zero_crossing_rate": round(zcr, 4),
    }


def extract_all_features(signal: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
    """
    Extracts all primary acoustic features into a unified dictionary.
    """
    mfcc, mel_spec = compute_mfcc(signal, sample_rate)
    delta_mfcc = compute_deltas(mfcc)
    f0, f0_contour, jitter, shimmer = extract_pitch_f0(signal, sample_rate)
    spectral = compute_spectral_features(signal, sample_rate)

    # Statistical pooling of MFCCs (mean and std across time)
    mfcc_mean = np.mean(mfcc, axis=0)
    mfcc_std = np.std(mfcc, axis=0)
    delta_mean = np.mean(delta_mfcc, axis=0)
    delta_std = np.std(delta_mfcc, axis=0)

    return {
        "mfcc_mean": mfcc_mean,
        "mfcc_std": mfcc_std,
        "delta_mean": delta_mean,
        "delta_std": delta_std,
        "pitch_f0_hz": round(f0, 2),
        "pitch_jitter": jitter,
        "amplitude_shimmer": shimmer,
        **spectral,
        "duration_seconds": round(len(signal) / sample_rate, 2),
    }
