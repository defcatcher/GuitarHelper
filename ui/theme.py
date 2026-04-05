"""
Theme — Dark Mode Design System
────────────────────────────────
Color tokens, palette, fonts, and global stylesheet
for the Guitar Assistant application.
"""

from PyQt6.QtWidgets import QApplication, QComboBox, QStyleOptionComboBox, QStyle
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter
from PyQt6.QtCore import Qt

# ── Color Tokens ─────────────────────────────────────────────────────────────

class Colors:
    """Centralized color palette matching requested green theme."""
    BG_PRIMARY     = '#2a332e'     # Very dark green-gray
    BG_SECONDARY   = '#2a332e'
    BG_TERTIARY    = '#334239'     # Elevated surface
    BG_INPUT       = '#334239'
    SURFACE        = '#2a332e'
    
    ACCENT         = '#3ea869'     # Primary accent green
    ACCENT_HOVER   = '#25db6d'     # Bright green hover
    ACCENT_DIM     = '#437557'     # Dimmed accent
    
    SECONDARY      = '#437557'     # Secondary accent
    SECONDARY_HOVER= '#3ea869'
    
    TEXT_PRIMARY   = '#eaeaea'
    TEXT_SECONDARY = '#a4b4a9'
    TEXT_MUTED     = '#7f9387'
    
    BORDER         = 'transparent'
    BORDER_LIGHT   = '#405047'
    
    STRING_COLORS  = ['#a4b4a9'] * 6

    NOTE_ROOT      = '#25db6d'
    NOTE_NATURAL   = '#eaeaea'
    NOTE_SHARP     = '#a4b4a9'
    NOTE_BG        = '#334239'
    NOTE_BG_ROOT   = '#2a332e'
    
    GREEN          = '#3ea869'
    YELLOW         = '#ffa502'
    RED            = '#ff4757'
    BLUE           = '#3742fa'

# ── Typography ───────────────────────────────────────────────────────────────

FONT_FAMILY = "Manrope"
FONT_FAMILY_MONO = "Cascadia Code, Consolas, Courier New"
FONT_SIZE_SM = 11
FONT_SIZE_MD = 13
FONT_SIZE_LG = 16
FONT_SIZE_XL = 22
FONT_SIZE_XXL = 32


# ── Custom Widgets ───────────────────────────────────────────────────────────

class CenteredComboBox(QComboBox):
    """QComboBox that centers its displayed text."""
    def paintEvent(self, event):
        painter = QPainter(self)
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        
        # Draw background and base styling
        self.style().drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt, painter, self)
        
        # Draw centered text
        text = self.currentText()
        painter.setPen(QColor(Colors.TEXT_PRIMARY))
        painter.drawText(opt.rect, Qt.AlignmentFlag.AlignCenter, text)


# ── Global Stylesheet ────────────────────────────────────────────────────────

def get_global_qss():
    return f"""
QMainWindow {{
    background-color: {Colors.BG_PRIMARY};
}}

QWidget {{
    color: {Colors.TEXT_PRIMARY};
    font-family: '{FONT_FAMILY}';
    font-size: {FONT_SIZE_MD}px;
}}

QLabel {{
    color: {Colors.TEXT_PRIMARY};
    background: transparent;
}}

QPushButton {{
    background-color: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
    border: none;
    border-radius: 12px;
    padding: 10px 16px;
    font-size: {FONT_SIZE_MD}px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {Colors.SECONDARY};
}}

QPushButton:pressed {{
    background-color: {Colors.SECONDARY_HOVER};
}}

QPushButton:checked {{
    background-color: {Colors.ACCENT};
    color: {Colors.BG_PRIMARY};
}}

QComboBox {{
    background-color: {Colors.BG_INPUT};
    color: {Colors.TEXT_PRIMARY};
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: bold;
}}

QComboBox::drop-down {{
    border: none;
    width: 0px;
}}

QComboBox::down-arrow {{
    image: none;
}}

QComboBox QAbstractItemView {{
    background-color: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_LIGHT};
    border-radius: 8px;
    selection-background-color: {Colors.SECONDARY_HOVER};
    selection-color: {Colors.TEXT_PRIMARY};
    outline: none;
}}

QSpinBox {{
    background-color: {Colors.BG_INPUT};
    color: {Colors.TEXT_PRIMARY};
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: bold;
}}

QSpinBox::up-button, QSpinBox::down-button {{
    width: 0px;
    border: none;
}}

QSlider::groove:horizontal {{
    background: {Colors.BG_TERTIARY};
    height: 8px;
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: {Colors.ACCENT};
    width: 24px;
    height: 24px;
    margin: -8px 0;
    border-radius: 12px;
}}

QSlider::sub-page:horizontal {{
    background: {Colors.ACCENT_DIM};
    height: 8px;
    border-radius: 4px;
}}

QPlainTextEdit {{
    background-color: {Colors.BG_INPUT};
    color: {Colors.TEXT_PRIMARY};
    border: none;
    border-radius: 12px;
    padding: 16px;
    font-family: {FONT_FAMILY_MONO};
    font-size: {FONT_SIZE_MD}px;
    selection-background-color: {Colors.SECONDARY_HOVER};
    selection-color: {Colors.TEXT_PRIMARY};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: {Colors.BG_TERTIARY};
    min-height: 40px;
    border-radius: 5px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QGroupBox {{
    color: {Colors.TEXT_SECONDARY};
    border: none;
    margin-top: 16px;
    padding-top: 20px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0;
    color: {Colors.TEXT_SECONDARY};
}}

QToolTip {{
    background-color: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
    border: none;
    border-radius: 8px;
    padding: 6px 12px;
}}
}}
"""


def apply_theme(app: QApplication):
    """Apply the active theme to the entire application."""
    import os
    from PyQt6.QtGui import QFontDatabase
    
    # Load fonts
    font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "font")
    if os.path.exists(font_dir):
        for font_file in os.listdir(font_dir):
            if font_file.endswith(".otf") or font_file.endswith(".ttf"):
                QFontDatabase.addApplicationFont(os.path.join(font_dir, font_file))

    # Set palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BG_PRIMARY))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(Colors.BG_INPUT))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.BG_SECONDARY))
    palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(Colors.BG_TERTIARY))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Colors.BG_PRIMARY))
    app.setPalette(palette)

    # Set global stylesheet
    app.setStyleSheet(get_global_qss())

    # Set default font
    font = QFont(FONT_FAMILY, FONT_SIZE_MD)
    font.setWeight(QFont.Weight.Light)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(font)
