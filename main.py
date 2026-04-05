"""
Guitar Assistant — Entry Point
───────────────────────────────
Minimalist desktop guitar assistant for Windows 10/11.
"""

import sys
import os

# Ensure the project root is in the path
_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ui.theme import apply_theme
from ui.app_window import AppWindow


def _window_icon_path():
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        return os.path.join(base, "icon", "guitarassistant.png")
    return os.path.join(_ROOT, "icon", "guitarassistant.png")


def main():
    # High-DPI support
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'

    app = QApplication(sys.argv)
    if sys.platform == "darwin":
        app.setStyle("Fusion")
    app.setApplicationName("Guitar Assistant")
    app.setOrganizationName("GuitarHelper")

    _ip = _window_icon_path()
    if os.path.isfile(_ip):
        app.setWindowIcon(QIcon(_ip))

    # Apply dark theme
    apply_theme(app)

    # Create and show main window
    window = AppWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
