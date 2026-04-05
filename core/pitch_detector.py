from __future__ import annotations

import numpy as np
from collections import deque

from core.music_theory import CHROMATIC, A4_FREQ, note_index, note_from_index


# ── YIN Algorithm ────────────────────────────────────────────────────────────

def _difference_function(signal: np.ndarray, max_tau: int) -> np.ndarray:
    """
    Compute the YIN difference function d(tau):
        d(tau) = sum_{j=0}^{n-tau-1} (x[j] - x[j+tau])^2

    Uses FFT-based autocorrelation plus cumulative energy sums.
    """
    n = len(signal)
    if n == 0 or max_tau <= 0:
        return np.array([], dtype=np.float64)

    x = signal.astype(np.float64, copy=False)

    fft_size = 1
    while fft_size < n + max_tau:
        fft_size <<= 1

    x2 = x * x
    cum = np.concatenate(([0.0], np.cumsum(x2)))

    fft_signal = np.fft.rfft(x, n=fft_size)
    acf = np.fft.irfft(fft_signal * np.conj(fft_signal), n=fft_size)[:max_tau]

    taus = np.arange(max_tau)

    # sum_{j=0}^{n-tau-1} x[j]^2
    e1 = cum[n - taus]

    # sum_{j=0}^{n-tau-1} x[j+tau]^2
    e2 = cum[n] - cum[taus]

    d = e1 + e2 - 2.0 * acf
    d[0] = 0.0

    # Numerical safety
    d = np.maximum(d, 0.0)
    return d


def _cumulative_mean_normalized_difference(d: np.ndarray) -> np.ndarray:
    """
    Compute the cumulative mean normalized difference function d'(tau).
    d'(0) = 1
    d'(tau) = d(tau) / ((1/tau) * sum_{j=1..tau} d(j))
    """
    if len(d) == 0:
        return np.array([], dtype=np.float64)

    d_prime = np.ones_like(d, dtype=np.float64)
    if len(d) < 2:
        return d_prime

    running_sum = np.cumsum(d, dtype=np.float64)

    taus = np.arange(len(d), dtype=np.float64)
    denom = running_sum[1:] / np.maximum(taus[1:], 1.0)

    safe_mask = denom > 1e-12
    d_prime[1:] = 1.0
    d_prime[1:][safe_mask] = d[1:][safe_mask] / denom[safe_mask]

    d_prime[0] = 1.0
    return d_prime


def _absolute_threshold(
    d_prime: np.ndarray,
    start_tau: int,
    threshold: float = 0.15,
) -> int:
    """
    Find the first tau >= start_tau where d'(tau) dips below threshold,
    then return the tau of the subsequent local minimum.

    If no tau crosses the threshold, fallback to the best minimum
    if it is reasonably low.
    """
    if len(d_prime) == 0 or start_tau >= len(d_prime):
        return -1

    best_tau = -1
    best_val = float("inf")

    tau = max(2, start_tau)
    while tau < len(d_prime):
        val = d_prime[tau]

        if val < best_val:
            best_val = val
            best_tau = tau

        if val < threshold:
            while tau + 1 < len(d_prime) and d_prime[tau + 1] < d_prime[tau]:
                tau += 1
            return tau

        tau += 1

    if best_tau != -1 and best_val < 0.35:
        while best_tau + 1 < len(d_prime) and d_prime[best_tau + 1] < d_prime[best_tau]:
            best_tau += 1
        return best_tau

    return -1


def _parabolic_interpolation(d: np.ndarray, tau: int) -> float:
    """Refine tau estimate using parabolic interpolation."""
    if tau <= 0 or tau >= len(d) - 1:
        return float(tau)

    s0 = d[tau - 1]
    s1 = d[tau]
    s2 = d[tau + 1]

    denom = 2.0 * (2.0 * s1 - s2 - s0)
    if abs(denom) < 1e-12:
        return float(tau)

    return tau + (s0 - s2) / denom


def detect_pitch(
    signal: np.ndarray,
    sample_rate: int = 44100,
    threshold: float = 0.15,
    min_freq: float = 70.0,
    max_freq: float = 400.0,
) -> float | None:
    """
    Detect the fundamental frequency of a monophonic audio signal.

    Parameters
    ----------
    signal : np.ndarray
        1D audio signal (mono, float32/float64).
    sample_rate : int
        Sampling rate in Hz.
    threshold : float
        YIN threshold.
    min_freq : float
        Minimum detectable frequency in Hz.
    max_freq : float
        Maximum detectable frequency in Hz.

    Returns
    -------
    float | None
        Detected frequency in Hz, or None if no clear pitch.
    """
    signal = np.asarray(signal, dtype=np.float64)
    if signal.ndim != 1:
        signal = signal.reshape(-1)

    if len(signal) < 2:
        return None

    # Remove DC
    signal = signal - np.mean(signal)

    # RMS gate
    rms = np.sqrt(np.mean(signal ** 2))
    if rms < 0.002:
        return None

    # Tau bounds from frequency bounds
    max_tau = min(int(sample_rate / min_freq), len(signal) // 2)
    min_tau = max(2, int(sample_rate / max_freq))

    if max_tau <= min_tau:
        return None

    d = _difference_function(signal, max_tau)
    if len(d) == 0:
        return None

    d_prime = _cumulative_mean_normalized_difference(d)
    tau = _absolute_threshold(d_prime, min_tau, threshold)
    if tau == -1:
        return None

    refined_tau = _parabolic_interpolation(d, tau)
    if refined_tau <= 0:
        return None

    freq = sample_rate / refined_tau
    if not np.isfinite(freq):
        return None

    if freq < min_freq or freq > max_freq:
        return None

    return float(freq)


# ── Optional smoothing for realtime tuner ───────────────────────────────────

_pitch_history: deque[float] = deque(maxlen=5)
_smoothed_freq: float | None = None


def smooth_pitch(freq: float | None, alpha: float = 0.22) -> float | None:
    """
    Smooth pitch between frames for steadier tuner needle.
    Uses median + exponential smoothing.
    """
    global _smoothed_freq

    if freq is None:
        return _smoothed_freq

    _pitch_history.append(float(freq))
    median_freq = float(np.median(np.array(_pitch_history, dtype=np.float64)))

    if _smoothed_freq is None:
        _smoothed_freq = median_freq
    else:
        _smoothed_freq = (1.0 - alpha) * _smoothed_freq + alpha * median_freq

    return _smoothed_freq


def reset_pitch_smoothing() -> None:
    """Reset smoothing state."""
    global _smoothed_freq
    _pitch_history.clear()
    _smoothed_freq = None


# ── Frequency → Note Mapping ─────────────────────────────────────────────────

def freq_to_note(freq: float) -> tuple[str, int, float]:
    """
    Convert a frequency to the closest note.

    Returns
    -------
    (note_name, octave, cents_offset)
        cents_offset: positive = sharp, negative = flat.
        Range: approximately -50 to +50 around nearest note.
    """
    if freq <= 0:
        return ("A", 4, 0.0)

    semitones = 12.0 * np.log2(freq / A4_FREQ)
    rounded = round(semitones)
    cents = (semitones - rounded) * 100.0

    midi_a4 = 69
    midi = midi_a4 + rounded
    octave = (midi // 12) - 1

    midi_chromatic = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    note_idx = midi % 12
    note_name = midi_chromatic[note_idx]

    return (note_name, octave, float(cents))


def closest_string(
    freq: float,
    tuning_freqs: list[tuple[str, int, float]],
) -> tuple[int, str, float, float]:
    """
    Find the closest string to a detected frequency.

    Parameters
    ----------
    freq : float
        Detected frequency in Hz.
    tuning_freqs : list of (note_name, octave, reference_freq)

    Returns
    -------
    (string_index, note_name, target_freq, cents_offset)
        string_index: 0 = lowest string (6th), 5 = highest (1st).
    """
    best_idx = 0
    best_cents = float("inf")

    for i, (note, octave, ref_freq) in enumerate(tuning_freqs):
        if ref_freq <= 0:
            continue

        cents = 1200.0 * np.log2(freq / ref_freq)
        if abs(cents) < abs(best_cents):
            best_cents = float(cents)
            best_idx = i

    note, octave, ref_freq = tuning_freqs[best_idx]
    return (best_idx, note, ref_freq, best_cents)