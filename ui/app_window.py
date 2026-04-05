"""
App Window — Main Application Shell
────────────────────────────────────
QMainWindow assembling the three-panel layout:
  Left:   Smart Notepad
  Center: Interactive Fretboard
  Right:  Metronome
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QStatusBar, QLabel, QSizePolicy,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from ui.theme import Colors, FONT_SIZE_SM, apply_theme
from ui.notepad_panel import NotepadPanel
from ui.fretboard_panel import FretboardPanel
from ui.metronome_panel import MetronomePanel

from PyQt6.QtWidgets import QApplication


class AppWindow(QMainWindow):
    """Main application window with three-panel layout."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guitar Assistant")
        self.setMinimumSize(QSize(1100, 650))
        self.resize(1400, 800)

        self._setup_ui()
        self._connect_panels()
        self._setup_status_bar()

    def _setup_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main horizontal layout using QSplitter for resizable panels
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {Colors.BORDER};
            }}
            QSplitter::handle:hover {{
                background-color: {Colors.ACCENT};
            }}
        """)

        # Left: Notepad
        self._notepad = NotepadPanel()
        
        # Center: Fretboard
        self._fretboard_panel = FretboardPanel()
        
        # Right: Metronome
        self._metronome = MetronomePanel()
        
        splitter.addWidget(self._notepad)
        splitter.addWidget(self._fretboard_panel)
        splitter.addWidget(self._metronome)

        # Set initial proportions: 25% / 50% / 25%
        splitter.setSizes([300, 600, 300])
        splitter.setStretchFactor(0, 1)  # notepad
        splitter.setStretchFactor(1, 3)  # fretboard (dominant)
        splitter.setStretchFactor(2, 1)  # metronome

        main_layout.addWidget(splitter)
        self._splitter = splitter

        self._apply_panel_styles()

    def _apply_panel_styles(self):
        self._notepad.setStyleSheet(f"""
            NotepadPanel {{
                background-color: {Colors.BG_SECONDARY};
                border-right: 1px solid {Colors.BORDER_LIGHT};
            }}
        """)
        self._fretboard_panel.setStyleSheet(f"""
            FretboardPanel {{
                background-color: {Colors.BG_PRIMARY};
            }}
        """)
        self._metronome.setStyleSheet(f"""
            MetronomePanel {{
                background-color: {Colors.BG_SECONDARY};
                border-left: 1px solid {Colors.BORDER_LIGHT};
            }}
        """)
        if hasattr(self, '_splitter'):
            self._splitter.setStyleSheet(f"""
                QSplitter::handle {{
                    background-color: {Colors.BORDER_LIGHT};
                }}
            """)



    def _connect_panels(self):
        """Wire up cross-panel communication."""
        # When key changes in notepad, highlight it on the fretboard
        self._notepad.scale_changed.connect(
            self._fretboard_panel.set_highlighted_key
        )
        # Set initial key highlight by simulating an update
        self._notepad._update_chords()

    def _setup_status_bar(self):
        status = QStatusBar()
        status.setStyleSheet(f"""
            QStatusBar {{
                background-color: {Colors.BG_PRIMARY};
                color: {Colors.TEXT_MUTED};
                border-top: 1px solid {Colors.BORDER_LIGHT};
                font-size: {FONT_SIZE_SM}px;
                padding: 2px 8px;
            }}
        """)
        status.showMessage("Guitar Assistant — Ready")
        self.setStatusBar(status)

    def closeEvent(self, event):
        """Cleanup resources on close."""
        self._fretboard_panel.cleanup()
        self._metronome.cleanup()
        event.accept()
