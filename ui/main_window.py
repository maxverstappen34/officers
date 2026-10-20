"""
Main Application Window - Officers Affairs Management System
Sidebar navigation, header, theme toggle, and view routing.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.theme import ThemeManager, FONTS
from ui.components.widgets import Button, info_dialog

logger = logging.getLogger(__name__)
tm = ThemeManager.get


# ──────────────────────────────────────────────
# Sidebar item
# ──────────────────────────────────────────────

class SidebarItem(tk.Frame):
    def __init__(self, parent, icon: str, label: str,
                 command=None, active: bool = False, **kw):
        t = tm()
        bg = t.c("sidebar_active") if active else t.c("bg_sidebar")
        super().__init__(parent, bg=bg, cursor="hand2", **kw)
        self._command = command
        self._active  = active
        self._icon    = icon
        self._label   = label
        self._compact = False

        inner = tk.Frame(self, bg=bg)
        self._inner = inner
        inner.pack(fill="x", padx=12, pady=9)

        self._icon_lbl = tk.Label(inner, text=icon, bg=bg,
                                   fg=t.c("text_sidebar_active") if active
                                   else t.c("text_sidebar"),
                                   font=("Segoe UI", 14), width=2)
        self._icon_lbl.pack(side="left")

        self._text_lbl = tk.Label(inner, text=label, bg=bg,
                                   fg=t.c("text_sidebar_active") if active
                                   else t.c("text_sidebar"),
                                   font=FONTS["sidebar_active"] if active
                                   else FONTS["sidebar"],
                                   anchor="w")
        self._text_lbl.pack(side="left", padx=10)

        # Active bar on left
        self._bar = tk.Frame(self, bg=t.c("accent") if active else bg, width=4)
        self._bar.place(relx=0, rely=0, relheight=1)

        self.bind("<Button-1>",    self._on_click)
        self.bind("<Enter>",       self._on_enter)
        self.bind("<Leave>",       self._on_leave)
        inner.bind("<Button-1>",   self._on_click)
        for child in inner.winfo_children():
            child.bind("<Button-1>", self._on_click)

    def _on_click(self, _=None):
        if self._command:
            self._command()

    def _on_enter(self, _):
        if not self._active:
            self.configure(bg=tm().c("bg_hover"))

    def _on_leave(self, _):
        if not self._active:
            self.configure(bg=tm().c("bg_sidebar"))

    def set_active(self, active: bool):
        self._active = active
        t = tm()
        bg = t.c("sidebar_active") if active else t.c("bg_sidebar")
        fg = t.c("text_sidebar_active") if active else t.c("text_sidebar")
        self.configure(bg=bg)
        self._icon_lbl.configure(bg=bg, fg=fg)
        self._text_lbl.configure(bg=bg, fg=fg,
                                  font=FONTS["sidebar_active"] if active
                                  else FONTS["sidebar"])
        self._bar.configure(bg=t.c("accent") if active else bg)
        for child in self.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=bg)

    def set_compact(self, compact: bool):
        self._compact = compact
        if compact:
            self._text_lbl.pack_forget()
            self._inner.configure(padx=6)
        else:
            if not self._text_lbl.winfo_manager():
                self._text_lbl.pack(side="left", padx=10)
            self._inner.configure(padx=12)


# ──────────────────────────────────────────────
# Main Application
# ──────────────────────────────────────────────

class MainApp(tk.Tk):
    def __init__(self, services):
        super().__init__()
        self._svc = services
        self._current_view = None
        self._current_module = None
        self._sidebar_items = {}
        self._sidebar_width = 240
        self._compact_sidebar = False

        self.title("Officers Affairs Management System")
        self.geometry("1280x780")
        self.minsize(900, 600)
        self._set_icon()
        self._configure_styles()

        tm().on_change(self._retheme)
        self._build_layout()
        self._navigate("dashboard")
        self.bind("<Configure>", self._on_resize)

        # Clock update
        self._update_clock()

    def _set_icon(self):
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        t = tm()
        style.configure("TNotebook",
                         background=t.c("bg_dialog"),
                         borderwidth=0)
        style.configure("TNotebook.Tab",
                         background=t.c("bg_hover"),
                         foreground=t.c("text_secondary"),
                         font=FONTS["body"],
                         padding=(16, 6))
        style.map("TNotebook.Tab",
                  background=[("selected", t.c("bg_card"))],
                  foreground=[("selected", t.c("accent"))])
        style.configure("Vertical.TScrollbar",
                         background=t.c("scrollbar"),
                         troughcolor=t.c("bg_app"),
                         borderwidth=0, arrowsize=14)
        style.configure("Horizontal.TScrollbar",
                         background=t.c("scrollbar"),
                         troughcolor=t.c("bg_app"),
                         borderwidth=0, arrowsize=14)
        style.configure("TSeparator", background=t.c("border"))

    def _build_layout(self):
        t = tm()
        self.configure(bg=t.c("bg_app"))

        # ── Sidebar ──────────────────────────────────────
        self._sidebar = tk.Frame(self, bg=t.c("bg_sidebar"), width=240)
        self._sidebar.grid(row=0, column=0, sticky="ns")
        self._sidebar.grid_propagate(False)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Logo / branding
        logo_frame = tk.Frame(self._sidebar, bg=t.c("bg_sidebar"), height=72)
        self._logo_frame = logo_frame
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        tk.Label(logo_frame, text="🛡", bg=t.c("bg_sidebar"),
                 font=("Segoe UI", 26)).pack(side="left", padx=14, pady=12)
        lbl_frame = tk.Frame(logo_frame, bg=t.c("bg_sidebar"))
        self._logo_labels_frame = lbl_frame
        lbl_frame.pack(side="left", pady=10)
        self._logo_title = tk.Label(lbl_frame, text="Officers", bg=t.c("bg_sidebar"),
                 fg="white", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self._logo_subtitle = tk.Label(lbl_frame, text="Affairs System", bg=t.c("bg_sidebar"),
                 fg=t.c("text_sidebar"), font=("Segoe UI", 8)).pack(anchor="w")

        # Separator
        tk.Frame(self._sidebar, bg="#2d4a6e", height=1).pack(fill="x", padx=12, pady=4)

        # Nav items
        nav_items = [
            ("dashboard",   "⊞",  "Dashboard"),
            ("search",      "🔎", "Global Search"),
            ("officers",    "👮", "Officers"),
            ("attendance",  "✓",  "Attendance"),
            ("leaves",      "📅", "Leave & Vacations"),
            ("accumulation","🧮", "Leave Accumulation"),
            ("duties",      "📋", "Daily Duties"),
            ("meals",       "🍽", "Meals Log"),
        ]
        for module_key, icon, label in nav_items:
            item = SidebarItem(
                self._sidebar, icon=icon, label=label,
                command=lambda k=module_key: self._navigate(k))
            item.pack(fill="x")
            self._sidebar_items[module_key] = item

        # Bottom section
        tk.Frame(self._sidebar, bg="#2d4a6e", height=1).pack(
            fill="x", padx=12, pady=(8, 4), side="bottom")

        bottom = tk.Frame(self._sidebar, bg=t.c("bg_sidebar"))
        bottom.pack(side="bottom", fill="x", pady=4)

        # Theme toggle
        self._theme_btn = tk.Label(
            bottom, text="☀  Light Mode", bg=t.c("bg_sidebar"),
            fg=t.c("text_sidebar"), font=FONTS["small"],
            cursor="hand2", padx=12, pady=8)
        self._theme_btn.pack(fill="x")
        self._theme_btn.bind("<Button-1>", lambda _: self._toggle_theme())

        # ── Right panel ──────────────────────────────────
        right = tk.Frame(self, bg=t.c("bg_app"))
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        # Header bar
        self._header = tk.Frame(right, bg=t.c("bg_header"), height=54)
        self._header.grid(row=0, column=0, sticky="ew")
        self._header.grid_propagate(False)

        self._breadcrumb = tk.Label(
            self._header, text="Dashboard",
            bg=t.c("bg_header"), fg=t.c("text_header"),
            font=FONTS["heading"])
        self._breadcrumb.pack(side="left", padx=20)

        self._menu_toggle = Button(self._header, "☰", command=self._toggle_sidebar, style="ghost")
        self._menu_toggle.pack(side="left", padx=(8, 0), pady=8)

        # Clock
        self._clock_lbl = tk.Label(
            self._header, text="",
            bg=t.c("bg_header"), fg=t.c("text_secondary"),
            font=FONTS["small"])
        self._clock_lbl.pack(side="right", padx=16)

        # User badge
        tk.Label(self._header, text="👤 Admin",
                 bg=t.c("bg_header"), fg=t.c("text_secondary"),
                 font=FONTS["small"]).pack(side="right", padx=8)

        # Divider
        tk.Frame(right, bg=t.c("border"), height=1).grid(row=1, column=0, sticky="ew")

        # Content area
        self._content = tk.Frame(right, bg=t.c("bg_app"))
        self._content.grid(row=2, column=0, sticky="nsew")
        self._apply_responsive_layout(self.winfo_width())

    def _navigate(self, module: str):
        if module == self._current_module:
            return

        # Update sidebar active state
        for key, item in self._sidebar_items.items():
            item.set_active(key == module)

        # Destroy old view
        if self._current_view:
            self._current_view.destroy()
            self._current_view = None

        self._current_module = module

        # Labels
        labels = {
            "dashboard":  "Dashboard",
            "search": "Global Smart Search",
            "officers":   "Officers Management",
            "attendance": "Attendance Management",
            "leaves":     "Leave & Vacation Management",
            "accumulation": "Leave Accumulation Management",
            "duties":     "Daily Duty & Work Tracking",
            "meals":      "Meals / Feeding Log",
        }
        self._breadcrumb.configure(text=labels.get(module, module.title()))

        # Load view
        view = self._create_view(module)
        if view:
            view.pack(fill="both", expand=True)
            self._current_view = view

    def _create_view(self, module: str):
        try:
            if module == "dashboard":
                from ui.views.dashboard_view import DashboardView
                return DashboardView(self._content, self._svc)

            elif module == "officers":
                from ui.views.officers_view import OfficersView
                return OfficersView(self._content, self._svc)

            elif module == "search":
                from ui.views.search_view import SearchView
                return SearchView(self._content, self._svc)

            elif module == "attendance":
                from ui.views.module_views import AttendanceView
                return AttendanceView(self._content, self._svc)

            elif module == "leaves":
                from ui.views.module_views import LeaveView
                return LeaveView(self._content, self._svc)

            elif module == "duties":
                from ui.views.module_views import DutiesView
                return DutiesView(self._content, self._svc)

            elif module == "accumulation":
                from ui.views.accumulation_view import AccumulationView
                return AccumulationView(self._content, self._svc)

            elif module == "meals":
                from ui.views.module_views import MealsView
                return MealsView(self._content, self._svc)

        except Exception as e:
            logger.error(f"Error loading view '{module}': {e}", exc_info=True)
            err_frame = tk.Frame(self._content, bg=tm().c("bg_app"))
            tk.Label(err_frame, text=f"Error loading {module}:\n{e}",
                     bg=tm().c("bg_app"), fg=tm().c("danger"),
                     font=FONTS["body"], wraplength=600,
                     justify="center").pack(expand=True)
            return err_frame

    def _toggle_theme(self):
        tm().toggle()
        mode = tm().mode
        self._theme_btn.configure(
            text="☀  Light Mode" if mode == "dark" else "🌙  Dark Mode")

    def _toggle_sidebar(self):
        self._compact_sidebar = not self._compact_sidebar
        self._apply_sidebar_mode(self._compact_sidebar)

    def _on_resize(self, event):
        if event.widget is self:
            self._apply_responsive_layout(event.width)

    def _apply_responsive_layout(self, width: int):
        compact = width < 1100
        self._apply_sidebar_mode(compact)
        if width < 860:
            self._breadcrumb.configure(font=FONTS["body_bold"])
        else:
            self._breadcrumb.configure(font=FONTS["heading"])

    def _apply_sidebar_mode(self, compact: bool):
        self._compact_sidebar = compact
        target_width = 84 if compact else 240
        self._sidebar.configure(width=target_width)
        for item in self._sidebar_items.values():
            item.set_compact(compact)
        self._theme_btn.configure(text="☀" if tm().mode == "dark" and compact else (
            "🌙" if tm().mode == "light" and compact else (
                "☀  Light Mode" if tm().mode == "dark" else "🌙  Dark Mode"
            )
        ))

    def _retheme(self):
        t = tm()
        self.configure(bg=t.c("bg_app"))
        self._sidebar.configure(bg=t.c("bg_sidebar"))
        self._header.configure(bg=t.c("bg_header"))
        self._breadcrumb.configure(bg=t.c("bg_header"), fg=t.c("text_header"))
        self._clock_lbl.configure(bg=t.c("bg_header"))
        self._content.configure(bg=t.c("bg_app"))
        self._configure_styles()
        self._apply_sidebar_mode(self._compact_sidebar)
        # Reload current view
        if self._current_module:
            mod = self._current_module
            self._current_module = None
            self._navigate(mod)

    def _update_clock(self):
        now = datetime.now().strftime("%a  %d %b %Y   %H:%M:%S")
        self._clock_lbl.configure(text=now)
        self.after(1000, self._update_clock)
