"""
Cross-platform user directories (Documents, etc.).
Requires QApplication before QStandardPaths is used (normal for UI code).
"""

from __future__ import annotations

import os

from PyQt6.QtCore import QStandardPaths

_APP_FOLDER = "Guitar Assistant"


def lyrics_library_dir() -> str:
    """`Documents/Guitar Assistant` (or platform equivalent). Created if missing."""
    docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    if not docs:
        docs = os.path.expanduser("~")
    path = os.path.join(docs, _APP_FOLDER)
    os.makedirs(path, exist_ok=True)
    return path
