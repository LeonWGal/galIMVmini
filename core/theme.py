"""
galIMVmini Theme and Styling Engine.
Faithful implementation of galIMV's Lobe Hub Neo Design System:
- Deep obsidian / zinc dark mode (#09090b, #121215, #18181b)
- Specular hairline card borders (#27272a / rgba(255,255,255,0.08))
- Pure vector aesthetics (zero emojis, Tabler icons)
- Elimination of all Windows native white/gray frames and backgrounds
- Signature Lobe accents (Lobe Blue, Purple, Emerald, Orange, Rose, Zinc)
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from PyQt6.QtCore import QSettings

LOBE_ACCENTS: Dict[str, str] = {
    "Lobe Blue": "#1677ff",
    "Lobe Purple": "#722ed1",
    "Lobe Magenta": "#eb2f96",
    "Lobe Cyan": "#13c2c2",
    "Lobe Green": "#52c41a",
    "Lobe Orange": "#fa8c16",
    "Monochrome Zinc": "#71717a",
}

LOBE_ACCENT_HOVERS: Dict[str, str] = {
    "Lobe Blue": "#4096ff",
    "Lobe Purple": "#9254de",
    "Lobe Magenta": "#f759ab",
    "Lobe Cyan": "#36cfc9",
    "Lobe Green": "#73d13d",
    "Lobe Orange": "#ffa940",
    "Monochrome Zinc": "#a1a1aa",
}

LOBE_ACCENT_PRESSED: Dict[str, str] = {
    "Lobe Blue": "#0958d9",
    "Lobe Purple": "#531dab",
    "Lobe Magenta": "#c41d7f",
    "Lobe Cyan": "#08979c",
    "Lobe Green": "#389e0d",
    "Lobe Orange": "#d46b08",
    "Monochrome Zinc": "#52525b",
}

@dataclass
class ThemeColors:
    is_dark: bool
    accent_name: str
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_subtle: str
    
    bg_app: str
    bg_surface: str
    bg_card: str
    bg_elevated: str
    bg_input: str
    
    border_subtle: str
    border_active: str
    border_specular: str
    
    text_primary: str
    text_secondary: str
    text_muted: str
    
    scroll_track: str
    scroll_handle: str
    scroll_handle_hover: str


class ThemeManager:
    _instance = None

    def __init__(self):
        self._settings = QSettings("galIMV", "galIMVmini")
        self.is_dark = self._settings.value("theme_is_dark", True, type=bool)
        saved_accent = str(self._settings.value("theme_accent", "Lobe Blue"))
        self.accent_name = saved_accent if saved_accent in LOBE_ACCENTS else "Lobe Blue"
        self._listeners = []

    @classmethod
    def get_instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    def add_listener(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def set_theme(self, is_dark: bool, accent_name: str = None):
        self.is_dark = is_dark
        self._settings.setValue("theme_is_dark", is_dark)
        if accent_name and accent_name in LOBE_ACCENTS:
            self.accent_name = accent_name
            self._settings.setValue("theme_accent", accent_name)
        self._settings.sync()
        self._notify()

    def set_accent(self, accent_name: str):
        if accent_name in LOBE_ACCENTS:
            self.accent_name = accent_name
            self._settings.setValue("theme_accent", accent_name)
            self._settings.sync()
            self._notify()

    def toggle_dark_light(self):
        self.is_dark = not self.is_dark
        self._settings.setValue("theme_is_dark", self.is_dark)
        self._settings.sync()
        self._notify()

    def _notify(self):
        for cb in self._listeners:
            try:
                cb()
            except Exception:
                pass

    def get_colors(self) -> ThemeColors:
        accent = LOBE_ACCENTS.get(self.accent_name, "#1677ff")
        accent_hover = LOBE_ACCENT_HOVERS.get(self.accent_name, "#4096ff")
        accent_pressed = LOBE_ACCENT_PRESSED.get(self.accent_name, "#0958d9")
        
        if self.is_dark:
            return ThemeColors(
                is_dark=True,
                accent_name=self.accent_name,
                accent=accent,
                accent_hover=accent_hover,
                accent_pressed=accent_pressed,
                accent_subtle="rgba(22, 119, 255, 0.16)",
                
                bg_app="#0e0e12",          # galIMV obsidian canvas
                bg_surface="#141419",      # galIMV surface panels & toolbar
                bg_card="#1a1a23",         # galIMV card containers
                bg_elevated="#22222e",     # galIMV badge hover & active items
                bg_input="#101015",        # galIMV deep contrast input areas
                
                border_subtle="#262633",   # galIMV refined border
                border_active=accent,
                border_specular="rgba(255, 255, 255, 0.12)",
                
                text_primary="#f8f8fc",    # galIMV high-contrast crisp text
                text_secondary="#c8c8d2",  # galIMV secondary text
                text_muted="#9494a0",      # galIMV captions & labels
                
                scroll_track="transparent",
                scroll_handle="#2b2b3a",
                scroll_handle_hover="#424258",
            )
        else:
            return ThemeColors(
                is_dark=False,
                accent_name=self.accent_name,
                accent=accent,
                accent_hover=accent_hover,
                accent_pressed=accent_pressed,
                accent_subtle="rgba(22, 119, 255, 0.12)",
                
                bg_app="#f8fafc",          # Clean modern canvas (Slate 50)
                bg_surface="#ffffff",      # Pure crisp white panels & cards
                bg_card="#ffffff",         # Card containers
                bg_elevated="#f1f5f9",     # Hover items & chips (Slate 100)
                bg_input="#f8fafc",        # Inputs with subtle boundary
                
                border_subtle="#e2e8f0",   # Crisp Slate 200 border
                border_active=accent,
                border_specular="rgba(0, 0, 0, 0.04)",
                
                text_primary="#0f172a",    # Deep crisp slate black (rich contrast)
                text_secondary="#334155",  # Clear legible slate text
                text_muted="#64748b",      # Legible captions & labels
                
                scroll_track="transparent",
                scroll_handle="#cbd5e1",
                scroll_handle_hover="#94a3b8",
            )

    def get_application_stylesheet(self) -> str:
        c = self.get_colors()
        return f"""
        QMainWindow, QDialog {{
            background-color: {c.bg_app};
            color: {c.text_primary};
            font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
            font-size: 13px;
        }}
        
        QWidget {{
            color: {c.text_primary};
            font-size: 13px;
            font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
        }}

        /* ToolBar */
        QToolBar {{
            background-color: {c.bg_surface};
            border-bottom: 1px solid {c.border_subtle};
            padding: 3px 8px;
            spacing: 4px;
        }}
        QToolBar::separator {{
            width: 1px;
            background-color: {c.border_subtle};
            margin: 5px 6px;
        }}

        /* ToolButton */
        QToolButton {{
            background-color: transparent;
            color: {c.text_secondary};
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 2px 5px;
            font-weight: 500;
            font-size: 12px;
        }}
        QToolButton::menu-indicator {{
            image: none;
            width: 0px;
        }}
        QToolButton:hover {{
            background-color: {c.bg_elevated};
            border-color: {c.border_subtle};
            color: {c.text_primary};
        }}
        QToolButton:pressed {{
            background-color: {c.bg_card};
        }}
        QToolButton:checked {{
            background-color: {c.accent_subtle};
            border-color: {c.accent};
            color: {c.accent};
        }}

        /* PushButton */
        QPushButton {{
            background-color: {c.bg_card};
            color: {c.text_primary};
            border: 1px solid {c.border_subtle};
            border-radius: 6px;
            padding: 4px 10px;
            font-weight: 500;
            font-size: 12px;
        }}
        QPushButton:hover {{
            background-color: {c.bg_elevated};
            border-color: {c.text_secondary};
        }}
        QPushButton:pressed {{
            background-color: {c.bg_app};
        }}
        QPushButton:disabled {{
            background-color: {c.bg_surface};
            color: {c.text_muted};
            border-color: {c.border_subtle};
        }}
        QPushButton#primaryOpenBtn {{
            background-color: {c.accent};
            color: #ffffff;
            border: 1px solid {c.accent};
            border-radius: 6px;
            padding: 4px 12px;
            font-weight: 600;
            font-size: 12.5px;
        }}
        QPushButton#primaryOpenBtn:hover {{
            background-color: {c.accent_hover};
            border-color: {c.accent_hover};
        }}
        QPushButton#primaryOpenBtn:pressed {{
            background-color: {c.accent_pressed};
            border-color: {c.accent_pressed};
        }}

        /* LineEdit & TextEdit */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {c.bg_input};
            color: {c.text_primary};
            border: 1px solid {c.border_subtle};
            border-radius: 6px;
            padding: 6px 10px;
            selection-background-color: {c.accent};
            selection-color: #ffffff;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {c.accent};
        }}

        /* TableWidget */
        QTableWidget {{
            background-color: {c.bg_surface};
            color: {c.text_primary};
            border: 1px solid {c.border_subtle};
            border-radius: 8px;
            gridline-color: {c.border_subtle};
            selection-background-color: {c.accent_subtle};
            selection-color: {c.text_primary};
        }}
        QHeaderView::section {{
            background-color: {c.bg_card};
            color: {c.text_secondary};
            padding: 6px 10px;
            border: none;
            border-bottom: 1px solid {c.border_subtle};
            font-weight: 600;
            font-size: 12px;
        }}

        /* TabWidget - Minimalist Underline Style (Lobe / galIMV) */
        QTabWidget {{
            border: none;
            background: transparent;
        }}
        QTabWidget::pane {{
            border: none;
            background-color: transparent;
            top: 0px;
        }}
        QTabBar {{
            background: transparent;
            border-bottom: 1px solid {c.border_subtle};
        }}
        QTabBar::tab {{
            background-color: transparent;
            color: {c.text_secondary};
            padding: 3px 9px;
            margin-right: 2px;
            border: none;
            border-bottom: 2px solid transparent;
            font-weight: 500;
            font-size: 11px;
        }}
        QTabBar::tab:hover {{
            color: {c.text_primary};
            background-color: {c.bg_elevated};
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        QTabBar::tab:selected {{
            color: {c.accent};
            border-bottom: 2px solid {c.accent};
            font-weight: 600;
        }}

        /* Global ScrollArea - Neutralize white backgrounds! */
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}

        /* Sleek Modern ScrollBars (Lobe 6px bar) */
        QScrollBar:vertical {{
            border: none;
            background-color: transparent;
            width: 6px;
            margin: 0;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {c.scroll_handle};
            min-height: 24px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {c.scroll_handle_hover};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
            height: 0;
        }}
        
        QScrollBar:horizontal {{
            border: none;
            background-color: transparent;
            height: 6px;
            margin: 0;
            border-radius: 3px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {c.scroll_handle};
            min-width: 24px;
            border-radius: 3px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {c.scroll_handle_hover};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
            width: 0;
        }}

        /* Splitter */
        QSplitter::handle {{
            background-color: {c.border_subtle};
        }}
        QSplitter::handle:hover {{
            background-color: {c.accent};
        }}

        /* StatusBar */
        QStatusBar {{
            background-color: {c.bg_surface};
            color: {c.text_secondary};
            border-top: 1px solid {c.border_subtle};
            padding: 2px 8px;
            font-size: 11px;
        }}

        /* Menu */
        QMenu {{
            background-color: {c.bg_surface};
            color: {c.text_primary};
            border: 1px solid {c.border_subtle};
            border-radius: 8px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 18px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {c.accent};
            color: #ffffff;
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {c.border_subtle};
            margin: 4px 6px;
        }}

        /* ToolTip */
        QToolTip {{
            background-color: {c.bg_card};
            color: {c.text_primary};
            border: 1px solid {c.border_subtle};
            border-radius: 6px;
            padding: 5px 8px;
            font-size: 12px;
        }}
        """
