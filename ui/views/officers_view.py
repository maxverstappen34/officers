"""
Officers Management View - Officers Affairs Management System
Full CRUD, search, filters, officer profile.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import ThemeManager, FONTS
from ui.components.widgets import (
    Button, Card, DataTable, SearchBar, LabeledEntry,
    LabeledCombo, LabeledText, StatusBadge, confirm_dialog, info_dialog
)
from models.models import Officer, PromotionHistory

tm = ThemeManager.get


class OfficersView(tk.Frame):
    def __init__(self, parent, services, **kw):
        t = tm()
        super().__init__(parent, bg=t.c("bg_app"), **kw)
        self._svc = services
        self._selected_id = None
        self._page = 1
        self._page_size = 50
        self._all_records = []
        self._build()
        self.load()

    def _build(self):
        t = tm()
        # Header
        hdr = tk.Frame(self, bg=t.c("bg_app"))
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(hdr, text="Officers Management", bg=t.c("bg_app"),
                 fg=t.c("text_primary"), font=FONTS["title"]).pack(side="left")

        # Toolbar
        toolbar = tk.Frame(self, bg=t.c("bg_app"))
        toolbar.pack(fill="x", padx=24, pady=(0, 8))

        Button(toolbar, "＋ Add Officer",   command=self._add,    style="primary").pack(side="left", padx=(0,4))
        Button(toolbar, "✎ Edit",           command=self._edit,   style="ghost").pack(side="left", padx=4)
        Button(toolbar, "🗑 Delete",        command=self._delete, style="danger").pack(side="left", padx=4)
        Button(toolbar, "👤 Profile",       command=self._profile,style="ghost").pack(side="left", padx=4)

        # Filters row
        flt = tk.Frame(self, bg=t.c("bg_app"))
        flt.pack(fill="x", padx=24, pady=(0, 6))

        self._search = SearchBar(flt, on_search=self._on_search)
        self._search.pack(side="left", padx=(0, 12))

        tk.Label(flt, text="Status:", bg=t.c("bg_app"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left")
        self._status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(flt, textvariable=self._status_var,
                                     values=["All", "Active", "On Leave",
                                             "Suspended", "Retired"],
                                     state="readonly", width=12,
                                     font=FONTS["input"])
        status_combo.pack(side="left", padx=(4, 12))
        status_combo.bind("<<ComboboxSelected>>", lambda _: self.load())

        tk.Label(flt, text="Dept:", bg=t.c("bg_app"),
                 fg=t.c("text_secondary"), font=FONTS["small"]).pack(side="left")
        depts = ["All"] + [d.name for d in self._svc.reference.get_departments()]
        self._dept_var = tk.StringVar(value="All")
        dept_combo = ttk.Combobox(flt, textvariable=self._dept_var,
                                   values=depts, state="readonly",
                                   width=18, font=FONTS["input"])
        dept_combo.pack(side="left", padx=(4, 0))
        dept_combo.bind("<<ComboboxSelected>>", lambda _: self.load())

        # Summary label
        self._summary = tk.Label(flt, text="", bg=t.c("bg_app"),
                                  fg=t.c("text_muted"), font=FONTS["small"])
        self._summary.pack(side="right")

        # Table
        columns = [
            ("ID",         50),  ("Officer #",  90), ("Full Name",    160),
            ("Rank",       120), ("Department", 130), ("Unit",        110),
            ("Status",     90),  ("Joining Date",110),
        ]
        self._table = DataTable(self, columns=columns,
                                 on_select=self._on_select,
                                 on_double_click=self._profile)
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 12))

    def load(self):
        search = self._search.get()
        status = self._status_var.get()
        dept_name = self._dept_var.get()

        dept_id = None
        if dept_name != "All":
            for d in self._svc.reference.get_departments():
                if d.name == dept_name:
                    dept_id = d.id
                    break

        officers = self._svc.officers.get_all(
            status=None if status == "All" else status,
            department_id=dept_id,
            search=search or None)
        self._all_records = officers

        rows = [(o.id, o.officer_number, o.full_name, o.rank_name,
                 o.department_name, o.unit_name, o.current_status,
                 o.date_of_joining)
                for o in officers]
        self._table.populate(rows)
        self._summary.configure(text=f"{len(officers)} officers found")

    def _on_search(self, _):
        self.load()

    def _on_select(self, record_id):
        self._selected_id = record_id

    def _add(self):
        OfficerFormDialog(self, self._svc, officer=None,
                           on_save=self.load)

    def _edit(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Please select an officer to edit.")
            return
        officer = self._svc.officers.get_by_id(self._selected_id)
        if officer:
            OfficerFormDialog(self, self._svc, officer=officer,
                               on_save=self.load)

    def _delete(self):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Please select an officer to delete.")
            return
        officer = self._svc.officers.get_by_id(self._selected_id)
        name = officer.full_name if officer else ""
        if confirm_dialog(self, "Confirm Delete",
                          f"Are you sure you want to delete officer\n'{name}'?\n\nThis cannot be undone."):
            ok, msg = self._svc.officers.delete(self._selected_id)
            info_dialog(self, "Result", msg)
            self._selected_id = None
            self.load()

    def _profile(self, _=None):
        if not self._selected_id:
            info_dialog(self, "No Selection", "Please select an officer first.")
            return
        officer = self._svc.officers.get_by_id(self._selected_id)
        if officer:
            OfficerProfileDialog(self, self._svc, officer)



# ──────────────────────────────────────────────
# Officer Form Dialog
# ──────────────────────────────────────────────

class OfficerFormDialog(tk.Toplevel):
    def __init__(self, parent, services, officer: Officer = None,
                 on_save=None):
        super().__init__(parent)
        self._svc = services
        self._officer = officer or Officer()
        self._on_save = on_save
        self._is_edit = (officer is not None and officer.id > 0)

        self.title("Edit Officer" if self._is_edit else "Add New Officer")
        self.configure(bg=tm().c("bg_dialog"))
        self.geometry("780x680")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self._build()
        self._populate()

    def _build(self):
        t = tm()
        # Title
        tk.Label(self, text="Edit Officer" if self._is_edit else "Add New Officer",
                 bg=t.c("bg_dialog"), fg=t.c("text_primary"),
                 font=FONTS["subtitle"]).pack(pady=(16, 8))
        ttk.Separator(self).pack(fill="x", padx=16)

        # Notebook tabs
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=8)

        personal_tab = tk.Frame(nb, bg=t.c("bg_dialog"))
        career_tab   = tk.Frame(nb, bg=t.c("bg_dialog"))
        nb.add(personal_tab, text="  Personal Information  ")
        nb.add(career_tab,   text="  Career Information  ")

        self._build_personal(personal_tab)
        self._build_career(career_tab)

        # Buttons
        btn_bar = tk.Frame(self, bg=t.c("bg_dialog"))
        btn_bar.pack(pady=12)
        Button(btn_bar, "💾 Save Officer", command=self._save, style="primary").pack(side="left", padx=8)
        Button(btn_bar, "Cancel", command=self.destroy, style="ghost").pack(side="left", padx=8)

    def _build_personal(self, tab):
        t = tm()
        frame = tk.Frame(tab, bg=t.c("bg_dialog"))
        frame.pack(fill="both", expand=True, padx=20, pady=12)

        def row(r, c, widget):
            widget.grid(row=r, column=c, padx=8, pady=6, sticky="ew")

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        self._f_number   = LabeledEntry(frame, "Officer Number", required=True)
        self._f_name     = LabeledEntry(frame, "Full Name", required=True, width=32)
        self._f_national = LabeledEntry(frame, "National ID")
        self._f_dob      = LabeledEntry(frame, "Date of Birth (YYYY-MM-DD)")
        self._f_phone    = LabeledEntry(frame, "Phone Number")
        self._f_emergency= LabeledEntry(frame, "Emergency Contact")
        self._f_marital  = LabeledCombo(frame, "Marital Status",
                                         ["", "Single","Married","Divorced","Widowed"])
        self._f_blood    = LabeledCombo(frame, "Blood Type",
                                         ["","A+","A-","B+","B-","AB+","AB-","O+","O-"])
        self._f_address  = LabeledText(frame, "Address", height=3)

        row(0, 0, self._f_number)
        row(0, 1, self._f_name)
        row(1, 0, self._f_national)
        row(1, 1, self._f_dob)
        row(2, 0, self._f_phone)
        row(2, 1, self._f_emergency)
        row(3, 0, self._f_marital)
        row(3, 1, self._f_blood)
        self._f_address.grid(row=4, column=0, columnspan=2, padx=8, pady=6, sticky="ew")

        # Photo section
        photo_frame = tk.Frame(frame, bg=t.c("bg_dialog"))
        photo_frame.grid(row=5, column=0, columnspan=2, padx=8, pady=4, sticky="w")
        self._photo_label = tk.Label(photo_frame, text="No photo selected",
                                      bg=t.c("bg_dialog"), fg=t.c("text_muted"),
                                      font=FONTS["small"])
        self._photo_label.pack(side="left")
        Button(photo_frame, "📷 Select Photo", command=self._select_photo,
               style="ghost").pack(side="left", padx=8)
        self._photo_path = ""

    def _build_career(self, tab):
        t = tm()
        frame = tk.Frame(tab, bg=t.c("bg_dialog"))
        frame.pack(fill="both", expand=True, padx=20, pady=12)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        ranks  = [""] + [r.name for r in self._svc.reference.get_ranks()]
        depts  = [""] + [d.name for d in self._svc.reference.get_departments()]
        units  = [""] + [u.name for u in self._svc.reference.get_units()]
        statuses = ["Active","On Leave","Suspended","Retired"]

        self._f_rank     = LabeledCombo(frame, "Rank", ranks)
        self._f_dept     = LabeledCombo(frame, "Department", depts)
        self._f_unit     = LabeledCombo(frame, "Unit", units)
        self._f_position = LabeledEntry(frame, "Job Position")
        self._f_joining  = LabeledEntry(frame, "Date of Joining (YYYY-MM-DD)")
        self._f_status   = LabeledCombo(frame, "Current Status", statuses, required=True)
        self._f_eligible = LabeledCombo(frame, "Eligible For Accumulation", ["No", "Yes"])
        self._f_acc_limit = LabeledEntry(frame, "Accumulation Limit (Days)")
        self._f_notes    = LabeledText(frame, "Notes", height=4)

        self._f_rank.grid(row=0, column=0, padx=8, pady=6, sticky="ew")
        self._f_dept.grid(row=0, column=1, padx=8, pady=6, sticky="ew")
        self._f_unit.grid(row=1, column=0, padx=8, pady=6, sticky="ew")
        self._f_position.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
        self._f_joining.grid(row=2, column=0, padx=8, pady=6, sticky="ew")
        self._f_status.grid(row=2, column=1, padx=8, pady=6, sticky="ew")
        self._f_eligible.grid(row=3, column=0, padx=8, pady=6, sticky="ew")
        self._f_acc_limit.grid(row=3, column=1, padx=8, pady=6, sticky="ew")
        self._f_notes.grid(row=4, column=0, columnspan=2, padx=8, pady=6, sticky="ew")

        # Update unit list when dept changes
        self._f_dept.combo.bind("<<ComboboxSelected>>", self._on_dept_change)

    def _on_dept_change(self, _):
        dept_name = self._f_dept.value
        dept_id = None
        for d in self._svc.reference.get_departments():
            if d.name == dept_name:
                dept_id = d.id
                break
        units = [""] + [u.name for u in self._svc.reference.get_units(dept_id)]
        self._f_unit.combo["values"] = units
        self._f_unit.value = ""

    def _populate(self):
        o = self._officer
        self._f_number.value   = o.officer_number
        self._f_name.value     = o.full_name
        self._f_national.value = o.national_id
        self._f_dob.value      = o.date_of_birth
        self._f_phone.value    = o.phone
        self._f_emergency.value= o.emergency_contact
        self._f_marital.value  = o.marital_status
        self._f_blood.value    = o.blood_type
        self._f_address.value  = o.address
        self._f_rank.value     = o.rank_name
        self._f_dept.value     = o.department_name
        self._f_unit.value     = o.unit_name
        self._f_position.value = o.job_position
        self._f_joining.value  = o.date_of_joining
        self._f_status.value   = o.current_status or "Active"
        self._f_eligible.value = "Yes" if o.eligible_for_accumulation else "No"
        self._f_acc_limit.value = str(o.accumulation_limit_days or 0)
        self._f_notes.value    = o.notes
        if o.photo_path:
            self._photo_label.configure(text=os.path.basename(o.photo_path))
            self._photo_path = o.photo_path

    def _select_photo(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if path:
            self._photo_path = path
            self._photo_label.configure(text=os.path.basename(path))

    def _save(self):
        o = self._officer
        o.officer_number  = self._f_number.value
        o.full_name       = self._f_name.value
        o.national_id     = self._f_national.value
        o.date_of_birth   = self._f_dob.value
        o.phone           = self._f_phone.value
        o.emergency_contact = self._f_emergency.value
        o.marital_status  = self._f_marital.value
        o.blood_type      = self._f_blood.value
        o.address         = self._f_address.value
        o.job_position    = self._f_position.value
        o.date_of_joining = self._f_joining.value
        o.current_status  = self._f_status.value
        o.notes           = self._f_notes.value
        o.eligible_for_accumulation = (self._f_eligible.value == "Yes")
        try:
            o.accumulation_limit_days = int(self._f_acc_limit.value or "0")
        except ValueError:
            info_dialog(self, "Error", "Accumulation limit must be a valid number.")
            return
        if o.accumulation_limit_days < 0:
            info_dialog(self, "Error", "Accumulation limit cannot be negative.")
            return

        o.marital_status = self._f_marital.value or None
        o.blood_type = self._f_blood.value or None

        # Resolve rank
        rank_name = self._f_rank.value
        o.rank_id = None
        for r in self._svc.reference.get_ranks():
            if r.name == rank_name:
                o.rank_id = r.id
                break

        # Resolve dept
        dept_name = self._f_dept.value
        o.department_id = None
        for d in self._svc.reference.get_departments():
            if d.name == dept_name:
                o.department_id = d.id
                break

        # Resolve unit
        unit_name = self._f_unit.value
        o.unit_id = None
        for u in self._svc.reference.get_units():
            if u.name == unit_name:
                o.unit_id = u.id
                break

        ok, msg = self._svc.officers.save(o)
        if ok:
            # Save photo
            if self._photo_path and o.id:
                try:
                    new_path = self._svc.officers.save_photo(o.id, self._photo_path)
                    o.photo_path = new_path
                    self._svc.officers.save(o)
                except Exception:
                    pass
            info_dialog(self, "Success", msg)
            if self._on_save:
                self._on_save()
            self.destroy()
        else:
            info_dialog(self, "Error", msg)


# ──────────────────────────────────────────────
# Officer Profile Dialog
# ──────────────────────────────────────────────

class OfficerProfileDialog(tk.Toplevel):
    def __init__(self, parent, services, officer: Officer):
        super().__init__(parent)
        self._svc = services
        self._officer = officer
        self.title(f"Officer Profile — {officer.full_name}")
        self.configure(bg=tm().c("bg_dialog"))
        self.geometry("750x640")
        self.transient(parent)
        self._build()

    def _build(self):
        t = tm()
        o = self._officer

        # Header card
        hdr = tk.Frame(self, bg=t.c("accent"), height=110)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        photo_lbl = tk.Label(hdr, text="👮", bg=t.c("accent"),
                             font=("Segoe UI", 42))
        photo_lbl.pack(side="left", padx=20)

        info = tk.Frame(hdr, bg=t.c("accent"))
        info.pack(side="left", padx=8, pady=10)
        tk.Label(info, text=o.display_name, bg=t.c("accent"),
                 fg="white", font=FONTS["subtitle"]).pack(anchor="w")
        tk.Label(info, text=f"Officer #{o.officer_number}  |  {o.department_name}",
                 bg=t.c("accent"), fg="#dbeafe", font=FONTS["small"]).pack(anchor="w")
        tk.Label(info, text=o.current_status, bg=t.c("accent"),
                 fg="#bbf7d0", font=FONTS["body_bold"]).pack(anchor="w")

        # Tabs
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=12)

        details_tab = tk.Frame(nb, bg=t.c("bg_dialog"))
        career_tab  = tk.Frame(nb, bg=t.c("bg_dialog"))
        promo_tab   = tk.Frame(nb, bg=t.c("bg_dialog"))
        nb.add(details_tab, text="  Personal  ")
        nb.add(career_tab,  text="  Career  ")
        nb.add(promo_tab,   text="  Promotions  ")

        self._build_details(details_tab, o)
        self._build_career(career_tab, o)
        self._build_promotions(promo_tab, o)

        Button(self, "Close", command=self.destroy, style="ghost").pack(pady=8)

    def _build_details(self, tab, o):
        t = tm()
        pairs = [
            ("National ID",       o.national_id),
            ("Date of Birth",     o.date_of_birth),
            ("Age",               o.age + " years" if o.age else ""),
            ("Blood Type",        o.blood_type),
            ("Marital Status",    o.marital_status),
            ("Phone",             o.phone),
            ("Emergency Contact", o.emergency_contact),
            ("Address",           o.address),
        ]
        self._draw_pairs(tab, pairs)

    def _build_career(self, tab, o):
        pairs = [
            ("Rank",          o.rank_name),
            ("Department",    o.department_name),
            ("Unit",          o.unit_name),
            ("Job Position",  o.job_position),
            ("Date of Joining",o.date_of_joining),
            ("Status",        o.current_status),
            ("Eligible For Accumulation", "Yes" if o.eligible_for_accumulation else "No"),
            ("Accumulation Limit (Days)", str(o.accumulation_limit_days or 0)),
            ("Notes",         o.notes),
        ]
        self._draw_pairs(tab, pairs)

    def _draw_pairs(self, tab, pairs):
        t = tm()
        frame = tk.Frame(tab, bg=t.c("bg_dialog"))
        frame.pack(fill="both", expand=True, padx=24, pady=12)
        for i, (label, value) in enumerate(pairs):
            row = tk.Frame(frame, bg=t.c("bg_dialog"))
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label + ":", width=20, anchor="w",
                     bg=t.c("bg_dialog"), fg=t.c("text_secondary"),
                     font=FONTS["body_bold"]).pack(side="left")
            tk.Label(row, text=value or "—", anchor="w",
                     bg=t.c("bg_dialog"), fg=t.c("text_primary"),
                     font=FONTS["body"]).pack(side="left", padx=8)
            if i < len(pairs) - 1:
                ttk.Separator(frame).pack(fill="x", pady=1)

    def _build_promotions(self, tab, o):
        t = tm()
        frame = tk.Frame(tab, bg=t.c("bg_dialog"))
        frame.pack(fill="both", expand=True, padx=16, pady=8)

        # Add promotion button
        btn_bar = tk.Frame(frame, bg=t.c("bg_dialog"))
        btn_bar.pack(fill="x", pady=(0, 8))
        Button(btn_bar, "＋ Add Promotion",
               command=lambda: self._add_promotion(frame),
               style="primary").pack(side="left")

        columns = [("ID",50), ("Previous Rank",130), ("New Rank",130),
                   ("Date",110), ("Notes",200)]
        table = DataTable(frame, columns=columns)
        table.pack(fill="both", expand=True)

        history = self._svc.officers.get_promotion_history(o.id)
        rows = [(p.id, p.previous_rank, p.new_rank,
                 p.promotion_date, p.notes) for p in history]
        table.populate(rows)

    def _add_promotion(self, parent):
        PromotionDialog(self, self._svc, self._officer,
                        on_save=lambda: self._refresh_promotions(parent))

    def _refresh_promotions(self, parent):
        for widget in parent.winfo_children():
            widget.destroy()
        self._build_promotions(parent, self._officer)


class PromotionDialog(tk.Toplevel):
    def __init__(self, parent, services, officer: Officer, on_save=None):
        super().__init__(parent)
        self._svc = services
        self._officer = officer
        self._on_save = on_save
        self.title(f"Add Promotion — {officer.full_name}")
        self.configure(bg=tm().c("bg_dialog"))
        self.geometry("520x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()

    def _build(self):
        t = tm()
        tk.Label(self, text="Record Promotion", bg=t.c("bg_dialog"),
                 fg=t.c("text_primary"), font=FONTS["subtitle"]).pack(pady=(16, 8))
        ttk.Separator(self).pack(fill="x", padx=16)

        form = tk.Frame(self, bg=t.c("bg_dialog"))
        form.pack(padx=24, pady=12, fill="both")
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1)

        ranks = [r.name for r in self._svc.reference.get_ranks()]
        self._f_prev = LabeledCombo(form, "Previous Rank", ranks)
        self._f_new  = LabeledCombo(form, "New Rank", ranks, required=True)
        self._f_date = LabeledEntry(form, "Promotion Date (YYYY-MM-DD)", required=True)
        self._f_notes = LabeledText(form, "Notes", height=4)

        self._f_prev.grid(row=0, column=0, padx=8, pady=6, sticky="ew")
        self._f_new.grid(row=0, column=1, padx=8, pady=6, sticky="ew")
        self._f_date.grid(row=1, column=0, padx=8, pady=6, sticky="ew")
        self._f_notes.grid(row=2, column=0, columnspan=2, padx=8, pady=6, sticky="ew")

        self._f_prev.value = self._officer.rank_name
        self._f_date.value = datetime.now().strftime("%Y-%m-%d")

        btn_frame = tk.Frame(self, bg=t.c("bg_dialog"))
        btn_frame.pack(pady=12)
        Button(btn_frame, "💾 Save", command=self._save, style="primary").pack(side="left", padx=8)
        Button(btn_frame, "Cancel", command=self.destroy, style="ghost").pack(side="left")

    def _save(self):
        ph = PromotionHistory(
            officer_id=self._officer.id,
            previous_rank=self._f_prev.value,
            new_rank=self._f_new.value,
            promotion_date=self._f_date.value,
            notes=self._f_notes.value,
        )
        ok, msg = self._svc.officers.add_promotion(ph)
        info_dialog(self, "Result", msg if ok else f"Error: {msg}")
        if ok:
            if self._on_save:
                self._on_save()
            self.destroy()
