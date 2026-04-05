"""
Metronome Panel — Right Panel
─────────────────────────────
Time signature, BPM, play/stop, and visual beat indicator.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSlider, QSpinBox,
    QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtGui import QFont

from ui.theme import Colors, FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_XL, CenteredComboBox
from core.metronome_engine import MetronomeEngine


class MetronomeSignals(QObject):
    beat = pyqtSignal(int, bool)


class _SectionHeader(QLabel):
    """Styled section header label."""
    def __init__(self, text: str, parent=None):
        # Convert to title case for elegance
        super().__init__(text.title(), parent)
        self.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: {FONT_SIZE_SM - 2}px;
            font-weight: normal;
            padding: 4px 0;
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)


class _BeatDot(QWidget):
    """Single beat indicator dot."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self._active = False
        self._accent = False

    def set_state(self, active: bool, accent: bool = False):
        self._active = active
        self._accent = accent
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QBrush, QColor
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._active:
            if self._accent:
                color = QColor(Colors.ACCENT)
            else:
                color = QColor(Colors.TEXT_SECONDARY)
        else:
            color = QColor(Colors.BG_TERTIARY)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color))
        p.drawEllipse(4, 4, 16, 16)
        p.end()


class _Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet(f"color: {Colors.BORDER}; margin: 4px 0;")
        self.setFixedHeight(1)


class MetronomePanel(QWidget):
    """
    Metronome panel with:
    - Time signature selector
    - BPM slider + direct input
    - Play/Stop button
    - Visual beat indicator
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        self.setMaximumWidth(320)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self._signals = MetronomeSignals()
        self._signals.beat.connect(self._update_beat_display)

        self._engine = MetronomeEngine()
        self._engine.set_beat_callback(self._on_beat)

        self._beat_dots: list[_BeatDot] = []
        self._current_beat: int = -1

        # Timer to reset beat dots after a short delay
        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.setInterval(100)
        self._reset_timer.timeout.connect(self._reset_dots)

        self._setup_ui()
        self._connect_signals()
        self._rebuild_beat_dots()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 16, 16)
        layout.setSpacing(12)

        # ── Vertical Centering Top Stretch ───────────────────────────────
        layout.addStretch()

        # ── Time Signature ───────────────────────────────────────────────
        layout.addWidget(_SectionHeader("TIME SIGNATURE"), alignment=Qt.AlignmentFlag.AlignCenter)

        ts_row = QHBoxLayout()
        ts_row.setSpacing(8)
        ts_row.addStretch()

        self._beats_combo = CenteredComboBox()
        for i in range(2, 8):
            self._beats_combo.addItem(str(i), userData=i)
        self._beats_combo.setCurrentIndex(2)  # default 4
        self._beats_combo.setFixedHeight(36)
        self._beats_combo.setMinimumWidth(65)
        ts_row.addWidget(self._beats_combo)

        slash_label = QLabel("/")
        slash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slash_label.setStyleSheet(f"font-size: {FONT_SIZE_XL}px; color: {Colors.TEXT_SECONDARY};")
        ts_row.addWidget(slash_label)

        self._value_combo = CenteredComboBox()
        for val in [4, 8]:
            self._value_combo.addItem(str(val), userData=val)
        self._value_combo.setFixedHeight(36)
        self._value_combo.setMinimumWidth(65)
        ts_row.addWidget(self._value_combo)

        ts_row.addStretch()
        layout.addLayout(ts_row)
        layout.addWidget(_Divider())

        # ── Beat Indicator ───────────────────────────────────────────────
        layout.addWidget(_SectionHeader("BEAT"), alignment=Qt.AlignmentFlag.AlignCenter)

        self._beat_row_layout = QHBoxLayout()
        self._beat_row_layout.setSpacing(8)
        self._beat_row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        beat_container = QWidget()
        beat_container.setLayout(self._beat_row_layout)
        beat_container.setMinimumHeight(40)
        layout.addWidget(beat_container)

        layout.addWidget(_Divider())

        # ── BPM ──────────────────────────────────────────────────────────
        layout.addWidget(_SectionHeader("TEMPO"), alignment=Qt.AlignmentFlag.AlignCenter)

        # Large BPM display
        self._bpm_display = QLabel("120")
        self._bpm_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._bpm_display.setStyleSheet(f"""
            font-size: 48px;
            font-weight: bold;
            color: {Colors.TEXT_PRIMARY};
            padding: 8px;
        """)
        layout.addWidget(self._bpm_display)

        # Slider
        self._bpm_slider = QSlider(Qt.Orientation.Horizontal)
        self._bpm_slider.setRange(30, 300)
        self._bpm_slider.setValue(120)
        self._bpm_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        layout.addWidget(self._bpm_slider)

        # BPM range labels
        range_row = QHBoxLayout()
        slow_label = QLabel("30")
        slow_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {FONT_SIZE_SM}px;")
        fast_label = QLabel("300")
        fast_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {FONT_SIZE_SM}px;")
        range_row.addWidget(slow_label)
        range_row.addStretch()
        range_row.addWidget(fast_label)
        layout.addLayout(range_row)

        # Direct BPM input
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        input_row.addStretch()

        bpm_input_label = QLabel("BPM:")
        bpm_input_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {FONT_SIZE_SM}px;")
        input_row.addWidget(bpm_input_label)

        self._bpm_minus = QPushButton("-")
        self._bpm_minus.setFixedSize(34, 34)
        self._bpm_minus.setCursor(Qt.CursorShape.PointingHandCursor)
        self._bpm_minus.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_TERTIARY};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                padding: 0;
            }}
            QPushButton:hover {{
                border-color: {Colors.ACCENT};
            }}
        """)
        input_row.addWidget(self._bpm_minus)

        self._bpm_spin = QSpinBox()
        self._bpm_spin.setRange(30, 300)
        self._bpm_spin.setValue(120)
        self._bpm_spin.setFixedHeight(34)
        self._bpm_spin.setMinimumWidth(80)
        self._bpm_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self._bpm_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_row.addWidget(self._bpm_spin)

        self._bpm_plus = QPushButton("+")
        self._bpm_plus.setFixedSize(34, 34)
        self._bpm_plus.setCursor(Qt.CursorShape.PointingHandCursor)
        self._bpm_plus.setStyleSheet(self._bpm_minus.styleSheet())
        input_row.addWidget(self._bpm_plus)

        input_row.addStretch()
        layout.addLayout(input_row)

        layout.addWidget(_Divider())
        
        # ── Volume ───────────────────────────────────────────────────────
        layout.addWidget(_SectionHeader("VOLUME"), alignment=Qt.AlignmentFlag.AlignCenter)
        vol_row = QHBoxLayout()
        
        vol_label = QLabel("Min")
        vol_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {FONT_SIZE_SM}px;")
        vol_row.addWidget(vol_label)
        
        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(100)
        self._vol_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        vol_row.addWidget(self._vol_slider)
        
        vol_max_label = QLabel("Max")
        vol_max_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {FONT_SIZE_SM}px;")
        vol_row.addWidget(vol_max_label)
        
        layout.addLayout(vol_row)
        layout.addWidget(_Divider())

        # ── Play/Stop Button ─────────────────────────────────────────────
        self._play_btn = QPushButton("Start")
        self._play_btn.setFixedHeight(48)
        self._play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.TEXT_PRIMARY};
                color: {Colors.BG_PRIMARY};
                border: none;
                border-radius: 12px;
                font-size: {FONT_SIZE_LG}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.TEXT_SECONDARY};
            }}
            QPushButton:pressed {{
                background-color: {Colors.TEXT_MUTED};
                color: {Colors.BG_PRIMARY};
            }}
        """)
        layout.addWidget(self._play_btn)

        layout.addStretch()

    def _connect_signals(self):
        self._bpm_slider.valueChanged.connect(self._on_slider_changed)
        self._bpm_spin.valueChanged.connect(self._on_spin_changed)
        self._bpm_minus.clicked.connect(lambda: self._bpm_spin.setValue(self._bpm_spin.value() - 1))
        self._bpm_plus.clicked.connect(lambda: self._bpm_spin.setValue(self._bpm_spin.value() + 1))

        self._vol_slider.valueChanged.connect(self._on_vol_changed)
        self._play_btn.clicked.connect(self._toggle_play)
        self._beats_combo.currentIndexChanged.connect(self._on_time_sig_changed)
        self._value_combo.currentIndexChanged.connect(self._on_time_sig_changed)

    # ── BPM Sync ─────────────────────────────────────────────────────────

    def _on_slider_changed(self, value: int):
        self._bpm_spin.blockSignals(True)
        self._bpm_spin.setValue(value)
        self._bpm_spin.blockSignals(False)
        self._bpm_display.setText(str(value))
        self._engine.bpm = float(value)

    def _on_spin_changed(self, value: int):
        self._bpm_slider.blockSignals(True)
        self._bpm_slider.setValue(value)
        self._bpm_slider.blockSignals(False)
        self._bpm_display.setText(str(value))
        self._engine.bpm = float(value)

    def _on_vol_changed(self, value: int):
        self._engine.volume = float(value) / 100.0

    # ── Time Signature ───────────────────────────────────────────────────

    def _on_time_sig_changed(self):
        beats = self._beats_combo.currentData()
        value = self._value_combo.currentData()
        if beats and value:
            self._engine.beats_per_bar = beats
            self._engine.beat_value = value
            self._rebuild_beat_dots()

    def _rebuild_beat_dots(self):
        """Rebuild the visual beat indicator dots."""
        # Remove existing dots
        while self._beat_row_layout.count():
            item = self._beat_row_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._beat_dots.clear()

        beats = self._engine.beats_per_bar
        for i in range(beats):
            dot = _BeatDot()
            self._beat_dots.append(dot)
            self._beat_row_layout.addWidget(dot)

    # ── Play/Stop ────────────────────────────────────────────────────────

    def _toggle_play(self):
        playing = self._engine.toggle()
        if playing:
            self._play_btn.setText("Stop")
            self._play_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_TERTIARY};
                    color: {Colors.ACCENT};
                    border: none;
                    border-radius: 12px;
                    font-size: {FONT_SIZE_LG}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {Colors.SECONDARY_HOVER};
                    color: {Colors.BG_PRIMARY};
                }}
                QPushButton:pressed {{
                    background-color: {Colors.BORDER_LIGHT};
                    color: {Colors.BG_PRIMARY};
                }}
            """)
        else:
            self._play_btn.setText("Start")
            self._play_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.TEXT_PRIMARY};
                    color: {Colors.BG_PRIMARY};
                    border: none;
                    border-radius: 12px;
                    font-size: {FONT_SIZE_LG}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {Colors.TEXT_SECONDARY};
                }}
                QPushButton:pressed {{
                    background-color: {Colors.TEXT_MUTED};
                    color: {Colors.BG_PRIMARY};
                }}
            """)
            self._reset_dots()

    # ── Beat Callback (from audio thread) ────────────────────────────────

    def _on_beat(self, beat_index: int, is_accent: bool):
        """
        Called from the audio thread.
        Use signal to safely update UI.
        """
        self._signals.beat.emit(beat_index, is_accent)

    @pyqtSlot(int, bool)
    def _update_beat_display(self, beat_index: int, is_accent: bool):
        """Update beat dots on the main thread."""
        for i, dot in enumerate(self._beat_dots):
            dot.set_state(i == beat_index, is_accent and i == beat_index)
        self._current_beat = beat_index

        # Reset after short delay
        self._reset_timer.start()

    def _reset_dots(self):
        """Dim all dots."""
        for dot in self._beat_dots:
            dot.set_state(False)

    # ── Cleanup ──────────────────────────────────────────────────────────

    def cleanup(self):
        """Stop engine on shutdown."""
        self._engine.stop()
