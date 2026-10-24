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
import weakref
from typing import Dict, List, Tuple

from .storage import application_settings
from .design import DESIGN, METRICS, text_on, readable_accent
from PyQt6.QtGui import QColor

ACCENT_DEFINITIONS={a["name"]:a for a in DESIGN["accents"]}
LOBE_ACCENTS: Dict[str,str]={name:a["hex"] for name,a in ACCENT_DEFINITIONS.items()}

def normalize_accent_name(name):
    candidate="Lobe "+name[8:] if name.startswith("GestArt ") else name
    return candidate if candidate in LOBE_ACCENTS else "Lobe Blue"

@dataclass
class ThemeColors:
    is_dark: bool
    accent_name: str
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_subtle: str
    accent_ink: str
    accent_text: str
    
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
        self._settings = application_settings()
        self.is_dark = self._settings.value("theme_is_dark", True, type=bool)
        saved_accent = str(self._settings.value("theme_accent", "Lobe Blue"))
        self.accent_name = normalize_accent_name(saved_accent)
        if self.accent_name != saved_accent:
            self._settings.setValue("theme_accent",self.accent_name)
            self._settings.sync()
        self._listeners = []

    @classmethod
    def get_instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    def add_listener(self,callback):
        for ref in self._listeners:
            if ref()==callback:return
        self._listeners.append(weakref.WeakMethod(callback) if getattr(callback,"__self__",None) is not None else lambda:callback)

    def remove_listener(self,callback):
        self._listeners=[ref for ref in self._listeners if ref() is not None and ref()!=callback]

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
        self._listeners=[ref for ref in self._listeners if ref() is not None]
        for ref in list(self._listeners):
            callback=ref()
            if callback is not None:
                try:callback()
                except RuntimeError:pass # A Qt widget may already have been destroyed.

    def get_colors(self) -> ThemeColors:
        p = DESIGN["colors"]["dark" if self.is_dark else "light"]
        definition=ACCENT_DEFINITIONS.get(self.accent_name,ACCENT_DEFINITIONS["Lobe Blue"])
        accent=definition.get("dark" if self.is_dark else "light",definition["hex"])
        hover=QColor(accent).lighter(108).name() if self.is_dark else QColor(accent).darker(106).name()
        pressed=QColor(accent).darker(112).name()
        rgb=tuple(int(accent[i:i+2],16) for i in (1,3,5))
        return ThemeColors(is_dark=self.is_dark,accent_name=self.accent_name,
            accent=accent,accent_hover=hover,accent_pressed=pressed,
            accent_subtle=f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {0.18 if self.is_dark else 0.10})",
            accent_ink=text_on(accent),accent_text=readable_accent(accent,p["card"]),
            bg_app=p["canvas"],bg_surface=p["surface"],bg_card=p["card"],bg_elevated=p["raised"],bg_input=p["input"],
            border_subtle=p["border"],border_active=accent,border_specular=p["border"],
            text_primary=p["text"],text_secondary=p["secondary"],text_muted=p["muted"],
            scroll_track="transparent",scroll_handle=p["scroll"],scroll_handle_hover=p["secondary"])

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
            padding: 8px 12px;
            spacing: 8px;
        }}
        QToolBar::separator {{
            width: 1px;
            background-color: {c.border_subtle};
            margin: 8px;
        }}

        /* ToolButton */
        QToolButton {{
            background-color: transparent;
            color: {c.text_secondary};
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 4px 8px;
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
            color: {c.accent_text};
        }}

        /* PushButton */
        QPushButton {{
            background-color: {c.bg_card};
            color: {c.text_primary};
            border: 1px solid {c.border_subtle};
            border-radius: 8px;
            padding: 8px 12px;
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
            color: {c.accent_ink};
            border: 1px solid {c.accent};
            border-radius: 8px;
            padding: 8px 12px;
            font-weight: 600;
            font-size: 13px;
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
            border-radius: 8px;
            padding: 6px 10px;
            selection-background-color: {c.accent};
            selection-color: {c.accent_ink};
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
            padding: 8px 12px;
            margin-right: 4px;
            border: none;
            border-bottom: 2px solid transparent;
            font-weight: 500;
            font-size: 12px;
        }}
        QTabBar::tab:hover {{
            color: {c.text_primary};
            background-color: {c.bg_elevated};
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        QTabBar::tab:selected {{
            color: {c.accent_text};
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
            font-size: 12px;
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
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {c.accent};
            color: {c.accent_ink};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {c.border_subtle};
            margin: 4px 6px;
        }}

        QToolButton:focus, QPushButton:focus, QComboBox:focus {{
            border: 2px solid {c.accent};
        }}
        QToolButton:disabled, QPushButton:disabled {{ color: {c.text_muted}; }}
        QComboBox {{
            background-color: {c.bg_input}; color: {c.text_primary};
            border: 1px solid {c.border_subtle}; border-radius: 8px;
            min-height: 32px; padding: 0px 8px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {c.bg_surface}; color: {c.text_primary};
            selection-background-color: {c.bg_elevated}; selection-color: {c.text_primary};
        }}
        QStackedWidget#inspectorStack {{ background-color: {c.bg_surface}; }}
        QLabel#inspectorHeading {{ font-size: 16px; font-weight: 600; padding: 0px; }}
        /* ToolTip */
        QToolTip {{
            background-color: {c.bg_card};
            color: {c.text_primary};
            border: 1px solid {c.border_subtle};
            border-radius: 8px;
            padding: 5px 8px;
            font-size: 12px;
        }}
        """
