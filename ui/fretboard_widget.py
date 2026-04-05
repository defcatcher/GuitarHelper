"""
Fretboard Widget — Custom QPainter Guitar Neck
───────────────────────────────────────────────
Beautiful, minimalist 2D guitar fretboard with:
- 6 strings × 12 frets
- Dynamic note labels at every intersection
- Fret markers (dots)
- Tuner mode glow overlay
- Anti-aliased rendering
"""

from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QLinearGradient,
    QRadialGradient, QPainterPath,
)

from ui.theme import Colors, FONT_FAMILY
from core.music_theory import (
    TUNINGS, TUNING_NAMES, get_fretboard, CHROMATIC,
    SINGLE_DOT_FRETS, DOUBLE_DOT_FRETS, NUM_FRETS,
)


class FretboardWidget(QWidget):
    """
    Custom widget rendering an interactive guitar fretboard.

    Layout: Horizontal — nut on the left, fret 12 on the right.
    String 6 (low E) at the bottom, string 1 (high E) at the top.
    """

    note_clicked = pyqtSignal(int, int)  # (string_index, fret)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        self._tuning_name: str = TUNING_NAMES[0]
        self._fretboard: list[list[str]] = get_fretboard(self._tuning_name)
        self._highlighted_key: str | None = None  # root note to highlight
        self._highlighted_mode: str = "Major"
        self._highlighted_scale: list[str] = []

        # Tuner overlay state
        self._tuner_active: bool = False
        self._tuner_string: int = -1        # 0-5, which string is being tuned
        self._tuner_cents: float = 0.0      # cents deviation
        self._tuner_in_tune: bool = False

        # Hover
        self._hover_string: int = -1
        self._hover_fret: int = -1

        # Layout constants (recomputed on resize)
        self._margin_left = 60
        self._margin_right = 30
        self._margin_top = 30
        self._margin_bottom = 30

    # ── Public API ───────────────────────────────────────────────────────

    def set_tuning(self, tuning_name: str):
        """Switch tuning and recalculate fretboard."""
        self._tuning_name = tuning_name
        self._fretboard = get_fretboard(tuning_name)
        self.update()

    def set_highlighted_key(self, key: str | None, mode: str = "Major", scale_notes: list[str] | None = None):
        """Highlight notes belonging to the given key and scale."""
        self._highlighted_key = key
        self._highlighted_mode = mode
        self._highlighted_scale = scale_notes or []
        self.update()

    def set_tuner_state(
        self, active: bool, string_idx: int = -1,
        cents: float = 0.0, in_tune: bool = False
    ):
        """Update tuner overlay."""
        self._tuner_active = active
        self._tuner_string = string_idx
        self._tuner_cents = cents
        self._tuner_in_tune = in_tune
        self.update()

    # ── Geometry helpers ─────────────────────────────────────────────────

    def _get_layout(self):
        """Calculate layout dimensions, limiting max width to center the fretboard."""
        w = self.width()
        h = self.height()
        
        # Max width constraint for elegance
        max_neck_w = 900
        neck_w = min(w - self._margin_left - self._margin_right, max_neck_w)
        
        # Center horizontally
        neck_x = (w - neck_w) / 2
        
        neck_y = self._margin_top
        neck_h = h - self._margin_top - self._margin_bottom
        return neck_x, neck_y, neck_w, neck_h

    def _fret_x(self, fret: int, neck_x: float, neck_w: float) -> float:
        """X position of a fret line. Fret 0 = nut."""
        if fret == 0:
            return neck_x
        # Uniform spacing for clarity
        return neck_x + (fret / NUM_FRETS) * neck_w

    def _string_y(self, string_idx: int, neck_y: float, neck_h: float) -> float:
        """
        Y position of a string.
        string_idx 0 = low E (bottom), 5 = high E (top).
        We draw from top to bottom: string 5 (high E) at top → string 0 (low E) at bottom.
        """
        n_strings = 6
        inverted = (n_strings - 1) - string_idx  # 5→0 (top), 0→5 (bottom)
        padding = 15  # keep strings away from edge
        usable = neck_h - 2 * padding
        return neck_y + padding + inverted * (usable / (n_strings - 1))

    def _note_center(self, string_idx: int, fret: int,
                     neck_x: float, neck_y: float,
                     neck_w: float, neck_h: float) -> QPointF:
        """Center point for a note circle at (string, fret)."""
        if fret == 0:
            x = neck_x - 20  # open note shown left of nut
        else:
            x0 = self._fret_x(fret - 1, neck_x, neck_w)
            x1 = self._fret_x(fret, neck_x, neck_w)
            x = (x0 + x1) / 2
        y = self._string_y(string_idx, neck_y, neck_h)
        return QPointF(x, y)

    # ── Paint ────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        neck_x, neck_y, neck_w, neck_h = self._get_layout()

        self._draw_neck_bg(painter, neck_x, neck_y, neck_w, neck_h)
        self._draw_fret_markers(painter, neck_x, neck_y, neck_w, neck_h)
        self._draw_frets(painter, neck_x, neck_y, neck_w, neck_h)
        self._draw_strings(painter, neck_x, neck_y, neck_w, neck_h)
        self._draw_notes(painter, neck_x, neck_y, neck_w, neck_h)
        self._draw_tuner_overlay(painter, neck_x, neck_y, neck_w, neck_h)

        painter.end()

    def _draw_neck_bg(self, p: QPainter, x, y, w, h):
        """Draw the fretboard background."""
        p.setBrush(QBrush(QColor(Colors.SURFACE)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(x - 20, y - 5, w + 25, h + 10), 16, 16)

    def _draw_fret_markers(self, p: QPainter, nx, ny, nw, nh):
        """Draw fret position markers (dots)."""
        p.setPen(Qt.PenStyle.NoPen)
        dot_color = QColor(Colors.TEXT_MUTED)
        dot_color.setAlpha(60)
        p.setBrush(QBrush(dot_color))

        mid_y = ny + nh / 2
        dot_r = 6

        for fret in SINGLE_DOT_FRETS:
            cx = (self._fret_x(fret - 1, nx, nw) + self._fret_x(fret, nx, nw)) / 2
            p.drawEllipse(QPointF(cx, mid_y), dot_r, dot_r)

        for fret in DOUBLE_DOT_FRETS:
            cx = (self._fret_x(fret - 1, nx, nw) + self._fret_x(fret, nx, nw)) / 2
            p.drawEllipse(QPointF(cx, mid_y - 25), dot_r, dot_r)
            p.drawEllipse(QPointF(cx, mid_y + 25), dot_r, dot_r)

    def _draw_frets(self, p: QPainter, nx, ny, nw, nh):
        """Draw fret wires and nut."""
        # Nut (thick bar at fret 0)
        nut_x = self._fret_x(0, nx, nw)
        p.setPen(QPen(QColor('#cccccc'), 4))
        p.drawLine(QPointF(nut_x, ny), QPointF(nut_x, ny + nh))

        # Fret wires (minimal line)
        for fret in range(1, NUM_FRETS + 1):
            fx = self._fret_x(fret, nx, nw)
            color = QColor(Colors.BORDER_LIGHT)
            p.setPen(QPen(color, 2))
            p.drawLine(QPointF(fx, ny), QPointF(fx, ny + nh))

        # Fret numbers
        p.setFont(QFont(FONT_FAMILY, 9))
        p.setPen(QColor(Colors.TEXT_MUTED))
        for fret in range(1, NUM_FRETS + 1):
            cx = (self._fret_x(fret - 1, nx, nw) + self._fret_x(fret, nx, nw)) / 2
            p.drawText(QRectF(cx - 10, ny + nh + 4, 20, 16),
                       Qt.AlignmentFlag.AlignCenter, str(fret))

    def _draw_strings(self, p: QPainter, nx, ny, nw, nh):
        """Draw 6 guitar strings with varying thickness."""
        thicknesses = [3.0, 2.5, 2.0, 1.6, 1.2, 1.0]  # low E → high E

        for i in range(6):
            sy = self._string_y(i, ny, nh)
            color = QColor(Colors.STRING_COLORS[i])

            # Tuner glow effect
            if self._tuner_active and self._tuner_string == i:
                glow_color = QColor(Colors.GREEN if self._tuner_in_tune else Colors.RED)
                glow_color.setAlpha(40)
                p.setPen(QPen(glow_color, thicknesses[i] + 10))
                p.drawLine(QPointF(nx, sy), QPointF(nx + nw, sy))

            color.setAlpha(180)
            p.setPen(QPen(color, thicknesses[i]))
            p.drawLine(QPointF(nx, sy), QPointF(nx + nw, sy))

    def _draw_notes(self, p: QPainter, nx, ny, nw, nh):
        """Draw note circles at every string × fret intersection."""
        note_r = 13
        font = QFont(FONT_FAMILY, 8, QFont.Weight.Bold)
        p.setFont(font)

        for s_idx in range(6):
            for fret in range(NUM_FRETS + 1):
                note = self._fretboard[s_idx][fret]
                center = self._note_center(s_idx, fret, nx, ny, nw, nh)

                # Determine colors
                is_root = (self._highlighted_key and note == self._highlighted_key)
                is_in_scale = (note in self._highlighted_scale)
                is_hover = (s_idx == self._hover_string and fret == self._hover_fret)

                # COMPLETELY hide out-of-scale notes for minimalistic look
                if self._highlighted_scale and not is_in_scale and not is_hover:
                    continue

                if is_root:
                    bg = QColor(Colors.NOTE_ROOT)
                    bg.setAlpha(255)
                    text_color = QColor(Colors.NOTE_BG_ROOT)
                elif is_hover:
                    bg = QColor(Colors.SECONDARY_HOVER)
                    bg.setAlpha(255)
                    text_color = QColor(Colors.TEXT_PRIMARY)
                elif is_in_scale:
                    bg = QColor(Colors.SECONDARY)
                    bg.setAlpha(200)
                    text_color = QColor(Colors.TEXT_PRIMARY)
                else: 
                    # Default rendering when no scale selected
                    bg = QColor(Colors.BG_TERTIARY)
                    bg.setAlpha(150)
                    text_color = QColor(Colors.TEXT_SECONDARY)

                # Draw circle
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(bg))
                r = note_r + (2 if is_root or is_hover else 0)
                p.drawEllipse(center, r, r)

                # Draw text
                p.setPen(text_color)
                rect = QRectF(center.x() - r, center.y() - r, r * 2, r * 2)
                p.drawText(rect, Qt.AlignmentFlag.AlignCenter, note)

    def _draw_tuner_overlay(self, p: QPainter, nx, ny, nw, nh):
        """Draw tuner mode glow on the active string."""
        if not self._tuner_active or self._tuner_string < 0:
            return

        s_idx = self._tuner_string
        sy = self._string_y(s_idx, ny, nh)

        # Determine glow color based on tuning accuracy
        cents = abs(self._tuner_cents)
        if cents < 5:
            glow = QColor(Colors.GREEN)
        elif cents < 15:
            glow = QColor(Colors.YELLOW)
        else:
            glow = QColor(Colors.RED)

        # Pulsing glow line
        for radius in [20, 14, 8]:
            c = QColor(glow)
            c.setAlpha(max(10, 60 - radius * 2))
            p.setPen(QPen(c, radius))
            p.drawLine(QPointF(nx - 20, sy), QPointF(nx + nw, sy))

    # ── Mouse interaction ────────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        nx, ny, nw, nh = self._get_layout()
        mx, my = event.position().x(), event.position().y()

        best_s, best_f = -1, -1
        best_dist = float('inf')

        for s_idx in range(6):
            for fret in range(NUM_FRETS + 1):
                center = self._note_center(s_idx, fret, nx, ny, nw, nh)
                dist = ((mx - center.x()) ** 2 + (my - center.y()) ** 2) ** 0.5
                if dist < 18 and dist < best_dist:
                    best_dist = dist
                    best_s = s_idx
                    best_f = fret

        if best_s != self._hover_string or best_f != self._hover_fret:
            self._hover_string = best_s
            self._hover_fret = best_f
            self.update()

    def leaveEvent(self, event):
        self._hover_string = -1
        self._hover_fret = -1
        self.update()

    def mousePressEvent(self, event):
        if self._hover_string >= 0 and self._hover_fret >= 0:
            self.note_clicked.emit(self._hover_string, self._hover_fret)
