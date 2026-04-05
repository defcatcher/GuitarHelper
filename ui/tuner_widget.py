"""
Tuner Widget — Visual Pitch Gauge
──────────────────────────────────
Horizontal gauge showing cents deviation with
needle animation, detected note, and string info.
"""

from __future__ import annotations

import math

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QRectF, QPointF, QPropertyAnimation, pyqtProperty, QEasingCurve
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QLinearGradient,
    QConicalGradient, QPainterPath,
)

from ui.theme import Colors, FONT_FAMILY, FONT_SIZE_XXL, FONT_SIZE_SM


class TunerGauge(QWidget):
    """
    Arc-style tuner gauge showing −50 to +50 cents.
    Features an animated needle and color gradient.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(140)

        self._needle_pos: float = 0.0  # -50 to +50
        self._animated_pos: float = 0.0

        # Smooth needle animation
        self._anim = QPropertyAnimation(self, b"animatedPos")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── Animated property ────────────────────────────────────────────────

    @pyqtProperty(float)
    def animatedPos(self) -> float:
        return self._animated_pos

    @animatedPos.setter
    def animatedPos(self, val: float):
        self._animated_pos = val
        self.update()

    def set_cents(self, cents: float):
        """Set the needle position (−50 to +50 cents)."""
        cents = max(-50.0, min(50.0, cents))
        self._needle_pos = cents
        self._anim.stop()
        self._anim.setStartValue(self._animated_pos)
        self._anim.setEndValue(cents)
        self._anim.start()

    # ── Paint ────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h - 20  # arc center near bottom

        arc_radius = min(w * 0.42, h * 0.8)
        start_angle = 30   # degrees from horizontal (left side)
        span = 120         # total arc span

        # ── Draw arc background ──────────────────────────────────────────
        arc_rect = QRectF(cx - arc_radius, cy - arc_radius,
                          arc_radius * 2, arc_radius * 2)

        # Gradient arc: red → yellow → green → yellow → red
        for i in range(60):
            frac = i / 59.0
            angle = (180 - start_angle) - frac * span  # Qt angles
            # Color mapping
            dist_from_center = abs(frac - 0.5) * 2  # 0 at center, 1 at edges
            if dist_from_center < 0.15:
                color = QColor(Colors.GREEN)
            elif dist_from_center < 0.45:
                color = QColor(Colors.YELLOW)
            else:
                color = QColor(Colors.RED)
            color.setAlpha(100)
            p.setPen(QPen(color, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawArc(arc_rect, int(angle * 16), int((span / 59) * 16))

        # ── Tick marks ───────────────────────────────────────────────────
        p.setPen(QPen(QColor(Colors.TEXT_MUTED), 1))
        for tick in range(11):  # -50, -40, ..., +50
            frac = tick / 10.0
            angle_rad = math.radians(180 - start_angle - frac * span)
            inner_r = arc_radius - 12
            outer_r = arc_radius + 5
            x1 = cx + inner_r * math.cos(angle_rad)
            y1 = cy - inner_r * math.sin(angle_rad)
            x2 = cx + outer_r * math.cos(angle_rad)
            y2 = cy - outer_r * math.sin(angle_rad)
            pen_w = 2 if tick == 5 else 1  # center tick thicker
            p.setPen(QPen(QColor(Colors.TEXT_MUTED), pen_w))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # ── Center marker ────────────────────────────────────────────────
        center_angle = math.radians(180 - start_angle - 0.5 * span)
        marker_r = arc_radius + 10
        mx = cx + marker_r * math.cos(center_angle)
        my = cy - marker_r * math.sin(center_angle)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(Colors.GREEN)))
        p.drawEllipse(QPointF(mx, my), 4, 4)

        # ── Needle ───────────────────────────────────────────────────────
        # Map cents (-50..+50) to fraction (0..1)
        frac = (self._animated_pos + 50.0) / 100.0
        frac = max(0.0, min(1.0, frac))
        needle_angle = math.radians(180 - start_angle - frac * span)

        needle_len = arc_radius - 20
        nx = cx + needle_len * math.cos(needle_angle)
        ny = cy - needle_len * math.sin(needle_angle)

        # Determine needle color
        cents_abs = abs(self._animated_pos)
        if cents_abs < 5:
            needle_color = QColor(Colors.GREEN)
        elif cents_abs < 15:
            needle_color = QColor(Colors.YELLOW)
        else:
            needle_color = QColor(Colors.RED)

        # Draw needle shadow
        shadow = QColor('#000000')
        shadow.setAlpha(60)
        p.setPen(QPen(shadow, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(cx + 1, cy + 1), QPointF(nx + 1, ny + 1))

        # Draw needle
        p.setPen(QPen(needle_color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(cx, cy), QPointF(nx, ny))

        # Needle pivot
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(Colors.TEXT_PRIMARY)))
        p.drawEllipse(QPointF(cx, cy), 5, 5)

        # ── Labels ───────────────────────────────────────────────────────
        label_font = QFont(FONT_FAMILY, 9)
        p.setFont(label_font)
        p.setPen(QColor(Colors.TEXT_SECONDARY))

        # Flat / Sharp labels
        flat_angle = math.radians(180 - start_angle)
        sharp_angle = math.radians(180 - start_angle - span)
        label_r = arc_radius + 22
        p.drawText(QPointF(cx + label_r * math.cos(flat_angle) - 10,
                           cy - label_r * math.sin(flat_angle)), "♭")
        p.drawText(QPointF(cx + label_r * math.cos(sharp_angle) - 2,
                           cy - label_r * math.sin(sharp_angle)), "♯")

        p.end()


class TunerWidget(QWidget):
    """
    Composite tuner display: gauge + note name + frequency + status.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._active = False

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Gauge
        self._gauge = TunerGauge()
        layout.addWidget(self._gauge)

        # Note name + frequency row
        info_row = QHBoxLayout()
        info_row.setSpacing(16)

        self._note_label = QLabel("—")
        self._note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._note_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_XXL}px;
            font-weight: bold;
            color: {Colors.TEXT_PRIMARY};
        """)
        info_row.addWidget(self._note_label)

        right_col = QVBoxLayout()
        right_col.setSpacing(2)

        self._freq_label = QLabel("— Hz")
        self._freq_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_SM}px;
            color: {Colors.TEXT_SECONDARY};
        """)
        right_col.addWidget(self._freq_label)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_SM}px;
            font-weight: bold;
        """)
        right_col.addWidget(self._status_label)

        info_row.addLayout(right_col)
        layout.addLayout(info_row)

    def update_tuner(self, note: str, freq: float, cents: float, string_name: str):
        """Update the tuner display with new pitch data."""
        self._note_label.setText(note)
        self._freq_label.setText(f"{freq:.1f} Hz")
        self._gauge.set_cents(cents)

        cents_abs = abs(cents)
        if cents_abs < 5:
            self._status_label.setText("✓ In Tune")
            self._status_label.setStyleSheet(f"font-size: {FONT_SIZE_SM}px; font-weight: bold; color: {Colors.GREEN};")
        elif cents < 0:
            self._status_label.setText(f"♭ Flat ({cents:.0f}¢)")
            self._status_label.setStyleSheet(f"font-size: {FONT_SIZE_SM}px; font-weight: bold; color: {Colors.RED};")
        else:
            self._status_label.setText(f"♯ Sharp (+{cents:.0f}¢)")
            self._status_label.setStyleSheet(f"font-size: {FONT_SIZE_SM}px; font-weight: bold; color: {Colors.BLUE};")

    def clear(self):
        """Reset to idle state."""
        self._note_label.setText("—")
        self._freq_label.setText("— Hz")
        self._status_label.setText("Play a string...")
        self._status_label.setStyleSheet(f"font-size: {FONT_SIZE_SM}px; color: {Colors.TEXT_SECONDARY};")
        self._gauge.set_cents(0.0)
