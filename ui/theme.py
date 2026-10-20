"""
Theme - Officers Affairs Management System
Color palette, fonts, and style definitions for tkinter.
Supports Light and Dark mode.
"""

from dataclasses import dataclass
from typing import Dict


LIGHT = {
    # Backgrounds
    "bg_app":       "#f5f7fb",
    "bg_sidebar":   "#1f2a44",
    "bg_header":    "#ffffff",
    "bg_card":      "#ffffff",
    "bg_input":     "#f9fbff",
    "bg_table":     "#ffffff",
    "bg_table_alt": "#f0f4f8",
    "bg_selected":  "#dbeafe",
    "bg_hover":     "#eef2fb",
    "bg_dialog":    "#ffffff",

    # Text
    "text_primary":   "#1f2937",
    "text_secondary": "#667085",
    "text_sidebar":   "#c7d2e5",
    "text_sidebar_active": "#ffffff",
    "text_header":    "#1e293b",
    "text_muted":     "#98a2b3",

    # Accent / Brand
    "accent":        "#3b82f6",
    "accent_hover":  "#2563eb",
    "accent_light":  "#dbeafe",
    "sidebar_active":"#2f6adf",

    # Status colors
    "success":  "#22c55e",
    "warning":  "#f59e0b",
    "danger":   "#ef4444",
    "info":     "#3b82f6",
    "purple":   "#a855f7",

    # Borders
    "border":       "#e4e7ec",
    "border_input": "#d0d5dd",

    # Table header
    "table_header_bg":   "#25324d",
    "table_header_text": "#ffffff",

    # Scrollbar
    "scrollbar":       "#d0d5dd",
    "scrollbar_hover": "#98a2b3",
}

DARK = {
    "bg_app":       "#0d1324",
    "bg_sidebar":   "#0a1020",
    "bg_header":    "#141c2f",
    "bg_card":      "#141c2f",
    "bg_input":     "#0f172a",
    "bg_table":     "#141c2f",
    "bg_table_alt": "#0d1324",
    "bg_selected":  "#1e40af",
    "bg_hover":     "#25324d",
    "bg_dialog":    "#141c2f",

    "text_primary":   "#f1f5f9",
    "text_secondary": "#a0abc0",
    "text_sidebar":   "#a8b3c8",
    "text_sidebar_active": "#ffffff",
    "text_header":    "#f1f5f9",
    "text_muted":     "#7f8ca6",

    "accent":        "#3b82f6",
    "accent_hover":  "#2563eb",
    "accent_light":  "#25324d",
    "sidebar_active":"#2d63cd",

    "success":  "#22c55e",
    "warning":  "#f59e0b",
    "danger":   "#ef4444",
    "info":     "#3b82f6",
    "purple":   "#a855f7",

    "border":       "#2b3a56",
    "border_input": "#344966",

    "table_header_bg":   "#0f172a",
    "table_header_text": "#e2e8f0",

    "scrollbar":       "#344966",
    "scrollbar_hover": "#4a6080",
}


class ThemeManager:
    _instance = None

    def __init__(self):
        self._mode = "light"
        self._colors = dict(LIGHT)
        self._callbacks = []

    @classmethod
    def get(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    @property
    def colors(self) -> Dict[str, str]:
        return self._colors

    @property
    def mode(self) -> str:
        return self._mode

    def toggle(self):
        self._mode = "dark" if self._mode == "light" else "light"
        self._colors = dict(DARK if self._mode == "dark" else LIGHT)
        for cb in self._callbacks:
            try:
                cb()
            except Exception:
                pass

    def on_change(self, callback):
        self._callbacks.append(callback)

    def c(self, key: str) -> str:
        """Shorthand colour getter."""
        return self._colors.get(key, "#000000")


# Fonts
FONTS = {
    "title":    ("Segoe UI", 19, "bold"),
    "subtitle": ("Segoe UI", 14, "bold"),
    "heading":  ("Segoe UI", 11, "bold"),
    "body":     ("Segoe UI", 10),
    "body_bold":("Segoe UI", 10, "bold"),
    "small":    ("Segoe UI", 9),
    "sidebar":  ("Segoe UI", 10),
    "sidebar_active": ("Segoe UI", 10, "bold"),
    "table":    ("Segoe UI", 9),
    "table_hdr":("Segoe UI", 9, "bold"),
    "badge":    ("Segoe UI", 8, "bold"),
    "stat":     ("Segoe UI", 22, "bold"),
    "stat_lbl": ("Segoe UI", 9),
    "btn":      ("Segoe UI", 9, "bold"),
    "input":    ("Segoe UI", 10),
}

# Status badge colours (fg, bg)
STATUS_BADGE = {
    "Active":    ("#ffffff", "#22c55e"),
    "On Leave":  ("#ffffff", "#3b82f6"),
    "Suspended": ("#ffffff", "#f59e0b"),
    "Retired":   ("#ffffff", "#6b7280"),
    "Present":   ("#ffffff", "#22c55e"),
    "Late":      ("#ffffff", "#f59e0b"),
    "Absent":    ("#ffffff", "#ef4444"),
    "Leave":     ("#ffffff", "#3b82f6"),
    "Pending":   ("#ffffff", "#f59e0b"),
    "Approved":  ("#ffffff", "#22c55e"),
    "Rejected":  ("#ffffff", "#ef4444"),
    "Completed": ("#ffffff", "#22c55e"),
    "Cancelled": ("#ffffff", "#ef4444"),
    "Partial":   ("#ffffff", "#3b82f6"),
}
