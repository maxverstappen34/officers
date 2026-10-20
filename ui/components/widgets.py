"""
UI Components - Officers Affairs Management System
Reusable, themed widgets built on top of tkinter.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional, Tuple
import sys
import os

# Make sure imports work regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.theme import ThemeManager, FONTS, STATUS_BADGE

tm = ThemeManager.get


# ───────────────────────────────────────────────
# Themed base frame
# ───────────────────────────────────────────────

class ThemedFrame(tk.Frame):
    def __init__(self, parent, bg_key="bg_card", **kw):
        super().__init__(parent, bg=tm().c(bg_key), **kw)
        tm().on_change(lambda: self.configure(bg=tm().c(bg_key)))


class ThemedLabel(tk.Label):
    def __init__(self, parent, text="", fg_key="text_primary",
                 bg_key="bg_card", font_key="body", **kw):
        super().__init__(parent, text=text,
                         fg=tm().c(fg_key), bg=tm().c(bg_key),
                         font=FONTS[font_key], **kw)


# ───────────────────────────────────────────────
# Card
# ───────────────────────────────────────────────

class Card(tk.Frame):
    def __init__(self, parent, title: str = "", **kw):
        t = tm()
        super().__init__(parent, bg=t.c("bg_card"),
                         highlightbackground=t.c("border"),
                         highlightthickness=1, bd=0, **kw)
        self.configure(padx=2, pady=2)
        if title:
            tk.Label(self, text=title, bg=t.c("bg_card"),
                     fg=t.c("text_primary"), font=FONTS["heading"],
                     anchor="w").pack(fill="x", padx=12, pady=(10, 6))
            ttk.Separator(self, orient="horizontal").pack(fill="x", padx=8)

        def _retheme():
            self.configure(bg=tm().c("bg_card"),
                            highlightbackground=tm().c("border"))
        tm().on_change(_retheme)


# ───────────────────────────────────────────────
# Stat Card (for dashboard)
# ───────────────────────────────────────────────

class StatCard(tk.Frame):
    def __init__(self, parent, title: str, value: str,
                 icon: str = "●", accent: str = "#2563eb", **kw):
        t = tm()
        super().__init__(parent, bg=t.c("bg_card"),
                         highlightbackground=t.c("border"),
                         highlightthickness=1, **kw)
        self.configure(padx=16, pady=14)

        # Icon stripe on left
        stripe = tk.Frame(self, width=5, bg=accent)
        stripe.pack(side="left", fill="y", padx=(0, 12))

        body = tk.Frame(self, bg=t.c("bg_card"))
        body.pack(side="left", fill="both", expand=True)

        self._val_label = tk.Label(body, text=value, bg=t.c("bg_card"),
                                    fg=accent, font=FONTS["stat"])
        self._val_label.pack(anchor="w")
        tk.Label(body, text=title, bg=t.c("bg_card"),
                 fg=t.c("text_secondary"), font=FONTS["stat_lbl"]).pack(anchor="w")

        def _rt():
            self.configure(bg=tm().c("bg_card"), highlightbackground=tm().c("border"))
            body.configure(bg=tm().c("bg_card"))
            self._val_label.configure(bg=tm().c("bg_card"))
        tm().on_change(_rt)

    def set_value(self, value: str):
        self._val_label.configure(text=value)


# ───────────────────────────────────────────────
# Modern Button
# ───────────────────────────────────────────────

class Button(tk.Label):
    """Flat button with hover and click effects."""

    def __init__(self, parent, text: str, command: Callable = None,
                 style: str = "primary", icon: str = "", **kw):
        t = tm()
        styles = {
            "primary": (t.c("accent"),       "#ffffff"),
            "success": (t.c("success"),       "#ffffff"),
            "danger":  (t.c("danger"),        "#ffffff"),
            "warning": (t.c("warning"),       "#ffffff"),
            "ghost":   (t.c("bg_hover"),      t.c("text_primary")),
            "outline": (t.c("bg_card"),       t.c("accent")),
        }
        self._bg, self._fg = styles.get(style, styles["primary"])
        self._hover_bg = t.c("accent_hover") if style == "primary" else (
            "#16a34a" if style == "success" else (
                "#dc2626" if style == "danger" else (
                    "#d97706" if style == "warning" else t.c("accent_light")
                )
            )
        )
        self._command = command
        self._style   = style
        label_text = f"{icon}  {text}" if icon else text
        super().__init__(parent, text=label_text, bg=self._bg, fg=self._fg,
                         font=FONTS["btn"], cursor="hand2",
                         padx=14, pady=8, bd=0, relief="flat", **kw)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>",    self._on_enter)
        self.bind("<Leave>",    self._on_leave)

    def _on_click(self, _):
        if self._command:
            self._command()

    def _on_enter(self, _):
        self.configure(bg=self._hover_bg)

    def _on_leave(self, _):
        self.configure(bg=self._bg)


# ───────────────────────────────────────────────
# LabeledEntry
# ───────────────────────────────────────────────

class LabeledEntry(tk.Frame):
    def __init__(self, parent, label: str, required: bool = False,
                 placeholder: str = "", width: int = 30, **kw):
        t = tm()
        super().__init__(parent, bg=t.c("bg_dialog"), **kw)
        lbl_text = f"{label} *" if required else label
        tk.Label(self, text=lbl_text, bg=t.c("bg_dialog"),
                 fg=t.c("text_secondary"), font=FONTS["small"],
                 anchor="w").pack(fill="x")
        self._var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self._var,
                               font=FONTS["input"], width=width,
                               bg=t.c("bg_input"), fg=t.c("text_primary"),
                               insertbackground=t.c("text_primary"),
                               relief="solid", bd=1,
                               highlightthickness=1,
                               highlightcolor=t.c("accent"),
                               highlightbackground=t.c("border_input"))
        self.entry.pack(fill="x", ipady=5)

    @property
    def value(self) -> str:
        return self._var.get().strip()

    @value.setter
    def value(self, v: str):
        self._var.set(v or "")


class LabeledCombo(tk.Frame):
    def __init__(self, parent, label: str, values: List[str],
                 required: bool = False, width: int = 28, **kw):
        t = tm()
        super().__init__(parent, bg=t.c("bg_dialog"), **kw)
        lbl_text = f"{label} *" if required else label
        tk.Label(self, text=lbl_text, bg=t.c("bg_dialog"),
                 fg=t.c("text_secondary"), font=FONTS["small"],
                 anchor="w").pack(fill="x")
        self._var = tk.StringVar()
        self.combo = ttk.Combobox(self, textvariable=self._var,
                                   values=values, state="readonly",
                                   font=FONTS["input"], width=width)
        self.combo.pack(fill="x", ipady=3)

    @property
    def value(self) -> str:
        return self._var.get()

    @value.setter
    def value(self, v: str):
        self._var.set(v or "")


class LabeledText(tk.Frame):
    def __init__(self, parent, label: str, height: int = 4, **kw):
        t = tm()
        super().__init__(parent, bg=t.c("bg_dialog"), **kw)
        tk.Label(self, text=label, bg=t.c("bg_dialog"),
                 fg=t.c("text_secondary"), font=FONTS["small"],
                 anchor="w").pack(fill="x")
        self.text = tk.Text(self, height=height, font=FONTS["input"],
                             bg=t.c("bg_input"), fg=t.c("text_primary"),
                             insertbackground=t.c("text_primary"),
                             relief="solid", bd=1, wrap="word")
        self.text.pack(fill="x")

    @property
    def value(self) -> str:
        return self.text.get("1.0", "end-1c").strip()

    @value.setter
    def value(self, v: str):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", v or "")


# ───────────────────────────────────────────────
# StatusBadge
# ───────────────────────────────────────────────

class StatusBadge(tk.Label):
    def __init__(self, parent, status: str, **kw):
        fg, bg = STATUS_BADGE.get(status, ("#ffffff", "#6b7280"))
        super().__init__(parent, text=f"  {status}  ",
                         bg=bg, fg=fg, font=FONTS["badge"],
                         relief="flat", **kw)


# ───────────────────────────────────────────────
# SearchBar
# ───────────────────────────────────────────────

class SearchBar(tk.Frame):
    def __init__(self, parent, on_search: Callable, placeholder: str = "Search…", **kw):
        t = tm()
        super().__init__(parent, bg=t.c("bg_header"), **kw)
        self._var = tk.StringVar()
        self._var.trace_add("write", lambda *_: on_search(self._var.get()))
        tk.Label(self, text="🔍", bg=t.c("bg_header"),
                 fg=t.c("text_secondary"), font=FONTS["body"]).pack(side="left", padx=(0, 4))
        self._entry = tk.Entry(self, textvariable=self._var,
                                font=FONTS["input"],
                                bg=t.c("bg_input"), fg=t.c("text_primary"),
                                insertbackground=t.c("text_primary"),
                                relief="solid", bd=1,
                                highlightthickness=1,
                                highlightcolor=t.c("accent"),
                                highlightbackground=t.c("border_input"))
        self._entry.pack(side="left", fill="x", expand=True, ipady=5)

    def get(self) -> str:
        return self._var.get()

    def clear(self):
        self._var.set("")


# ───────────────────────────────────────────────
# DataTable (Treeview wrapper)
# ───────────────────────────────────────────────

class DataTable(tk.Frame):
    def __init__(self, parent, columns: List[Tuple[str, int]],
                 on_select: Callable = None, on_double_click: Callable = None,
                 **kw):
        t = tm()
        super().__init__(parent, bg=t.c("bg_table"), **kw)

        # Style Treeview
        style = ttk.Style()
        style.configure("OA.Treeview",
                         background=t.c("bg_table"),
                         fieldbackground=t.c("bg_table"),
                         foreground=t.c("text_primary"),
                        rowheight=32,
                         font=FONTS["table"])
        style.configure("OA.Treeview.Heading",
                         background=t.c("table_header_bg"),
                         foreground=t.c("table_header_text"),
                         font=FONTS["table_hdr"],
                         relief="flat")
        style.map("OA.Treeview",
                  background=[("selected", t.c("bg_selected"))],
                  foreground=[("selected", t.c("text_primary"))])
        style.map("OA.Treeview.Heading",
                  background=[("active", t.c("table_header_bg"))])

        col_ids = [c[0] for c in columns]
        self.tree = ttk.Treeview(self, columns=col_ids, show="headings",
                                  style="OA.Treeview", selectmode="browse")

        for col_id, width in columns:
            self.tree.heading(col_id, text=col_id,
                               command=lambda c=col_id: self._sort(c))
            self.tree.column(col_id, width=width, minwidth=50,
                             anchor="center", stretch=True)

        # Scrollbars
        vsb = ttk.Scrollbar(self, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        if on_select:
            self.tree.bind("<<TreeviewSelect>>", lambda _: on_select(self.selected_id()))
        if on_double_click:
            self.tree.bind("<Double-1>", lambda _: on_double_click(self.selected_id()))

        self._sort_col = None
        self._sort_rev = False

        # Alternating rows
        self.tree.tag_configure("alt", background=t.c("bg_table_alt"))

    def populate(self, rows: List[tuple], id_col: bool = True):
        """rows: list of tuples. First element assumed to be the record id (hidden)."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, row in enumerate(rows):
            tag = "alt" if i % 2 == 1 else ""
            if id_col:
                self.tree.insert("", "end", iid=str(row[0]),
                                  values=row[1:], tags=(tag,))
            else:
                self.tree.insert("", "end", values=row, tags=(tag,))

    def selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if sel:
            try:
                return int(sel[0])
            except ValueError:
                return None
        return None

    def selected_values(self) -> Optional[tuple]:
        sel = self.tree.selection()
        if sel:
            return self.tree.item(sel[0], "values")
        return None

    def _sort(self, col: str):
        data = [(self.tree.set(iid, col), iid) for iid in self.tree.get_children()]
        reverse = (col == self._sort_col and not self._sort_rev)
        data.sort(key=lambda x: x[0].lower() if isinstance(x[0], str) else x[0],
                  reverse=reverse)
        for idx, (_, iid) in enumerate(data):
            self.tree.move(iid, "", idx)
        self._sort_col = col
        self._sort_rev = reverse


# ───────────────────────────────────────────────
# Confirmation Dialog
# ───────────────────────────────────────────────

def confirm_dialog(parent, title: str, message: str) -> bool:
    result = [False]
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.configure(bg=tm().c("bg_dialog"))
    w = max(360, min(520, int(parent.winfo_width() * 0.45)))
    h = 180
    x = parent.winfo_rootx() + max(0, (parent.winfo_width() - w) // 2)
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - h) // 2)
    dlg.geometry(f"{w}x{h}+{x}+{y}")
    dlg.resizable(True, False)
    dlg.transient(parent)
    dlg.grab_set()

    tk.Label(dlg, text=message, bg=tm().c("bg_dialog"),
             fg=tm().c("text_primary"), font=FONTS["body"],
             wraplength=340, justify="center").pack(pady=24)

    btn_frame = tk.Frame(dlg, bg=tm().c("bg_dialog"))
    btn_frame.pack()

    def _yes():
        result[0] = True
        dlg.destroy()

    Button(btn_frame, "Confirm", command=_yes, style="danger").pack(side="left", padx=8)
    Button(btn_frame, "Cancel", command=dlg.destroy, style="ghost").pack(side="left", padx=8)
    dlg.bind("<Return>", lambda *_: _yes())
    dlg.bind("<Escape>", lambda *_: dlg.destroy())

    parent.wait_window(dlg)
    return result[0]


def info_dialog(parent, title: str, message: str):
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.configure(bg=tm().c("bg_dialog"))
    w = max(360, min(520, int(parent.winfo_width() * 0.45)))
    h = 170
    x = parent.winfo_rootx() + max(0, (parent.winfo_width() - w) // 2)
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - h) // 2)
    dlg.geometry(f"{w}x{h}+{x}+{y}")
    dlg.resizable(True, False)
    dlg.transient(parent)
    dlg.grab_set()
    tk.Label(dlg, text=message, bg=tm().c("bg_dialog"),
             fg=tm().c("text_primary"), font=FONTS["body"],
             wraplength=340, justify="center").pack(pady=28)
    Button(dlg, "OK", command=dlg.destroy, style="primary").pack()
    dlg.bind("<Return>", lambda *_: dlg.destroy())
    dlg.bind("<Escape>", lambda *_: dlg.destroy())
    parent.wait_window(dlg)


# ───────────────────────────────────────────────
# Pagination bar
# ───────────────────────────────────────────────

class PaginationBar(tk.Frame):
    def __init__(self, parent, on_page_change: Callable, **kw):
        t = tm()
        super().__init__(parent, bg=t.c("bg_card"), **kw)
        self._page = 1
        self._total_pages = 1
        self._cb = on_page_change

        Button(self, "◀", command=self._prev, style="ghost").pack(side="left", padx=2)
        self._label = tk.Label(self, text="Page 1 / 1",
                                bg=t.c("bg_card"), fg=t.c("text_secondary"),
                                font=FONTS["small"])
        self._label.pack(side="left", padx=8)
        Button(self, "▶", command=self._next, style="ghost").pack(side="left", padx=2)

    def update_info(self, page: int, total_pages: int, total_records: int):
        self._page = page
        self._total_pages = total_pages
        self._label.configure(
            text=f"Page {page} / {total_pages}  ({total_records} records)")

    def _prev(self):
        if self._page > 1:
            self._page -= 1
            self._cb(self._page)

    def _next(self):
        if self._page < self._total_pages:
            self._page += 1
            self._cb(self._page)
