"""
Fretboard Panel — Center Panel Assembly
────────────────────────────────────────
Combines the fretboard widget, tuning selector carousel,
and tuner controls (mic selection, tuner toggle, tuner gauge).
"""

from __future__ import annotations

import threading
import numpy as np
import sounddevice as sd

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject

from ui.theme import Colors, FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG, CenteredComboBox
from ui.fretboard_widget import FretboardWidget
from ui.tuner_widget import TunerWidget
from core.music_theory import TUNING_NAMES, get_tuning_freqs
from core.pitch_detector import detect_pitch, freq_to_note, closest_string


class _TunerWorkerSignals(QObject):
    """Signals emitted by the tuner worker (thread-safe bridge)."""
    pitch_detected = pyqtSignal(float, str, int, float, float, int, bool)
    # freq, note_name, octave, cents, target_freq, string_idx, in_tune
    no_pitch = pyqtSignal()


class _Divider(QFrame):
    """Horizontal divider line."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet(f"color: {Colors.BORDER}; margin: 4px 0;")
        self.setFixedHeight(1)


class FretboardPanel(QWidget):
    """
    Center panel containing:
    - Top: Tuner controls (toggle, mic, gauge)
    - Middle: Interactive fretboard
    - Bottom: Tuning selector carousel
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._tuning_index: int = 0
        self._tuner_active: bool = False
        self._audio_stream: sd.InputStream | None = None
        self._tuner_signals = _TunerWorkerSignals()

        self._setup_ui()
        self._connect_signals()
        self._populate_mic_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(10)

        # ── Top: Tuner Controls ──────────────────────────────────────────
        tuner_row = QHBoxLayout()
        tuner_row.setSpacing(12)
        tuner_row.addStretch()

        # Mic selector
        mic_label = QLabel("Mic:")
        mic_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {FONT_SIZE_SM}px;")
        tuner_row.addWidget(mic_label)

        self._mic_combo = CenteredComboBox()
        self._mic_combo.setMinimumWidth(160)
        self._mic_combo.setFixedHeight(32)
        tuner_row.addWidget(self._mic_combo)

        # Tuner toggle
        self._tuner_btn = QPushButton("Tuner")
        self._tuner_btn.setCheckable(True)
        self._tuner_btn.setFixedHeight(36)
        self._tuner_btn.setMinimumWidth(100)
        self._tuner_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_TERTIARY};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 8px;
                font-size: {FONT_SIZE_MD}px;
                font-weight: bold;
                padding: 4px 16px;
            }}
            QPushButton:checked {{
                background-color: {Colors.ACCENT};
                border-color: {Colors.ACCENT};
                color: white;
            }}
            QPushButton:hover {{
                border-color: {Colors.ACCENT_HOVER};
            }}
        """)
        tuner_row.addWidget(self._tuner_btn)
        tuner_row.addStretch()
        layout.addLayout(tuner_row)

        # Tuner gauge (hidden by default)
        self._tuner_widget = TunerWidget()
        self._tuner_widget.setVisible(False)
        layout.addWidget(self._tuner_widget)

        layout.addWidget(_Divider())

        # ── Middle: Fretboard ────────────────────────────────────────────
        self._fretboard = FretboardWidget()
        layout.addWidget(self._fretboard, stretch=1)

        layout.addWidget(_Divider())

        # ── Bottom: Tuning Carousel ──────────────────────────────────────
        carousel_row = QHBoxLayout()
        carousel_row.setSpacing(12)
        carousel_row.addStretch()

        self._prev_btn = QPushButton("<")
        self._prev_btn.setFixedSize(36, 36)
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: bold;
                color: {Colors.TEXT_MUTED};
            }}
            QPushButton:hover {{
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        carousel_row.addWidget(self._prev_btn)

        self._tuning_label = QLabel(TUNING_NAMES[0])
        self._tuning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tuning_label.setMinimumWidth(200)
        self._tuning_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_MD}px;
            font-weight: bold;
            color: {Colors.TEXT_PRIMARY};
            background: {Colors.BG_TERTIARY};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: 8px;
            padding: 8px 20px;
        """)
        carousel_row.addWidget(self._tuning_label)

        self._next_btn = QPushButton(">")
        self._next_btn.setFixedSize(36, 36)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.setStyleSheet(self._prev_btn.styleSheet())
        carousel_row.addWidget(self._next_btn)

        carousel_row.addStretch()
        layout.addLayout(carousel_row)

    def _connect_signals(self):
        self._prev_btn.clicked.connect(self._prev_tuning)
        self._next_btn.clicked.connect(self._next_tuning)
        self._tuner_btn.toggled.connect(self._toggle_tuner)
        self._tuner_signals.pitch_detected.connect(self._on_pitch_detected)
        self._tuner_signals.no_pitch.connect(self._on_no_pitch)

    def _populate_mic_list(self):
        """Populate mic dropdown with available input devices."""
        self._mic_combo.clear()
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    name = dev['name']
                    self._mic_combo.addItem(f"{name}", userData=i)
        except Exception as e:
            self._mic_combo.addItem(f"Error: {e}")

    # ── Tuning Carousel ──────────────────────────────────────────────────

    def _prev_tuning(self):
        self._tuning_index = (self._tuning_index - 1) % len(TUNING_NAMES)
        self._apply_tuning()

    def _next_tuning(self):
        self._tuning_index = (self._tuning_index + 1) % len(TUNING_NAMES)
        self._apply_tuning()

    def _apply_tuning(self):
        name = TUNING_NAMES[self._tuning_index]
        self._tuning_label.setText(name)
        self._fretboard.set_tuning(name)

    # ── Tuner Logic ──────────────────────────────────────────────────────

    def _toggle_tuner(self, active: bool):
        self._tuner_active = active
        self._tuner_widget.setVisible(active)

        if active:
            self._start_tuner()
            self._tuner_widget.clear()
        else:
            self._stop_tuner()
            self._fretboard.set_tuner_state(False)
            self._tuner_widget.clear()

    def _start_tuner(self):
        """Start listening to the microphone for pitch detection."""
        device_idx = self._mic_combo.currentData()
        if device_idx is None:
            return

        sample_rate = 44100
        block_size = 2048  # Good balance for YIN accuracy vs latency

        try:
            self._audio_stream = sd.InputStream(
                device=device_idx,
                samplerate=sample_rate,
                channels=1,
                dtype='float32',
                blocksize=block_size,
                latency='low',
                callback=self._audio_callback,
            )
            self._audio_stream.start()
        except Exception as e:
            print(f"Tuner start error: {e}")
            self._tuner_btn.setChecked(False)

    def _stop_tuner(self):
        """Stop the audio stream."""
        if self._audio_stream:
            try:
                self._audio_stream.stop()
                self._audio_stream.close()
            except Exception:
                pass
            self._audio_stream = None

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Audio callback — runs on the PortAudio thread.
        Performs pitch detection and emits results via signal.
        """
        if status:
            return

        signal = indata[:, 0]  # mono
        freq = detect_pitch(signal, sample_rate=44100)

        if freq is None:
            self._tuner_signals.no_pitch.emit()
            return

        note_name, octave, cents = freq_to_note(freq)

        # Find closest string
        tuning_name = TUNING_NAMES[self._tuning_index]
        tuning_freqs = get_tuning_freqs(tuning_name)
        s_idx, s_note, target_freq, s_cents = closest_string(freq, tuning_freqs)

        in_tune = bool(abs(s_cents) < 5)

        self._tuner_signals.pitch_detected.emit(
            float(freq), str(note_name), int(octave), float(s_cents), float(target_freq), int(s_idx), in_tune
        )

    def _on_pitch_detected(
        self, freq: float, note: str, octave: int,
        cents: float, target_freq: float, string_idx: int, in_tune: bool
    ):
        """Handle pitch detection result on the main thread."""
        self._tuner_widget.update_tuner(note, freq, cents, "")
        self._fretboard.set_tuner_state(True, string_idx, cents, in_tune)

    def _on_no_pitch(self):
        """Handle no pitch detected."""
        pass  # Keep last display, don't flicker

    # ── Public API ───────────────────────────────────────────────────────

    def set_highlighted_key(self, key: str | None, mode: str = "Major", scale_notes: list[str] | None = None):
        """Pass through to fretboard."""
        self._fretboard.set_highlighted_key(key, mode, scale_notes)

    # ── Cleanup ──────────────────────────────────────────────────────────

    def cleanup(self):
        """Stop audio streams on shutdown."""
        self._stop_tuner()
