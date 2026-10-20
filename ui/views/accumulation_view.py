"""
Leave Accumulation View
Officers Affairs Management System
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import ThemeManager, FONTS
from ui.components.widgets import (
    Button, Card, DataTable, SearchBar, LabeledEntry,
    LabeledCombo, LabeledText, confirm_dialog, info_dialog
)
from models.models import LeaveAccumulationRequest

tm = ThemeManager.get


# ======================================================================
# Leave Accumulation View
# ======================================================================

class AccumulationView(tk.Frame):
    """Leave accumulation request management and balance tracking."""
    
    MODULE_TITLE = "Leave Accumulation"
    TABLE_COLUMNS = [
        ("ID", 70), ("Officer #", 90), ("Name", 140), ("Days Requested", 100),
        ("Reason", 150), ("Status", 90), ("Reviewed By", 100), ("Request Date", 120),
    ]

    def __init__(self, parent, services, **kw):
        t = tm()
        super().__init__(parent, bg=t.c("bg_app"), **kw)
        self._svc = services
        self._selected_id = None
        self._build_header()
        self._build_toolbar()
        self._build_filters()
        self._build_balance_panel()
        self._build_table()
        self.load()

    def _build_header(self):
        t = tm()
        hdr = tk.Frame(self, bg=t.c("bg_app"))
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(hdr, text=self.MODULE_TITLE, bg=t.c("bg_app"),
                 fg=t.c("text_primary"), font=FONTS["title"]).pack(side="left")

    def _build_toolbar(self):
        t = tm()
        self._toolbar = tk.Frame(self, bg=t.c("bg_app"))
        self._toolbar.pack(fill="x", padx=24, pady=(0, 8))
        Button(self._toolbar, "＋ New Request", command=self._add, style="primary").pack(side="left", padx=(0, 4))
        Button(self._toolbar, "✎ Edit", command=self._edit, style="ghost").pack(side="left", padx=4)
        Button(self._toolbar, "🗑 Delete", command=self._delete, style="danger").pack(side="left", padx=4)
        Button(self._toolbar, "✔ Approve", command=self._approve, style="success").pack(side="left", padx=4)
        Button(self._toolbar, "✖ Reject", command=self._reject, style="danger").pack(side="left", padx=4)

    def _build_filters(self):
        t = tm()
        self._flt = tk.Frame(self, bg=t.c("bg_app"))
        self._flt.pack(fill="x", padx=24, pady=(0, 6))
        self._search = SearchBar(self._flt, on_search=lambda _: self.load())
        self._search.pack(side="left")
        self._summary_lbl = tk.Label(self._flt, text="", bg=t.c("bg_app"),
                                      fg=t.c("text_muted"), font=FONTS["small"])
        self._summary_lbl.pack(side="right")

        tk.Label(self._flt, text="Status:", bg=t.c("bg_app"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(12, 4))
        self._status_var = tk.StringVar(value="All")
        ttk.Combobox(self._flt, textvariable=self._status_var,
                     values=["All", "Pending", "Approved", "Rejected"],
                     state="readonly", width=10,
                     font=FONTS["input"]).pack(side="left")
        self._status_var.trace_add("write", lambda *_: self.load())
        tk.Label(self._flt, text="Officer:", bg=t.c("bg_app"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(8, 4))
        self._officer_var = tk.StringVar(value="All")
        officers = self._svc.officers.get_all_simple()
        self._officer_map = {f"{n} ({num})": oid for oid, num, n in officers}
        officer_values = ["All"] + list(self._officer_map.keys())
        ttk.Combobox(self._flt, textvariable=self._officer_var,
                     values=officer_values, state="readonly", width=26,
                     font=FONTS["input"]).pack(side="left")
        self._officer_var.trace_add("write", lambda *_: self.load())

    def _build_balance_panel(self):
        t = tm()
        panel = tk.Frame(self, bg=t.c("bg_app"))
        panel.pack(fill="x", padx=24, pady=(0, 12))
        
        # Summary stats
        stats_frame = tk.Frame(panel, bg=t.c("bg_card"),
                               highlightbackground=t.c("border"),
                               highlightthickness=1)
        stats_frame.pack(fill="x")
        
        # Stats display
        inner = tk.Frame(stats_frame, bg=t.c("bg_card"))
        inner.pack(fill="x", padx=16, pady=12)
        
        self._balance_earned = tk.Label(inner, text="Earned: 0 days",
                                         bg=t.c("bg_card"), fg="#22c55e",
                                         font=FONTS["body"])
        self._balance_earned.pack(side="left", padx=(0, 20))
        
        self._balance_used = tk.Label(inner, text="Used: 0 days",
                                       bg=t.c("bg_card"), fg="#ef4444",
                                       font=FONTS["body"])
        self._balance_used.pack(side="left", padx=(0, 20))
        
        self._balance_available = tk.Label(inner, text="Available: 0 days",
                                            bg=t.c("bg_card"), fg="#3b82f6",
                                            font=FONTS["heading"])
        self._balance_available.pack(side="left")

    def _build_table(self):
        self._table = DataTable(self, columns=self.TABLE_COLUMNS,
                                 on_select=self._on_select)
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 12))

    def _on_select(self, rid):
        self._selected_id = rid

    def load(self):
        status = self._status_var.get() if hasattr(self, "_status_var") else "All"
        search = self._search.get() if hasattr(self, "_search") else None
        records = self._svc.accumulation.get_all(
            officer_id=self._officer_map.get(self._officer_var.get()) if self._officer_var.get() != "All" else None,
            status=None if status == "All" else status,
            search=search or None)
        rows = [(r.id, r.officer_number, r.officer_name, r.requested_days,
                 r.request_reason, r.approval_status, r.approved_by, r.request_date) for r in records]
        self._table.populate(rows)
        self._summary_lbl.configure(text=f"{len(rows)} requests")
        
        # Update balance display
        agg_balance = self._svc.accumulation.get_aggregate_balance()
        self._balance_earned.configure(text=f"Earned: {agg_balance['total_earned']} days")
        self._balance_used.configure(text=f"Used: {agg_balance['total_used']} days")
        self._balance_available.configure(text=f"Available: {agg_balance['available']} days")

    def _add(self):
        AccumulationFormDialog(self, self._svc, on_save=self.load)

    def _edit(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Select a request.")
            return
        rec = self._svc.accumulation.get_by_id(self._selected_id)
        if rec:
            AccumulationFormDialog(self, self._svc, record=rec, on_save=self.load)

    def _delete(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Select a request to delete.")
            return
        if confirm_dialog(self, "Confirm Delete", "Delete this accumulation request?"):
            ok, msg = self._svc.accumulation.delete(self._selected_id)
            info_dialog(self, "Result", msg)
            self._selected_id = None
            self.load()

    def _approve(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Select a request to approve.")
            return
        ok, msg = self._svc.accumulation.approve(self._selected_id)
        info_dialog(self, "Result", msg)
        self.load()

    def _reject(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Select a request to reject.")
            return
        ok, msg = self._svc.accumulation.reject(self._selected_id)
        info_dialog(self, "Result", msg)
        self.load()


class AccumulationFormDialog(tk.Toplevel):
    def __init__(self, parent, services, record: LeaveAccumulationRequest = None, on_save=None):
        super().__init__(parent)
        self._svc = services
        self._rec = record or LeaveAccumulationRequest()
        self._on_save = on_save
        self._is_edit = bool(record and record.id)
        self.title("Edit Accumulation Request" if self._is_edit else "New Accumulation Request")
        self.configure(bg=tm().c("bg_dialog"))
        self.geometry("520x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._populate()

    def _build(self):
        t = tm()
        tk.Label(self, text="Leave Accumulation Request", bg=t.c("bg_dialog"),
                 fg=t.c("text_primary"), font=FONTS["subtitle"]).pack(pady=(16, 8))
        ttk.Separator(self).pack(fill="x", padx=16)

        form = tk.Frame(self, bg=t.c("bg_dialog"))
        form.pack(padx=24, pady=12, fill="both")
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        officers = self._svc.officers.get_all_simple()
        onames = [f"{n} ({num})" for _, num, n in officers]
        self._officer_map = {f"{n} ({num})": oid for oid, num, n in officers}

        self._f_officer = LabeledCombo(form, "Officer", onames, required=True)
        self._f_days = LabeledEntry(form, "Requested Days", required=True)
        self._f_reason = LabeledText(form, "Reason / Justification", height=4)
        self._f_status = LabeledCombo(form, "Status", ["Pending", "Approved", "Rejected"])
        self._f_notes = LabeledText(form, "Notes", height=2)

        self._f_officer.grid(row=0, column=0, columnspan=2, padx=8, pady=6, sticky="ew")
        self._f_days.grid(row=1, column=0, columnspan=2, padx=8, pady=6, sticky="ew")
        self._f_reason.grid(row=2, column=0, columnspan=2, padx=8, pady=6, sticky="ew")
        self._f_status.grid(row=3, column=0, columnspan=2, padx=8, pady=6, sticky="ew")
        self._f_notes.grid(row=4, column=0, columnspan=2, padx=8, pady=6, sticky="ew")

        btn = tk.Frame(self, bg=t.c("bg_dialog"))
        btn.pack(pady=12)
        Button(btn, "💾 Save", command=self._save, style="primary").pack(side="left", padx=8)
        Button(btn, "Cancel", command=self.destroy, style="ghost").pack(side="left")

    def _populate(self):
        r = self._rec
        if r.officer_id:
            for oid, num, n in self._svc.officers.get_all_simple():
                if oid == r.officer_id:
                    self._f_officer.value = f"{n} ({num})"
                    break
        self._f_days.value = str(r.requested_days) if r.requested_days else ""
        self._f_reason.value = r.request_reason
        self._f_status.value = r.approval_status or "Pending"
        self._f_notes.value = r.notes

    def _save(self):
        r = self._rec
        okey = self._f_officer.value
        r.officer_id = self._officer_map.get(okey, 0)
        try:
            r.requested_days = int(self._f_days.value)
        except ValueError:
            info_dialog(self, "Error", "Requested days must be a number.")
            return
        r.request_reason = self._f_reason.value
        r.approval_status = self._f_status.value
        r.notes = self._f_notes.value
        
        ok, msg = self._svc.accumulation.save(r)
        info_dialog(self, "Result", msg)
        if ok:
            if self._on_save:
                self._on_save()
            self.destroy()
