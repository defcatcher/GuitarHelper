"""
Metronome Engine
────────────────
Callback-based metronome using sounddevice OutputStream.
Timing is handled by the audio driver's high-priority thread
for zero-jitter click playback.
"""

from __future__ import annotations

import threading
import numpy as np
import sounddevice as sd

# ── Click Sound Synthesis ────────────────────────────────────────────────────

def _generate_click(
    freq: float = 1000.0,
    duration: float = 0.025,
    sample_rate: int = 44100,
    amplitude: float = 0.7,
) -> np.ndarray:
    """
    Synthesize a short click sound: sine wave with exponential decay envelope.
    """
    n_samples = int(sample_rate * duration)
    t = np.arange(n_samples, dtype=np.float64) / sample_rate
    # Sine tone
    tone = np.sin(2.0 * np.pi * freq * t)
    # Exponential decay envelope
    envelope = np.exp(-t * (1.0 / (duration * 0.3)))
    return (tone * envelope * amplitude).astype(np.float32)


class MetronomeEngine:
    """
    Precise, callback-driven metronome engine.

    Uses sounddevice.OutputStream: the callback is invoked by the
    audio driver's thread at regular intervals, ensuring sample-accurate
    beat placement with no drift or jitter.
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self._bpm: float = 120.0
        self._beats_per_bar: int = 4
        self._beat_value: int = 4  # denominator of time signature

        # Pre-generate click sounds
        self._accent_click = _generate_click(
            freq=1500.0, duration=0.03, sample_rate=sample_rate, amplitude=0.85
        )
        self._normal_click = _generate_click(
            freq=900.0, duration=0.025, sample_rate=sample_rate, amplitude=0.6
        )

        # Audio state — accessed from callback thread
        self._lock = threading.Lock()
        self._sample_counter: int = 0
        self._beat_counter: int = 0
        self._samples_per_beat: int = self._calc_samples_per_beat()
        
        # Cross-buffer playback state
        self._current_click: np.ndarray | None = None
        self._click_idx: int = 0
        self._volume: float = 1.0

        # The stream
        self._stream: sd.OutputStream | None = None
        self._playing = False

        # Beat callback for UI sync (called from audio thread — keep fast!)
        self._beat_callback: callable = None

    def _calc_samples_per_beat(self) -> int:
        """Calculate samples between beats based on current BPM."""
        return int(self.sample_rate * 60.0 / self._bpm)

    @property
    def bpm(self) -> float:
        return self._bpm

    @bpm.setter
    def bpm(self, value: float):
        value = max(30.0, min(300.0, value))
        with self._lock:
            self._bpm = value
            self._samples_per_beat = self._calc_samples_per_beat()
            
    @property
    def volume(self) -> float:
        return self._volume
        
    @volume.setter
    def volume(self, value: float):
        with self._lock:
            self._volume = max(0.0, min(1.0, value))

    @property
    def beats_per_bar(self) -> int:
        return self._beats_per_bar

    @beats_per_bar.setter
    def beats_per_bar(self, value: int):
        with self._lock:
            self._beats_per_bar = max(1, min(12, value))

    @property
    def beat_value(self) -> int:
        return self._beat_value

    @beat_value.setter
    def beat_value(self, value: int):
        with self._lock:
            self._beat_value = value

    @property
    def is_playing(self) -> bool:
        return self._playing

    def set_beat_callback(self, callback: callable):
        """
        Set a callback that fires on each beat.
        Signature: callback(beat_index: int, is_accent: bool)
        WARNING: Called from the audio thread — must be very fast.
        """
        self._beat_callback = callback

    def _audio_callback(
        self,
        outdata: np.ndarray,
        frames: int,
        time_info,
        status: sd.CallbackFlags,
    ):
        """
        PortAudio callback — fills the output buffer with click sounds
        at precisely the right sample positions.
        """
        if status:
            pass  # Could log xruns here

        outdata[:] = 0.0  # silence by default

        with self._lock:
            spb = self._samples_per_beat
            bpb = self._beats_per_bar
            vol = self._volume

        i = 0
        while i < frames:
            # 1. Output currently playing click natively across chunks
            if self._current_click is not None:
                remaining_click = len(self._current_click) - self._click_idx
                remaining_frames = frames - i
                n_copy = min(remaining_click, remaining_frames)
                outdata[i:i + n_copy, 0] += self._current_click[self._click_idx:self._click_idx + n_copy] * vol
                self._click_idx += n_copy
                
                if self._click_idx >= len(self._current_click):
                    self._current_click = None  # done playing
                
            # 2. Advance time until the next beat
            samples_until_beat = spb - self._sample_counter

            if samples_until_beat <= 0:
                # Beat fires NOW
                is_accent = (self._beat_counter % bpb) == 0
                self._current_click = self._accent_click if is_accent else self._normal_click
                self._click_idx = 0

                # Fire UI callback
                if self._beat_callback:
                    try:
                        self._beat_callback(self._beat_counter % bpb, is_accent)
                    except Exception:
                        pass

                self._beat_counter += 1
                self._sample_counter = 0
                
                # IMPORTANT: Loop continues to process the click logic on the 
                # next iteration, so we don't break / skip.
                continue
            else:
                # Advance to the next beat or end of buffer
                advance = min(samples_until_beat, frames - i)
                self._sample_counter += advance
                i += advance

    def start(self):
        """Start the metronome."""
        if self._playing:
            return

        self._sample_counter = 0
        self._beat_counter = 0

        try:
            self._stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=512,
                latency='low',
                callback=self._audio_callback,
            )
            self._stream.start()
            self._playing = True
        except Exception as e:
            print(f"Metronome start error: {e}")
            self._playing = False

    def stop(self):
        """Stop the metronome."""
        if not self._playing:
            return
        self._playing = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def toggle(self) -> bool:
        """Toggle play/stop. Returns new state."""
        if self._playing:
            self.stop()
        else:
            self.start()
        return self._playing
