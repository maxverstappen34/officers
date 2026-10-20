"""
Attendance, Leave, Duties, and Meals Views
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
from models.models import AttendanceRecord, LeaveRequest, DailyDuty, MealRecord

tm = ThemeManager.get


# ======================================================================
# Base Module View (shared boilerplate)
# ======================================================================

class _BaseModuleView(tk.Frame):
    """Shared skeleton for all module views."""

    MODULE_TITLE    = "Module"
    TABLE_COLUMNS   = []

    def __init__(self, parent, services, **kw):
        t = tm()
        super().__init__(parent, bg=t.c("bg_app"), **kw)
        self._svc = services
        self._selected_id = None
        self._build_header()
        self._build_toolbar()
        self._build_filters()
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
        Button(self._toolbar, "＋ Add",    command=self._add,    style="primary").pack(side="left", padx=(0, 4))
        Button(self._toolbar, "✎ Edit",    command=self._edit,   style="ghost").pack(side="left", padx=4)
        Button(self._toolbar, "🗑 Delete", command=self._delete, style="danger").pack(side="left", padx=4)
        self._extra_toolbar_buttons()

    def _extra_toolbar_buttons(self): pass

    def _build_filters(self):
        t = tm()
        self._flt = tk.Frame(self, bg=t.c("bg_app"))
        self._flt.pack(fill="x", padx=24, pady=(0, 6))
        self._search = SearchBar(self._flt, on_search=lambda _: self.load())
        self._search.pack(side="left")
        self._summary_lbl = tk.Label(self._flt, text="", bg=t.c("bg_app"),
                                      fg=t.c("text_muted"), font=FONTS["small"])
        self._summary_lbl.pack(side="right")

    def _build_table(self):
        self._table = DataTable(self, columns=self.TABLE_COLUMNS,
                                 on_select=self._on_select)
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 12))

    def _on_select(self, rid): self._selected_id = rid
    def load(self): pass
    def _add(self): pass
    def _edit(self): pass

    def _delete(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Select a record to delete.")
            return
        if confirm_dialog(self, "Confirm Delete", "Delete this record?"):
            ok, msg = self._do_delete(self._selected_id)
            info_dialog(self, "Result", msg)
            self._selected_id = None
            self.load()

    def _do_delete(self, rid): return False, "Not implemented"


# ======================================================================
# ATTENDANCE VIEW
# ======================================================================

class AttendanceView(_BaseModuleView):
    MODULE_TITLE  = "Attendance Management"
    TABLE_COLUMNS = [
        ("ID",70),("Officer #",90),("Name",150),("Rank",110),
        ("Date",100),("Check-In",90),("Check-Out",90),("Status",90),
    ]

    def _build_filters(self):
        super()._build_filters()
        t = tm()
        tk.Label(self._flt, text="Date:", bg=t.c("bg_app"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(12, 4))
        self._date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        tk.Entry(self._flt, textvariable=self._date_var, width=12,
                 bg=tm().c("bg_input"), fg=tm().c("text_primary"),
                 font=FONTS["input"], relief="solid", bd=1).pack(side="left")
        Button(self._flt, "Filter", command=self.load, style="ghost").pack(side="left", padx=4)
        Button(self._flt, "Today",
               command=lambda: (self._date_var.set(datetime.now().strftime("%Y-%m-%d")), self.load()),
               style="ghost").pack(side="left", padx=4)

        tk.Label(self._flt, text="Status:", bg=t.c("bg_app"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(8, 4))
        self._status_var = tk.StringVar(value="All")
        ttk.Combobox(self._flt, textvariable=self._status_var,
                     values=["All","Present","Late","Absent","Leave"],
                     state="readonly", width=10, font=FONTS["input"]).pack(side="left")
        self._status_var.trace_add("write", lambda *_: self.load())

    def _extra_toolbar_buttons(self):
        Button(self._toolbar, "📊 Monthly Report",
               command=self._monthly_report, style="ghost").pack(side="left", padx=4)

    def load(self):
        date_f = self._date_var.get() if hasattr(self, "_date_var") else None
        status = self._status_var.get() if hasattr(self, "_status_var") else "All"
        search = self._search.get() if hasattr(self, "_search") else None
        records = self._svc.attendance.get_all(
            date_filter=date_f or None,
            status=None if status == "All" else status,
            search=search or None)
        rows = [(r.id, r.officer_number, r.officer_name, r.rank_name,
                 r.date, r.check_in, r.check_out, r.status) for r in records]
        self._table.populate(rows)
        self._summary_lbl.configure(text=f"{len(rows)} records")

    def _add(self):
        AttendanceFormDialog(self, self._svc, on_save=self.load)

    def _edit(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Select a record to edit.")
            return
        rec = self._svc.attendance.get_by_id(self._selected_id)
        if rec:
            AttendanceFormDialog(self, self._svc, record=rec, on_save=self.load)

    def _do_delete(self, rid):
        return self._svc.attendance.delete(rid)

    def _monthly_report(self):
        MonthlyAttendanceDialog(self, self._svc)



class AttendanceFormDialog(tk.Toplevel):
    def __init__(self, parent, services, record: AttendanceRecord = None, on_save=None):
        super().__init__(parent)
        self._svc = services
        self._rec = record or AttendanceRecord()
        self._on_save = on_save
        self._is_edit = bool(record and record.id)
        self.title("Edit Attendance" if self._is_edit else "Record Attendance")
        self.configure(bg=tm().c("bg_dialog"))
        self.geometry("500x460")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._populate()

    def _build(self):
        t = tm()
        tk.Label(self, text="Attendance Record",
                 bg=t.c("bg_dialog"), fg=t.c("text_primary"),
                 font=FONTS["subtitle"]).pack(pady=(16, 8))
        ttk.Separator(self).pack(fill="x", padx=16)

        form = tk.Frame(self, bg=t.c("bg_dialog"))
        form.pack(padx=24, pady=12, fill="both")
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        officers = self._svc.officers.get_all_simple()
        officer_names = [f"{n} ({num})" for _, num, n in officers]
        self._officer_map = {f"{n} ({num})": oid for oid, num, n in officers}

        self._f_officer  = LabeledCombo(form, "Officer", officer_names, required=True)
        self._f_date     = LabeledEntry(form, "Date (YYYY-MM-DD)", required=True)
        self._f_checkin  = LabeledEntry(form, "Check-In (HH:MM)")
        self._f_checkout = LabeledEntry(form, "Check-Out (HH:MM)")
        self._f_status   = LabeledCombo(form, "Status",
                                         ["Present","Late","Absent","Leave"], required=True)
        self._f_notes    = LabeledText(form, "Notes", height=3)

        self._f_officer.grid(row=0, column=0, columnspan=2, padx=8, pady=6, sticky="ew")
        self._f_date.grid(row=1, column=0, padx=8, pady=6, sticky="ew")
        self._f_status.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
        self._f_checkin.grid(row=2, column=0, padx=8, pady=6, sticky="ew")
        self._f_checkout.grid(row=2, column=1, padx=8, pady=6, sticky="ew")
        self._f_notes.grid(row=3, column=0, columnspan=2, padx=8, pady=6, sticky="ew")

        btn = tk.Frame(self, bg=t.c("bg_dialog"))
        btn.pack(pady=12)
        Button(btn, "💾 Save", command=self._save, style="primary").pack(side="left", padx=8)
        Button(btn, "Cancel", command=self.destroy, style="ghost").pack(side="left")

    def _populate(self):
        r = self._rec
        if r.officer_id:
            officers = self._svc.officers.get_all_simple()
            for oid, num, n in officers:
                if oid == r.officer_id:
                    self._f_officer.value = f"{n} ({num})"
                    break
        self._f_date.value     = r.date or datetime.now().strftime("%Y-%m-%d")
        self._f_checkin.value  = r.check_in
        self._f_checkout.value = r.check_out
        self._f_status.value   = r.status or "Present"
        self._f_notes.value    = r.notes

    def _save(self):
        r = self._rec
        officer_key = self._f_officer.value
        r.officer_id = self._officer_map.get(officer_key, 0)
        r.date       = self._f_date.value
        r.check_in   = self._f_checkin.value
        r.check_out  = self._f_checkout.value
        r.status     = self._f_status.value
        r.notes      = self._f_notes.value
        ok, msg = self._svc.attendance.save(r)
        info_dialog(self, "Result", msg)
        if ok:
            if self._on_save: self._on_save()
            self.destroy()


class MonthlyAttendanceDialog(tk.Toplevel):
    def __init__(self, parent, services):
        super().__init__(parent)
        self._svc = services
        self.title("Monthly Attendance Report")
        self.configure(bg=tm().c("bg_dialog"))
        self.geometry("720x520")
        self.transient(parent)
        self._build()

    def _build(self):
        t = tm()
        ctrl = tk.Frame(self, bg=t.c("bg_dialog"))
        ctrl.pack(fill="x", padx=16, pady=12)
        now = datetime.now()

        tk.Label(ctrl, text="Year:", bg=t.c("bg_dialog"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left")
        self._year = tk.StringVar(value=str(now.year))
        tk.Entry(ctrl, textvariable=self._year, width=6,
                 bg=t.c("bg_input"), fg=t.c("text_primary"),
                 font=FONTS["input"], relief="solid", bd=1).pack(side="left", padx=4)

        tk.Label(ctrl, text="Month:", bg=t.c("bg_dialog"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(8, 0))
        self._month = tk.StringVar(value=str(now.month))
        months = [str(i) for i in range(1, 13)]
        ttk.Combobox(ctrl, textvariable=self._month, values=months,
                     state="readonly", width=4,
                     font=FONTS["input"]).pack(side="left", padx=4)
        Button(ctrl, "Generate", command=self._generate, style="primary").pack(side="left", padx=8)

        cols = [("Officer #",90),("Name",150),("Present",80),
                ("Late",70),("Absent",70),("Leave",70)]
        self._table = DataTable(self, columns=cols)
        self._table.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self._generate()

    def _generate(self):
        try:
            y, m = int(self._year.get()), int(self._month.get())
            stats = self._svc.attendance.get_monthly_stats(y, m)
            rows = [(i+1, s["officer_number"], s["full_name"],
                     s["present_days"], s["late_days"],
                     s["absent_days"], s["leave_days"])
                    for i, s in enumerate(stats)]
            self._table.populate(rows, id_col=True)
        except Exception as e:
            info_dialog(self, "Error", str(e))



# ======================================================================
# LEAVE VIEW
# ======================================================================

class LeaveView(_BaseModuleView):
    MODULE_TITLE  = "Leave & Vacation Management"
    TABLE_COLUMNS = [
        ("ID",70),("Officer #",90),("Name",140),("Leave Type",120),
        ("Start Date",100),("End Date",100),("Days",60),("Status",90),
    ]

    def _build_filters(self):
        super()._build_filters()
        t = tm()
        tk.Label(self._flt, text="Status:", bg=t.c("bg_app"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(12, 4))
        self._status_var = tk.StringVar(value="All")
        ttk.Combobox(self._flt, textvariable=self._status_var,
                     values=["All","Pending","Approved","Rejected"],
                     state="readonly", width=10,
                     font=FONTS["input"]).pack(side="left")
        self._status_var.trace_add("write", lambda *_: self.load())

    def _extra_toolbar_buttons(self):
        Button(self._toolbar, "✔ Approve", command=self._approve, style="success").pack(side="left", padx=4)
        Button(self._toolbar, "✖ Reject",  command=self._reject,  style="danger").pack(side="left", padx=4)

    def load(self):
        status = self._status_var.get() if hasattr(self, "_status_var") else "All"
        search = self._search.get() if hasattr(self, "_search") else None
        records = self._svc.leaves.get_all(
            status=None if status == "All" else status,
            search=search or None)
        rows = [(r.id, r.officer_number, r.officer_name, r.leave_type_name,
                 r.start_date, r.end_date, r.duration_days, r.approval_status)
                for r in records]
        self._table.populate(rows)
        self._summary_lbl.configure(text=f"{len(rows)} requests")

    def _add(self):
        LeaveFormDialog(self, self._svc, on_save=self.load)

    def _edit(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Select a record."); return
        rec = self._svc.leaves.get_by_id(self._selected_id)
        if rec: LeaveFormDialog(self, self._svc, record=rec, on_save=self.load)

    def _do_delete(self, rid):
        return self._svc.leaves.delete(rid)

    def _approve(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Select a leave request."); return
        ok, msg = self._svc.leaves.approve(self._selected_id)
        info_dialog(self, "Result", msg)
        self.load()

    def _reject(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Select a leave request."); return
        ok, msg = self._svc.leaves.reject(self._selected_id)
        info_dialog(self, "Result", msg)
        self.load()


class LeaveFormDialog(tk.Toplevel):
    def __init__(self, parent, services, record: LeaveRequest = None, on_save=None):
        super().__init__(parent)
        self._svc = services
        self._rec = record or LeaveRequest()
        self._on_save = on_save
        self._is_edit = bool(record and record.id)
        self.title("Edit Leave Request" if self._is_edit else "New Leave Request")
        self.configure(bg=tm().c("bg_dialog"))
        self.geometry("500x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._populate()

    def _build(self):
        t = tm()
        tk.Label(self, text="Leave Request", bg=t.c("bg_dialog"),
                 fg=t.c("text_primary"), font=FONTS["subtitle"]).pack(pady=(16,8))
        ttk.Separator(self).pack(fill="x", padx=16)

        form = tk.Frame(self, bg=t.c("bg_dialog"))
        form.pack(padx=24, pady=12, fill="both")
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1)

        officers = self._svc.officers.get_all_simple()
        onames = [f"{n} ({num})" for _, num, n in officers]
        self._officer_map = {f"{n} ({num})": oid for oid, num, n in officers}
        leave_types = self._svc.reference.get_leave_types()
        ltypes = [lt.name for lt in leave_types]
        self._lt_map = {lt.name: lt.id for lt in leave_types}

        self._f_officer  = LabeledCombo(form, "Officer", onames, required=True)
        self._f_ltype    = LabeledCombo(form, "Leave Type", ltypes, required=True)
        self._f_start    = LabeledEntry(form, "Start Date (YYYY-MM-DD)", required=True)
        self._f_end      = LabeledEntry(form, "End Date (YYYY-MM-DD)",   required=True)
        self._f_status   = LabeledCombo(form, "Status", ["Pending","Approved","Rejected"])
        self._use_acc_var = tk.BooleanVar(value=False)
        use_acc_cb = tk.Checkbutton(
            form,
            text="Use accumulated leave balance",
            variable=self._use_acc_var,
            bg=t.c("bg_dialog"),
            fg=t.c("text_primary"),
            selectcolor=t.c("bg_card"),
            activebackground=t.c("bg_dialog"),
            activeforeground=t.c("text_primary"),
            font=FONTS["small"],
        )
        self._f_acc_used = LabeledEntry(form, "Accumulated Days Used")
        self._f_notes    = LabeledText(form, "Notes", height=3)

        self._f_officer.grid(row=0, column=0, columnspan=2, padx=8, pady=6, sticky="ew")
        self._f_ltype.grid(row=1, column=0, padx=8, pady=6, sticky="ew")
        self._f_status.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
        self._f_start.grid(row=2, column=0, padx=8, pady=6, sticky="ew")
        self._f_end.grid(row=2, column=1, padx=8, pady=6, sticky="ew")
        use_acc_cb.grid(row=3, column=0, columnspan=2, padx=8, pady=6, sticky="w")
        self._f_acc_used.grid(row=4, column=0, columnspan=2, padx=8, pady=6, sticky="ew")
        self._f_notes.grid(row=5, column=0, columnspan=2, padx=8, pady=6, sticky="ew")

        btn = tk.Frame(self, bg=t.c("bg_dialog"))
        btn.pack(pady=12)
        Button(btn, "💾 Save", command=self._save, style="primary").pack(side="left", padx=8)
        Button(btn, "Cancel", command=self.destroy, style="ghost").pack(side="left")

    def _populate(self):
        r = self._rec
        if r.officer_id:
            for oid, num, n in self._svc.officers.get_all_simple():
                if oid == r.officer_id:
                    self._f_officer.value = f"{n} ({num})"; break
        self._f_ltype.value  = r.leave_type_name
        self._f_start.value  = r.start_date
        self._f_end.value    = r.end_date
        self._f_status.value = r.approval_status or "Pending"
        self._use_acc_var.set(bool(r.use_accumulated))
        self._f_acc_used.value = str(r.accumulated_days_used or 0)
        self._f_notes.value  = r.notes

    def _save(self):
        r = self._rec
        okey = self._f_officer.value
        r.officer_id    = self._officer_map.get(okey, 0)
        lt_name = self._f_ltype.value
        r.leave_type_id = self._lt_map.get(lt_name)
        r.start_date    = self._f_start.value
        r.end_date      = self._f_end.value
        r.approval_status = self._f_status.value
        r.use_accumulated = self._use_acc_var.get()
        try:
            r.accumulated_days_used = int(self._f_acc_used.value or "0")
        except ValueError:
            info_dialog(self, "Error", "Accumulated days used must be a valid number.")
            return
        r.notes         = self._f_notes.value
        ok, msg = self._svc.leaves.save(r)
        info_dialog(self, "Result", msg)
        if ok:
            if self._on_save: self._on_save()
            self.destroy()


# ======================================================================
# DUTIES VIEW
# ======================================================================

class DutiesView(_BaseModuleView):
    MODULE_TITLE  = "Daily Duty & Work Tracking"
    TABLE_COLUMNS = [
        ("ID",70),("Officer #",90),("Name",140),("Date",100),
        ("Shift",90),("Assignment",150),("Location",120),("Status",100),
    ]

    def _build_filters(self):
        super()._build_filters()
        t = tm()
        tk.Label(self._flt, text="Date:", bg=t.c("bg_app"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(12,4))
        self._date_var = tk.StringVar()
        tk.Entry(self._flt, textvariable=self._date_var, width=12,
                 bg=t.c("bg_input"), fg=t.c("text_primary"),
                 font=FONTS["input"], relief="solid", bd=1).pack(side="left")
        Button(self._flt, "Filter", command=self.load, style="ghost").pack(side="left", padx=4)
        Button(self._flt, "Today",
               command=lambda: (self._date_var.set(datetime.now().strftime("%Y-%m-%d")), self.load()),
               style="ghost").pack(side="left")

    def load(self):
        date_f = self._date_var.get() if hasattr(self, "_date_var") else None
        search = self._search.get() if hasattr(self, "_search") else None
        records = self._svc.duties.get_all(date_filter=date_f or None, search=search or None)
        rows = [(r.id, r.officer_number, r.officer_name, r.duty_date,
                 r.shift, r.assignment, r.duty_location, r.completion_status)
                for r in records]
        self._table.populate(rows)
        self._summary_lbl.configure(text=f"{len(rows)} duties")

    def _add(self):
        DutyFormDialog(self, self._svc, on_save=self.load)

    def _edit(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Select a record."); return
        rec = self._svc.duties.get_by_id(self._selected_id)
        if rec: DutyFormDialog(self, self._svc, record=rec, on_save=self.load)

    def _do_delete(self, rid):
        return self._svc.duties.delete(rid)


class DutyFormDialog(tk.Toplevel):
    def __init__(self, parent, services, record: DailyDuty = None, on_save=None):
        super().__init__(parent)
        self._svc = services
        self._rec = record or DailyDuty()
        self._on_save = on_save
        self._is_edit = bool(record and record.id)
        self.title("Edit Duty" if self._is_edit else "Add Duty")
        self.configure(bg=tm().c("bg_dialog"))
        self.geometry("500x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._populate()

    def _build(self):
        t = tm()
        tk.Label(self, text="Daily Duty Record", bg=t.c("bg_dialog"),
                 fg=t.c("text_primary"), font=FONTS["subtitle"]).pack(pady=(16,8))
        ttk.Separator(self).pack(fill="x", padx=16)

        form = tk.Frame(self, bg=t.c("bg_dialog"))
        form.pack(padx=24, pady=12, fill="both")
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1)

        officers = self._svc.officers.get_all_simple()
        onames = [f"{n} ({num})" for _, num, n in officers]
        self._officer_map = {f"{n} ({num})": oid for oid, num, n in officers}

        self._f_officer   = LabeledCombo(form, "Officer", onames, required=True)
        self._f_date      = LabeledEntry(form, "Duty Date (YYYY-MM-DD)", required=True)
        self._f_shift     = LabeledCombo(form, "Shift",
                                          ["","Morning","Afternoon","Night","Full Day"])
        self._f_assignment= LabeledEntry(form, "Assignment")
        self._f_location  = LabeledEntry(form, "Duty Location")
        self._f_status    = LabeledCombo(form, "Status",
                                          ["Pending","Completed","Cancelled","Partial"])
        self._f_notes     = LabeledText(form, "Notes", height=3)

        self._f_officer.grid(row=0, column=0, columnspan=2, padx=8, pady=6, sticky="ew")
        self._f_date.grid(row=1, column=0, padx=8, pady=6, sticky="ew")
        self._f_shift.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
        self._f_assignment.grid(row=2, column=0, padx=8, pady=6, sticky="ew")
        self._f_location.grid(row=2, column=1, padx=8, pady=6, sticky="ew")
        self._f_status.grid(row=3, column=0, padx=8, pady=6, sticky="ew")
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
                    self._f_officer.value = f"{n} ({num})"; break
        self._f_date.value      = r.duty_date or datetime.now().strftime("%Y-%m-%d")
        self._f_shift.value     = r.shift
        self._f_assignment.value= r.assignment
        self._f_location.value  = r.duty_location
        self._f_status.value    = r.completion_status or "Pending"
        self._f_notes.value     = r.notes

    def _save(self):
        r = self._rec
        okey = self._f_officer.value
        r.officer_id       = self._officer_map.get(okey, 0)
        r.duty_date        = self._f_date.value
        r.shift            = self._f_shift.value
        r.assignment       = self._f_assignment.value
        r.duty_location    = self._f_location.value
        r.completion_status= self._f_status.value
        r.notes            = self._f_notes.value
        ok, msg = self._svc.duties.save(r)
        info_dialog(self, "Result", msg)
        if ok:
            if self._on_save: self._on_save()
            self.destroy()


# ======================================================================
# MEALS VIEW
# ======================================================================

class MealsView(_BaseModuleView):
    MODULE_TITLE  = "Meals / Feeding Log Management"
    TABLE_COLUMNS = [
        ("ID",70),("Officer #",90),("Name",140),
        ("Date",100),("Meal Type",100),("Qty",60),("Notes",160),
    ]

    def _build_filters(self):
        super()._build_filters()
        t = tm()
        tk.Label(self._flt, text="Date:", bg=t.c("bg_app"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(12,4))
        self._date_var = tk.StringVar()
        tk.Entry(self._flt, textvariable=self._date_var, width=12,
                 bg=t.c("bg_input"), fg=t.c("text_primary"),
                 font=FONTS["input"], relief="solid", bd=1).pack(side="left")
        Button(self._flt, "Filter", command=self.load, style="ghost").pack(side="left", padx=4)
        Button(self._flt, "Today",
               command=lambda: (self._date_var.set(datetime.now().strftime("%Y-%m-%d")), self.load()),
               style="ghost").pack(side="left")

        tk.Label(self._flt, text="Type:", bg=t.c("bg_app"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(8,4))
        self._type_var = tk.StringVar(value="All")
        ttk.Combobox(self._flt, textvariable=self._type_var,
                     values=["All","Breakfast","Lunch","Dinner","Snack"],
                     state="readonly", width=10, font=FONTS["input"]).pack(side="left")
        self._type_var.trace_add("write", lambda *_: self.load())

    def _extra_toolbar_buttons(self):
        Button(self._toolbar, "📊 Monthly Summary",
               command=self._monthly_summary, style="ghost").pack(side="left", padx=4)

    def load(self):
        date_f = self._date_var.get() if hasattr(self, "_date_var") else None
        meal_t = self._type_var.get() if hasattr(self, "_type_var") else "All"
        search = self._search.get() if hasattr(self, "_search") else None
        records = self._svc.meals.get_all(
            date_filter=date_f or None,
            meal_type=None if meal_t == "All" else meal_t,
            search=search or None)
        rows = [(r.id, r.officer_number, r.officer_name,
                 r.meal_date, r.meal_type, r.quantity, r.notes) for r in records]
        self._table.populate(rows)
        self._summary_lbl.configure(text=f"{len(rows)} records")

    def _add(self):
        MealFormDialog(self, self._svc, on_save=self.load)

    def _edit(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Select a record."); return
        rec = self._svc.meals.get_by_id(self._selected_id)
        if rec: MealFormDialog(self, self._svc, record=rec, on_save=self.load)

    def _do_delete(self, rid):
        return self._svc.meals.delete(rid)

    def _monthly_summary(self):
        MealsMonthlySummaryDialog(self, self._svc)



class MealFormDialog(tk.Toplevel):
    def __init__(self, parent, services, record: MealRecord = None, on_save=None):
        super().__init__(parent)
        self._svc = services
        self._rec = record or MealRecord()
        self._on_save = on_save
        self._is_edit = bool(record and record.id)
        self.title("Edit Meal Record" if self._is_edit else "Add Meal Record")
        self.configure(bg=tm().c("bg_dialog"))
        self.geometry("460x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._populate()

    def _build(self):
        t = tm()
        tk.Label(self, text="Meal Record", bg=t.c("bg_dialog"),
                 fg=t.c("text_primary"), font=FONTS["subtitle"]).pack(pady=(16,8))
        ttk.Separator(self).pack(fill="x", padx=16)

        form = tk.Frame(self, bg=t.c("bg_dialog"))
        form.pack(padx=24, pady=12, fill="both")
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1)

        officers = self._svc.officers.get_all_simple()
        onames = [f"{n} ({num})" for _, num, n in officers]
        self._officer_map = {f"{n} ({num})": oid for oid, num, n in officers}

        self._f_officer = LabeledCombo(form, "Officer", onames, required=True)
        self._f_date    = LabeledEntry(form, "Date (YYYY-MM-DD)", required=True)
        self._f_type    = LabeledCombo(form, "Meal Type",
                                        ["Breakfast","Lunch","Dinner","Snack"], required=True)
        self._f_qty     = LabeledEntry(form, "Quantity")
        self._f_notes   = LabeledText(form, "Notes", height=3)

        self._f_officer.grid(row=0, column=0, columnspan=2, padx=8, pady=6, sticky="ew")
        self._f_date.grid(row=1, column=0, padx=8, pady=6, sticky="ew")
        self._f_type.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
        self._f_qty.grid(row=2, column=0, padx=8, pady=6, sticky="ew")
        self._f_notes.grid(row=3, column=0, columnspan=2, padx=8, pady=6, sticky="ew")

        btn = tk.Frame(self, bg=t.c("bg_dialog"))
        btn.pack(pady=12)
        Button(btn, "💾 Save", command=self._save, style="primary").pack(side="left", padx=8)
        Button(btn, "Cancel", command=self.destroy, style="ghost").pack(side="left")

    def _populate(self):
        r = self._rec
        if r.officer_id:
            for oid, num, n in self._svc.officers.get_all_simple():
                if oid == r.officer_id:
                    self._f_officer.value = f"{n} ({num})"; break
        self._f_date.value = r.meal_date or datetime.now().strftime("%Y-%m-%d")
        self._f_type.value = r.meal_type or "Lunch"
        self._f_qty.value  = str(r.quantity) if r.quantity else "1"
        self._f_notes.value= r.notes

    def _save(self):
        r = self._rec
        okey = self._f_officer.value
        r.officer_id = self._officer_map.get(okey, 0)
        r.meal_date  = self._f_date.value
        r.meal_type  = self._f_type.value
        try:
            r.quantity = int(self._f_qty.value or "1")
        except ValueError:
            r.quantity = 1
        r.notes = self._f_notes.value
        ok, msg = self._svc.meals.save(r)
        info_dialog(self, "Result", msg)
        if ok:
            if self._on_save: self._on_save()
            self.destroy()


class MealsMonthlySummaryDialog(tk.Toplevel):
    def __init__(self, parent, services):
        super().__init__(parent)
        self._svc = services
        self.title("Monthly Meals Summary")
        self.configure(bg=tm().c("bg_dialog"))
        self.geometry("680x480")
        self.transient(parent)
        self._build()

    def _build(self):
        t = tm()
        ctrl = tk.Frame(self, bg=t.c("bg_dialog"))
        ctrl.pack(fill="x", padx=16, pady=12)
        now = datetime.now()
        tk.Label(ctrl, text="Year:", bg=t.c("bg_dialog"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left")
        self._year = tk.StringVar(value=str(now.year))
        tk.Entry(ctrl, textvariable=self._year, width=6,
                 bg=t.c("bg_input"), fg=t.c("text_primary"),
                 font=FONTS["input"], relief="solid", bd=1).pack(side="left", padx=4)
        tk.Label(ctrl, text="Month:", bg=t.c("bg_dialog"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left", padx=(8,0))
        self._month = tk.StringVar(value=str(now.month))
        ttk.Combobox(ctrl, textvariable=self._month,
                     values=[str(i) for i in range(1,13)],
                     state="readonly", width=4,
                     font=FONTS["input"]).pack(side="left", padx=4)
        Button(ctrl, "Generate", command=self._generate, style="primary").pack(side="left", padx=8)

        cols = [("Officer #",90),("Name",150),("Breakfast",90),
                ("Lunch",80),("Dinner",80),("Total",70)]
        self._table = DataTable(self, columns=cols)
        self._table.pack(fill="both", expand=True, padx=16, pady=(0,12))
        self._generate()

    def _generate(self):
        try:
            y, m = int(self._year.get()), int(self._month.get())
            summary = self._svc.meals.get_monthly_summary(y, m)
            rows = [(i+1, s["officer_number"], s["full_name"],
                     s["breakfast"], s["lunch"], s["dinner"], s["total"])
                    for i, s in enumerate(summary)]
            self._table.populate(rows, id_col=True)
        except Exception as e:
            info_dialog(self, "Error", str(e))
