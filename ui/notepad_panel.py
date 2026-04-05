"""
Notepad Panel — Smart Lyrics & Chord Notepad
─────────────────────────────────────────────
Left panel with key selector, diatonic chord suggestions,
capo transposition, and a text editor for lyrics/chords.
"""

from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QPlainTextEdit, QPushButton,
    QFrame, QSizePolicy, QGridLayout, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.theme import Colors, FONT_FAMILY_MONO, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG, CenteredComboBox
from core.user_paths import lyrics_library_dir
from core.music_theory import (
    CHROMATIC,
    get_diatonic_chords,
    capo_display_chords,
    DiatonicChord,
    get_scale_notes,
    transpose_chord_name,
)


class _SectionHeader(QLabel):
    """Styled section header label."""
    def __init__(self, text: str, parent=None):
        super().__init__(text.title(), parent)
        self.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: {FONT_SIZE_SM - 2}px;
            font-weight: normal;
            padding: 4px 0;
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)


class _ChordButton(QPushButton):
    """Styled chord suggestion button."""
    def __init__(self, chord: DiatonicChord, parent=None):
        super().__init__(parent)
        self._chord = chord
        self._update_display(chord)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(52)

    def _update_display(self, chord: DiatonicChord):
        self._chord = chord
        self.setText(chord.name)
        self.setToolTip(f"{chord.roman} — {chord.name}")

        # Color by quality (minimalist iOS style)
        if chord.quality == '':
            border = Colors.ACCENT
            text_color = Colors.TEXT_PRIMARY
        elif chord.quality == 'm':
            border = Colors.TEXT_SECONDARY
            text_color = Colors.TEXT_PRIMARY
        else:  # dim
            border = Colors.BORDER_LIGHT
            text_color = Colors.TEXT_MUTED

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_TERTIARY};
                color: {text_color};
                border: 1px solid {border};
                border-radius: 12px;
                font-size: {FONT_SIZE_MD}px;
                font-weight: bold;
                padding: 4px;
            }}
            QPushButton:hover {{
                border-color: {Colors.ACCENT_HOVER};
                color: {Colors.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.BORDER_LIGHT};
            }}
        """)


class _Divider(QFrame):
    """Horizontal divider line."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet(f"color: {Colors.BORDER}; margin: 4px 0;")
        self.setFixedHeight(1)


class NotepadPanel(QWidget):
    """
    Smart Notepad panel with:
    - Musical key selector
    - Mode selector (Major/Minor)
    - Diatonic chord suggestion buttons
    - Capo transposition control
    - Lyrics/chord text editor
    """

    scale_changed = pyqtSignal(str, str, list)  # key, mode, scale_notes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._previous_capo = 0
        self._lyrics_path: str | None = None
        self._setup_ui()
        self._connect_signals()
        self._update_chords()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 8, 16)
        layout.setSpacing(12)

        # ── Title ────────────────────────────────────────────────────────
        # Removed as per ultra-minimalist request.

        # ── Key & Capo Row ───────────────────────────────────────────────
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)

        # Key selector
        key_col = QVBoxLayout()
        key_col.setSpacing(4)
        key_col.addWidget(_SectionHeader("KEY"))
        
        key_row = QHBoxLayout()
        key_row.setSpacing(4)
        
        self._key_combo = CenteredComboBox()
        self._key_combo.addItems(CHROMATIC)
        self._key_combo.setCurrentText('C')
        self._key_combo.setFixedHeight(34)
        key_row.addWidget(self._key_combo, stretch=1)
        
        self._mode_combo = CenteredComboBox()
        self._mode_combo.addItems(["Major", "Minor"])
        self._mode_combo.setCurrentText('Major')
        self._mode_combo.setFixedHeight(34)
        key_row.addWidget(self._mode_combo, stretch=1)
        
        key_col.addLayout(key_row)
        controls_layout.addLayout(key_col)

        # Capo selector
        capo_col = QVBoxLayout()
        capo_col.setSpacing(4)
        capo_col.addWidget(_SectionHeader("CAPO"))
        self._capo_minus = QPushButton("-")
        self._capo_minus.setFixedSize(34, 34)
        self._capo_minus.setCursor(Qt.CursorShape.PointingHandCursor)
        self._capo_minus.setStyleSheet(f"""
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

        self._capo_spin = QSpinBox()
        self._capo_spin.setRange(-12, 12)
        self._capo_spin.setValue(0)
        self._capo_spin.setFixedHeight(34)
        self._capo_spin.setSuffix(" st")
        self._capo_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self._capo_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._capo_plus = QPushButton("+")
        self._capo_plus.setFixedSize(34, 34)
        self._capo_plus.setCursor(Qt.CursorShape.PointingHandCursor)
        self._capo_plus.setStyleSheet(self._capo_minus.styleSheet())

        capo_spin_row = QHBoxLayout()
        capo_spin_row.setSpacing(4)
        capo_spin_row.addWidget(self._capo_minus)
        capo_spin_row.addWidget(self._capo_spin, stretch=1)
        capo_spin_row.addWidget(self._capo_plus)

        capo_col.addLayout(capo_spin_row)
        controls_layout.addLayout(capo_col)

        layout.addLayout(controls_layout)

        # ── Chord Suggestions ────────────────────────────────────────────
        layout.addWidget(_SectionHeader("SUGGESTED CHORDS"))

        self._chord_grid = QGridLayout()
        self._chord_grid.setSpacing(6)
        self._chord_buttons: list[_ChordButton] = []

        # Create 7 chord buttons in 2 rows: 4 + 3
        for i in range(7):
            btn = _ChordButton(DiatonicChord('', '', '', ''))
            self._chord_buttons.append(btn)
            row = 0 if i < 4 else 1
            col = i if i < 4 else i - 4
            self._chord_grid.addWidget(btn, row, col)

        layout.addLayout(self._chord_grid)

        # ── Capo info label ──────────────────────────────────────────────
        self._capo_label = QLabel("")
        self._capo_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: {FONT_SIZE_SM}px;
            font-style: italic;
            padding: 2px 0;
        """)
        self._capo_label.setWordWrap(True)
        layout.addWidget(self._capo_label)

        layout.addWidget(_Divider())

        # ── Text Editor ──────────────────────────────────────────────────
        layout.addWidget(_SectionHeader("LYRICS & CHORDS"))

        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText(
            "Write your lyrics and chords here...\n\n"
            "Tip: Click a chord above to insert it\n"
            "at the cursor position."
        )
        self._editor.setFont(QFont(FONT_FAMILY_MONO.split(',')[0].strip(), 12))
        self._editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._editor, stretch=1)

        io_row = QHBoxLayout()
        io_row.setSpacing(8)
        self._save_btn = QPushButton("Save")
        self._load_btn = QPushButton("Load")
        for b in (self._save_btn, self._load_btn):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFixedHeight(36)
            b.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_TERTIARY};
                    color: {Colors.TEXT_PRIMARY};
                    border: 1px solid {Colors.BORDER_LIGHT};
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: {FONT_SIZE_SM}px;
                    padding: 0 16px;
                }}
                QPushButton:hover {{
                    border-color: {Colors.ACCENT};
                }}
            """)
        io_row.addWidget(self._save_btn)
        io_row.addWidget(self._load_btn)
        io_row.addStretch()
        layout.addLayout(io_row)

        self._lyrics_path_label = QLabel("")
        self._lyrics_path_label.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: {FONT_SIZE_SM - 1}px;
        """)
        self._lyrics_path_label.setWordWrap(True)
        layout.addWidget(self._lyrics_path_label)

    def _connect_signals(self):
        self._key_combo.currentTextChanged.connect(self._update_chords)
        self._mode_combo.currentTextChanged.connect(self._update_chords)
        self._capo_spin.valueChanged.connect(self._on_capo_changed)
        self._capo_minus.clicked.connect(lambda: self._capo_spin.setValue(self._capo_spin.value() - 1))
        self._capo_plus.clicked.connect(lambda: self._capo_spin.setValue(self._capo_spin.value() + 1))
        for btn in self._chord_buttons:
            btn.clicked.connect(lambda checked, b=btn: self._insert_chord(b))
        self._save_btn.clicked.connect(self._save_lyrics)
        self._load_btn.clicked.connect(self._load_lyrics)

    def _update_lyrics_path_label(self):
        if self._lyrics_path:
            self._lyrics_path_label.setText(os.path.basename(self._lyrics_path))
        else:
            self._lyrics_path_label.setText("")

    def _save_lyrics(self):
        path = self._lyrics_path
        if not path:
            default = os.path.join(lyrics_library_dir(), "lyrics.txt")
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save lyrics",
                default,
                "Text files (*.txt);;All files (*)",
            )
            if not path:
                return
            if not path.lower().endswith(".txt"):
                path += ".txt"
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._editor.toPlainText())
            self._lyrics_path = path
            self._update_lyrics_path_label()
        except OSError as e:
            QMessageBox.warning(self, "Save failed", str(e))

    def _load_lyrics(self):
        default_dir = lyrics_library_dir()
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load lyrics",
            default_dir,
            "Text files (*.txt);;All files (*)",
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            QMessageBox.warning(self, "Load failed", str(e))
            return
        self._editor.setPlainText(text)
        self._lyrics_path = path
        self._update_lyrics_path_label()

    def _on_capo_changed(self, value: int):
        delta = self._previous_capo - value
        
        # Transpose text editor chords safely (must be in brackets)
        text = self._editor.toPlainText()
        if text:
            import re
            from core.music_theory import transpose_chord_name
            
            def _replace(m):
                chord = m.group(1)
                transposed = transpose_chord_name(chord, delta)
                return f"[{transposed}]"
                
            new_text = re.sub(r'\[([^\]]+)\]', _replace, text)
            
            # preserve cursor
            cursor = self._editor.textCursor()
            pos = cursor.position()
            self._editor.setPlainText(new_text)
            
            cursor = self._editor.textCursor()
            cursor.setPosition(min(pos, len(new_text)))
            self._editor.setTextCursor(cursor)
                
        self._previous_capo = value
        self._update_chords()

    def _update_chords(self):
        """Recalculate and display diatonic chords for the current key + capo."""
        key = self._key_combo.currentText()
        mode = self._mode_combo.currentText()
        capo = self._capo_spin.value()

        base_chords = get_diatonic_chords(key, mode)
        scale_notes = get_scale_notes(key, mode)
        
        # Emit signal to update fretboard
        self.scale_changed.emit(key, mode, scale_notes)

        if capo > 0:
            display_chords = capo_display_chords(base_chords, capo)
            self._capo_label.setText(
                f"Capo +{capo}: shapes for key of {key}, "
                f"sounding pitch is {capo} semitone(s) higher."
            )
        elif capo < 0:
            display_chords = capo_display_chords(base_chords, capo)
            self._capo_label.setText(
                f"Transpose {capo}: suggested chords shifted {abs(capo)} semitone(s) down "
                f"(same shapes as key of {key}, written lower)."
            )
        else:
            display_chords = base_chords
            self._capo_label.setText("")

        for i, chord in enumerate(display_chords):
            self._chord_buttons[i]._update_display(chord)

    def _insert_chord(self, btn: _ChordButton):
        """Insert the chord name at the current cursor position in the editor."""
        chord_name = btn._chord.name
        # If name contains " → ", use only the shape name
        if ' → ' in chord_name:
            chord_name = chord_name.split(' → ')[0]
        chord_name = transpose_chord_name(chord_name, 0)
        cursor = self._editor.textCursor()
        cursor.insertText(f"[{chord_name}] ")
        self._editor.setFocus()
