"""
Global Search View
Fast, intelligent cross-module search with filters and suggestions.
"""

import tkinter as tk
from tkinter import ttk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import ThemeManager, FONTS
from ui.components.widgets import Button, DataTable

tm = ThemeManager.get


class SearchView(tk.Frame):
    MODULE_TITLE = "Global Smart Search"

    def __init__(self, parent, services, **kw):
        super().__init__(parent, bg=tm().c("bg_app"), **kw)
        self._svc = services
        self._suggestions = []
        self._debounce = None
        self._build()
        self._run_search()

    def _build(self):
        t = tm()
        hdr = tk.Frame(self, bg=t.c("bg_app"))
        hdr.pack(fill="x", padx=24, pady=(18, 8))
        tk.Label(hdr, text=self.MODULE_TITLE, bg=t.c("bg_app"),
                 fg=t.c("text_primary"), font=FONTS["title"]).pack(side="left")
        tk.Label(hdr, text="Search officers, records, penalties, appeals, leaves, dates, status",
                 bg=t.c("bg_app"), fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="right", pady=6)

        top = tk.Frame(self, bg=t.c("bg_app"))
        top.pack(fill="x", padx=24, pady=(0, 8))

        self._q_var = tk.StringVar()
        self._q_var.trace_add("write", lambda *_: self._on_query_change())
        self._entry = tk.Entry(top, textvariable=self._q_var, font=FONTS["input"],
                               bg=t.c("bg_input"), fg=t.c("text_primary"),
                               insertbackground=t.c("text_primary"),
                               relief="solid", bd=1, highlightthickness=1,
                               highlightbackground=t.c("border_input"),
                               highlightcolor=t.c("accent"))
        self._entry.pack(side="left", fill="x", expand=True, ipady=8)
        self._entry.bind("<Return>", lambda *_: self._run_search())

        Button(top, "Search", command=self._run_search, style="primary").pack(side="left", padx=(8, 0))
        Button(top, "Clear", command=self._clear, style="ghost").pack(side="left", padx=(6, 0))

        self._sugg_list = tk.Listbox(self, height=6, font=FONTS["small"],
                                     bg=t.c("bg_card"), fg=t.c("text_primary"),
                                     relief="solid", bd=1, highlightthickness=1,
                                     highlightbackground=t.c("border"))
        self._sugg_list.bind("<<ListboxSelect>>", self._pick_suggestion)

        flt = tk.Frame(self, bg=t.c("bg_app"))
        flt.pack(fill="x", padx=24, pady=(0, 10))
        tk.Label(flt, text="Category", bg=t.c("bg_app"), fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(0, 6))
        self._category = tk.StringVar(value="All")
        ttk.Combobox(flt, textvariable=self._category, state="readonly", width=14,
                     values=["All", "Officers", "Leaves", "Accumulation", "Penalties", "Appeals"]).pack(side="left", padx=(0, 12))
        self._category.trace_add("write", lambda *_: self._run_search())

        tk.Label(flt, text="Status", bg=t.c("bg_app"), fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(0, 6))
        self._status = tk.StringVar(value="")
        ttk.Combobox(flt, textvariable=self._status, width=14, values=["", "Pending", "Approved", "Rejected", "Active", "On Leave", "Suspended", "Retired", "Issued", "In Effect", "Resolved"]).pack(side="left", padx=(0, 12))

        tk.Label(flt, text="Department", bg=t.c("bg_app"), fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(0, 6))
        self._dept_map = {}
        depts = self._svc.reference.get_departments()
        dept_values = ["All"]
        for d in depts:
            dept_values.append(d.name)
            self._dept_map[d.name] = d.id
        self._dept = tk.StringVar(value="All")
        ttk.Combobox(flt, textvariable=self._dept, state="readonly", width=18, values=dept_values).pack(side="left", padx=(0, 12))

        tk.Label(flt, text="From", bg=t.c("bg_app"), fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(0, 6))
        self._date_from = tk.StringVar(value="")
        tk.Entry(flt, textvariable=self._date_from, width=12, font=FONTS["small"],
                 bg=t.c("bg_input"), fg=t.c("text_primary"), relief="solid", bd=1).pack(side="left", padx=(0, 8))
        tk.Label(flt, text="To", bg=t.c("bg_app"), fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(0, 6))
        self._date_to = tk.StringVar(value="")
        tk.Entry(flt, textvariable=self._date_to, width=12, font=FONTS["small"],
                 bg=t.c("bg_input"), fg=t.c("text_primary"), relief="solid", bd=1).pack(side="left", padx=(0, 8))

        Button(flt, "Apply Filters", command=self._run_search, style="ghost").pack(side="left")

        self._summary = tk.Label(self, text="", bg=t.c("bg_app"), fg=t.c("text_muted"), font=FONTS["small"])
        self._summary.pack(fill="x", padx=24, pady=(0, 6), anchor="w")

        cols = [("No", 60), ("Category", 120), ("Title", 210), ("Status", 120), ("Date", 120), ("Department", 160), ("Match Context", 420)]
        self._empty_lbl = tk.Label(self, text="", bg=t.c("bg_app"), fg=t.c("text_muted"), font=FONTS["body"])
        self._empty_lbl.pack(fill="x", padx=24, pady=(0, 6), anchor="w")

        self._table = DataTable(self, columns=cols)
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 12))

    def _filters(self):
        dept_name = self._dept.get()
        return {
            "category": self._category.get() or "All",
            "status": self._status.get() or "",
            "department_id": None if dept_name == "All" else self._dept_map.get(dept_name),
            "date_from": self._date_from.get().strip(),
            "date_to": self._date_to.get().strip(),
        }

    def _on_query_change(self):
        if self._debounce:
            self.after_cancel(self._debounce)
        self._debounce = self.after(180, self._load_suggestions)

    def _load_suggestions(self):
        q = self._q_var.get().strip()
        if len(q) < 2:
            self._sugg_list.place_forget()
            return
        self._suggestions = self._svc.search.suggestions(q, self._filters(), limit=8)
        self._sugg_list.delete(0, "end")
        for s in self._suggestions:
            self._sugg_list.insert("end", s)
        if self._suggestions:
            x = self._entry.winfo_rootx() - self.winfo_rootx()
            y = self._entry.winfo_rooty() - self.winfo_rooty() + self._entry.winfo_height() + 2
            self._sugg_list.place(x=x, y=y, width=self._entry.winfo_width(), height=150)
        else:
            self._sugg_list.place_forget()

    def _pick_suggestion(self, _):
        sel = self._sugg_list.curselection()
        if not sel:
            return
        txt = self._sugg_list.get(sel[0]).split("•")[0].strip()
        self._q_var.set(txt)
        self._sugg_list.place_forget()
        self._run_search()

    def _run_search(self):
        query = self._q_var.get().strip()
        rows = self._svc.search.search(query, self._filters(), limit=250)
        table_rows = []
        for i, r in enumerate(rows, 1):
            table_rows.append((
                i,
                r.get("category", ""),
                r.get("title_h", ""),
                r.get("status", ""),
                r.get("date_value", ""),
                r.get("department", ""),
                r.get("snippet_h", ""),
            ))
        self._table.populate(table_rows, id_col=False)
        self._summary.configure(text=f"{len(rows)} results")
        if query and not rows:
            self._empty_lbl.configure(text="No matching records found. Try broader keywords or remove filters.")
        elif not query and not rows:
            self._empty_lbl.configure(text="Start typing to search across officers, leaves, penalties, appeals, and related records.")
        else:
            self._empty_lbl.configure(text="")
        self._sugg_list.place_forget()

    def _clear(self):
        self._q_var.set("")
        self._status.set("")
        self._category.set("All")
        self._dept.set("All")
        self._date_from.set("")
        self._date_to.set("")
        self._sugg_list.place_forget()
        self._run_search()
