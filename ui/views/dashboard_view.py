"""
Dashboard View - Officers Affairs Management System
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import ThemeManager, FONTS
from ui.components.widgets import StatCard, Card

tm = ThemeManager.get


class DashboardView(tk.Frame):
    def __init__(self, parent, services, **kw):
        t = tm()
        super().__init__(parent, bg=t.c("bg_app"), **kw)
        self._svc = services
        self._build()
        tm().on_change(self._retheme)

    def _build(self):
        t = tm()
        # Title bar
        title_bar = tk.Frame(self, bg=t.c("bg_app"))
        title_bar.pack(fill="x", padx=24, pady=(20, 0))
        tk.Label(title_bar, text="Dashboard",
                 bg=t.c("bg_app"), fg=t.c("text_primary"),
                 font=FONTS["title"]).pack(side="left")
        tk.Label(title_bar, text="Officers Affairs Management System",
                 bg=t.c("bg_app"), fg=t.c("text_secondary"),
                 font=FONTS["small"]).pack(side="right", pady=6)

        # Refresh button
        from ui.components.widgets import Button
        refresh_bar = tk.Frame(self, bg=t.c("bg_app"))
        refresh_bar.pack(fill="x", padx=24, pady=(4, 12))
        Button(refresh_bar, "↻  Refresh", command=self.refresh, style="ghost").pack(side="left")

        # Responsive demo controls
        sample_card = Card(self, title="Responsive UI Demo")
        sample_card.pack(fill="x", padx=24, pady=(0, 12))
        sample_frame = tk.Frame(sample_card, bg=t.c("bg_card"))
        sample_frame.pack(fill="both", expand=True, padx=12, pady=12)
        sample_frame.columnconfigure(1, weight=1)

        tk.Label(sample_frame, text="Search officers:", bg=t.c("bg_card"),
                 fg=t.c("text_secondary"), font=FONTS["body"]).grid(row=0, column=0, sticky="w")
        self._sample_search = tk.Entry(sample_frame, font=FONTS["input"],
                                       bg=t.c("bg_input"), fg=t.c("text_primary"))
        self._sample_search.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)

        tk.Label(sample_frame, text="Notes:", bg=t.c("bg_card"),
                 fg=t.c("text_secondary"), font=FONTS["body"]).grid(row=1, column=0, sticky="nw", pady=(8, 0))
        self._sample_text = tk.Text(sample_frame, height=4, font=FONTS["input"],
                                    bg=t.c("bg_input"), fg=t.c("text_primary"), wrap="word")
        self._sample_text.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))

        action_bar = tk.Frame(sample_frame, bg=t.c("bg_card"))
        action_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        Button(action_bar, "Save Note", style="primary", command=lambda: None).pack(side="left", padx=(0, 8))
        Button(action_bar, "Clear", style="ghost", command=lambda: self._sample_text.delete("1.0", "end")).pack(side="left")

        # Scrollable content
        canvas = tk.Canvas(self, bg=t.c("bg_app"), highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=0)

        self._scroll_frame = tk.Frame(canvas, bg=t.c("bg_app"))
        self._scroll_win = canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        self._scroll_frame.bind("<Configure>",
                                 lambda e: canvas.configure(
                                     scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", self._on_canvas_resize)

        self._canvas = canvas
        self._content = self._scroll_frame
        self._cards = []
        self.refresh()

    def refresh(self):
        for w in self._content.winfo_children():
            w.destroy()

        stats = self._svc.dashboard.get_stats()
        t = tm()

        # ── Stat cards row ──────────────────────────────────────────
        stat_grid = tk.Frame(self._content, bg=t.c("bg_app"))
        stat_grid.pack(fill="both", padx=24, pady=8, expand=True)
        self._stat_grid = stat_grid

        cards_data = [
            ("Total Officers",       str(stats["total_officers"]),   "#2563eb"),
            ("Active Officers",      str(stats["active_officers"]),  "#22c55e"),
            ("Present Today",        str(stats["present_today"]),    "#22c55e"),
            ("Absent Today",         str(stats["absent_today"]),     "#ef4444"),
            ("On Leave",             str(stats["on_leave"]),         "#3b82f6"),
            ("Duties Today",         str(stats["duties_today"]),     "#a855f7"),
            ("Pending Leaves",       str(stats["pending_leaves"]),   "#f59e0b"),
            ("Attendance Rate",      f"{stats['attendance_rate']}%","#22c55e"),
        ]
        self._cards = [StatCard(stat_grid, title=title, value=val, accent=accent)
                       for title, val, accent in cards_data]
        self._arrange_stat_cards()

        # ── Charts row ──────────────────────────────────────────────
        charts_row = tk.Frame(self._content, bg=t.c("bg_app"))
        charts_row.pack(fill="both", padx=24, pady=8, expand=True)
        charts_row.columnconfigure(0, weight=2)
        charts_row.columnconfigure(1, weight=1)

        # Department chart
        dept_card = Card(charts_row, title="Officers by Department")
        dept_card.grid(row=0, column=0, padx=(0, 6), pady=0, sticky="nsew")
        self._draw_bar_chart(dept_card, stats["dept_distribution"])

        # Status pie chart (simulated with colored rows)
        status_card = Card(charts_row, title="Status Distribution")
        status_card.grid(row=0, column=1, padx=(6, 0), pady=0, sticky="nsew")
        self._draw_status_dist(status_card, stats["status_distribution"])

        # ── Weekly attendance ───────────────────────────────────────
        weekly_card = Card(self._content, title="Weekly Attendance (Last 7 Days)")
        weekly_card.pack(fill="x", padx=24, pady=(8, 0))
        self._draw_weekly(weekly_card, stats["weekly_attendance"])

        # ── Recent Activity ─────────────────────────────────────────
        activity_card = Card(self._content, title="Recent Activity")
        activity_card.pack(fill="x", padx=24, pady=(8, 16))
        self._draw_activity(activity_card, stats["recent_activity"])

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._scroll_win, width=event.width)
        self._arrange_stat_cards(event.width)

    def _arrange_stat_cards(self, width: int = None):
        if not hasattr(self, '_cards') or not self._cards:
            return
        if width is None:
            width = self._content.winfo_width() or self._canvas.winfo_width()
        width = max(width, 320)
        columns = min(4, max(1, width // 280))

        for widget in self._stat_grid.winfo_children():
            widget.grid_forget()

        for idx, card in enumerate(self._cards):
            row = idx // columns
            col = idx % columns
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        for i in range(columns):
            self._stat_grid.columnconfigure(i, weight=1)

        for r in range((len(self._cards) + columns - 1) // columns):
            self._stat_grid.rowconfigure(r, weight=1)

    def _draw_bar_chart(self, parent, data):
        """Draw a simple horizontal bar chart."""
        t = tm()
        if not data:
            tk.Label(parent, text="No data", bg=t.c("bg_card"),
                     fg=t.c("text_muted"), font=FONTS["small"]).pack(pady=20)
            return
        frame = tk.Frame(parent, bg=t.c("bg_card"))
        frame.pack(fill="x", padx=12, pady=8)
        max_val = max(v for _, v in data) or 1
        colors = ["#2563eb","#22c55e","#f59e0b","#ef4444",
                  "#a855f7","#06b6d4","#10b981","#f97316"]
        for i, (name, val) in enumerate(data):
            row = tk.Frame(frame, bg=t.c("bg_card"))
            row.pack(fill="x", pady=2)
            tk.Label(row, text=name[:18], width=18, anchor="w",
                     bg=t.c("bg_card"), fg=t.c("text_secondary"),
                     font=FONTS["small"]).pack(side="left")
            bar_bg = tk.Frame(row, bg=t.c("border"), height=16)
            bar_bg.pack(side="left", fill="x", expand=True, padx=(4, 8))
            bar_width = max(int(200 * val / max_val), 4)
            tk.Frame(bar_bg, bg=colors[i % len(colors)],
                     width=bar_width, height=16).place(x=0, y=0)
            tk.Label(row, text=str(val), bg=t.c("bg_card"),
                     fg=t.c("text_secondary"), font=FONTS["small"],
                     width=4).pack(side="left")

    def _draw_status_dist(self, parent, data):
        t = tm()
        colors = {
            "Active":    "#22c55e",
            "On Leave":  "#3b82f6",
            "Suspended": "#f59e0b",
            "Retired":   "#6b7280",
        }
        frame = tk.Frame(parent, bg=t.c("bg_card"))
        frame.pack(fill="both", padx=12, pady=8)
        for status, cnt in data:
            row = tk.Frame(frame, bg=t.c("bg_card"))
            row.pack(fill="x", pady=3)
            dot = tk.Label(row, text="●", bg=t.c("bg_card"),
                           fg=colors.get(status, "#6b7280"), font=("Segoe UI", 14))
            dot.pack(side="left", padx=(0, 6))
            tk.Label(row, text=status, bg=t.c("bg_card"),
                     fg=t.c("text_primary"), font=FONTS["body"],
                     width=12, anchor="w").pack(side="left")
            tk.Label(row, text=str(cnt), bg=t.c("bg_card"),
                     fg=t.c("text_secondary"), font=FONTS["body_bold"]).pack(side="right")

    def _draw_weekly(self, parent, data):
        t = tm()
        if not data:
            tk.Label(parent, text="No attendance data this week",
                     bg=t.c("bg_card"), fg=t.c("text_muted"),
                     font=FONTS["small"]).pack(pady=12)
            return
        frame = tk.Frame(parent, bg=t.c("bg_card"))
        frame.pack(fill="x", padx=12, pady=8)
        # Header
        header = tk.Frame(frame, bg=t.c("bg_card"))
        header.pack(fill="x")
        for lbl, w in [("Date", 120), ("Present", 80), ("Late", 80),
                        ("Absent", 80), ("Total", 80)]:
            tk.Label(header, text=lbl, width=w//8, bg=t.c("bg_card"),
                     fg=t.c("text_secondary"), font=FONTS["small"],
                     anchor="center").pack(side="left", padx=4)
        ttk.Separator(frame).pack(fill="x", pady=4)
        for date, present, late, absent in data:
            row = tk.Frame(frame, bg=t.c("bg_card"))
            row.pack(fill="x", pady=1)
            for val, w, color in [
                (date, 15, t.c("text_primary")),
                (present, 10, "#22c55e"),
                (late, 10, "#f59e0b"),
                (absent, 10, "#ef4444"),
                (present + late + absent, 10, t.c("text_secondary")),
            ]:
                tk.Label(row, text=str(val), width=w, anchor="center",
                         bg=t.c("bg_card"), fg=color,
                         font=FONTS["small"]).pack(side="left", padx=4)

    def _draw_activity(self, parent, activities):
        t = tm()
        if not activities:
            tk.Label(parent, text="No recent activity",
                     bg=t.c("bg_card"), fg=t.c("text_muted"),
                     font=FONTS["small"]).pack(pady=12)
            return
        frame = tk.Frame(parent, bg=t.c("bg_card"))
        frame.pack(fill="x", padx=12, pady=8)
        action_colors = {"INSERT": "#22c55e", "UPDATE": "#3b82f6", "DELETE": "#ef4444"}
        for act in activities:
            row = tk.Frame(frame, bg=t.c("bg_card"))
            row.pack(fill="x", pady=2)
            color = action_colors.get(act.get("action",""), "#6b7280")
            tk.Label(row, text=f"[{act.get('action','')}]",
                     bg=t.c("bg_card"), fg=color,
                     font=FONTS["badge"], width=8).pack(side="left")
            table = act.get("table_name","").replace("_"," ").title()
            details = act.get("details","")
            tk.Label(row, text=f"{table}: {details}",
                     bg=t.c("bg_card"), fg=t.c("text_primary"),
                     font=FONTS["small"], anchor="w").pack(side="left", padx=8)
            tk.Label(row, text=act.get("timestamp","")[:16],
                     bg=t.c("bg_card"), fg=t.c("text_muted"),
                     font=FONTS["small"]).pack(side="right")

    def _retheme(self):
        self.configure(bg=tm().c("bg_app"))
        self.refresh()
