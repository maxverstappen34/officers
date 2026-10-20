"""
Repositories - Officers Affairs Management System
Data access layer (Repository Pattern).
"""

import sqlite3
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date

from database.db_manager import DatabaseManager
from models.models import (
    Officer, Rank, Department, Unit, PromotionHistory,
    AttendanceRecord, LeaveType, LeaveRequest, LeaveAccumulationRequest,
    DailyDuty, MealRecord,
    DisciplinaryPenalty, AppealRequest, AppealReview, Attachment
)

logger = logging.getLogger(__name__)


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row) if row else {}


# ======================================================================
# Officer Repository
# ======================================================================

class OfficerRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self, status: str = None, department_id: int = None,
                search: str = None) -> List[Officer]:
        sql = """
            SELECT o.*, r.name as rank_name,
                   d.name as department_name, u.name as unit_name
            FROM officers o
            LEFT JOIN ranks r       ON r.id = o.rank_id
            LEFT JOIN departments d ON d.id = o.department_id
            LEFT JOIN units u       ON u.id = o.unit_id
            WHERE 1=1
        """
        params: list = []
        if status:
            sql += " AND o.current_status = ?"
            params.append(status)
        if department_id:
            sql += " AND o.department_id = ?"
            params.append(department_id)
        if search:
            sql += " AND (o.full_name LIKE ? OR o.officer_number LIKE ? OR o.national_id LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s])
        sql += " ORDER BY o.full_name"
        return [self._row_to_officer(r) for r in self.db.fetchall(sql, tuple(params))]

    def get_by_id(self, officer_id: int) -> Optional[Officer]:
        row = self.db.fetchone("""
            SELECT o.*, r.name as rank_name,
                   d.name as department_name, u.name as unit_name
            FROM officers o
            LEFT JOIN ranks r       ON r.id = o.rank_id
            LEFT JOIN departments d ON d.id = o.department_id
            LEFT JOIN units u       ON u.id = o.unit_id
            WHERE o.id = ?
        """, (officer_id,))
        return self._row_to_officer(row) if row else None

    def insert(self, o: Officer) -> int:
        rowid = self.db.execute("""
            INSERT INTO officers(officer_number, full_name, rank_id, national_id,
                date_of_birth, address, phone, emergency_contact, marital_status,
                blood_type, photo_path, department_id, unit_id, job_position,
                date_of_joining, current_status, eligible_for_accumulation,
                accumulation_limit_days, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (o.officer_number, o.full_name, o.rank_id, o.national_id,
              o.date_of_birth, o.address, o.phone, o.emergency_contact,
              o.marital_status, o.blood_type, o.photo_path, o.department_id,
              o.unit_id, o.job_position, o.date_of_joining, o.current_status,
              int(o.eligible_for_accumulation), o.accumulation_limit_days, o.notes))
        self.db.log_audit("officers", rowid, "INSERT", f"Added: {o.full_name}")
        return rowid

    def update(self, o: Officer) -> bool:
        self.db.execute("""
            UPDATE officers SET
                officer_number=?, full_name=?, rank_id=?, national_id=?,
                date_of_birth=?, address=?, phone=?, emergency_contact=?,
                marital_status=?, blood_type=?, photo_path=?, department_id=?,
                unit_id=?, job_position=?, date_of_joining=?, current_status=?,
                eligible_for_accumulation=?, accumulation_limit_days=?,
                notes=?, updated_at=datetime('now')
            WHERE id=?
        """, (o.officer_number, o.full_name, o.rank_id, o.national_id,
              o.date_of_birth, o.address, o.phone, o.emergency_contact,
              o.marital_status, o.blood_type, o.photo_path, o.department_id,
              o.unit_id, o.job_position, o.date_of_joining, o.current_status,
              int(o.eligible_for_accumulation), o.accumulation_limit_days,
              o.notes, o.id))
        self.db.log_audit("officers", o.id, "UPDATE", f"Updated: {o.full_name}")
        return True

    def delete(self, officer_id: int) -> bool:
        officer = self.get_by_id(officer_id)
        self.db.execute("DELETE FROM officers WHERE id=?", (officer_id,))
        if officer:
            self.db.log_audit("officers", officer_id, "DELETE", f"Deleted: {officer.full_name}")
        return True

    def get_promotion_history(self, officer_id: int) -> List[PromotionHistory]:
        rows = self.db.fetchall("""
            SELECT ph.*, o.full_name as officer_name
            FROM promotion_history ph
            JOIN officers o ON o.id = ph.officer_id
            WHERE ph.officer_id=?
            ORDER BY ph.promotion_date DESC
        """, (officer_id,))
        return [PromotionHistory(**{k: v for k, v in dict(r).items()
                                    if k in PromotionHistory.__dataclass_fields__})
                for r in rows]

    def add_promotion(self, ph: PromotionHistory) -> int:
        return self.db.execute("""
            INSERT INTO promotion_history(officer_id, previous_rank, new_rank,
                                          promotion_date, notes)
            VALUES (?,?,?,?,?)
        """, (ph.officer_id, ph.previous_rank, ph.new_rank, ph.promotion_date, ph.notes))

    @staticmethod
    def _row_to_officer(row: sqlite3.Row) -> Officer:
        d = dict(row)
        fields = Officer.__dataclass_fields__.keys()
        return Officer(**{k: d.get(k, "") or "" for k in fields
                          if k not in ("rank_name","department_name","unit_name")},
                       rank_name=d.get("rank_name") or "",
                       department_name=d.get("department_name") or "",
                       unit_name=d.get("unit_name") or "")

    def get_all_simple(self) -> List[Tuple[int, str, str]]:
        """Returns list of (id, officer_number, full_name) for dropdowns."""
        rows = self.db.fetchall(
            "SELECT id, officer_number, full_name FROM officers ORDER BY full_name")
        return [(r["id"], r["officer_number"], r["full_name"]) for r in rows]


# ======================================================================
# Reference Data Repository
# ======================================================================

class ReferenceRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_ranks(self) -> List[Rank]:
        rows = self.db.fetchall("SELECT * FROM ranks ORDER BY order_level DESC")
        return [Rank(id=r["id"], name=r["name"], order_level=r["order_level"]) for r in rows]

    def get_departments(self) -> List[Department]:
        rows = self.db.fetchall("SELECT * FROM departments ORDER BY name")
        return [Department(id=r["id"], name=r["name"], code=r["code"] or "") for r in rows]

    def get_units(self, department_id: int = None) -> List[Unit]:
        if department_id:
            rows = self.db.fetchall(
                "SELECT u.*, d.name as dept_name FROM units u "
                "LEFT JOIN departments d ON d.id=u.department_id "
                "WHERE u.department_id=? ORDER BY u.name", (department_id,))
        else:
            rows = self.db.fetchall(
                "SELECT u.*, d.name as dept_name FROM units u "
                "LEFT JOIN departments d ON d.id=u.department_id ORDER BY u.name")
        return [Unit(id=r["id"], name=r["name"],
                     department_id=r["department_id"],
                     department_name=r["dept_name"] or "") for r in rows]

    def get_leave_types(self) -> List[LeaveType]:
        rows = self.db.fetchall("SELECT * FROM leave_types ORDER BY name")
        return [LeaveType(id=r["id"], name=r["name"], max_days=r["max_days"]) for r in rows]


# ======================================================================
# Attendance Repository
# ======================================================================

class AttendanceRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self, date_filter: str = None, officer_id: int = None,
                status: str = None, search: str = None) -> List[AttendanceRecord]:
        sql = """
            SELECT a.*, o.full_name as officer_name, o.officer_number,
                   r.name as rank_name
            FROM attendance a
            JOIN officers o ON o.id = a.officer_id
            LEFT JOIN ranks r ON r.id = o.rank_id
            WHERE 1=1
        """
        params: list = []
        if date_filter:
            sql += " AND a.date = ?"
            params.append(date_filter)
        if officer_id:
            sql += " AND a.officer_id = ?"
            params.append(officer_id)
        if status:
            sql += " AND a.status = ?"
            params.append(status)
        if search:
            sql += " AND (o.full_name LIKE ? OR o.officer_number LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s])
        sql += " ORDER BY a.date DESC, o.full_name"
        return [self._to_record(r) for r in self.db.fetchall(sql, tuple(params))]

    def get_by_id(self, att_id: int) -> Optional[AttendanceRecord]:
        row = self.db.fetchone("""
            SELECT a.*, o.full_name as officer_name, o.officer_number,
                   r.name as rank_name
            FROM attendance a
            JOIN officers o ON o.id = a.officer_id
            LEFT JOIN ranks r ON r.id = o.rank_id
            WHERE a.id=?
        """, (att_id,))
        return self._to_record(row) if row else None

    def insert(self, rec: AttendanceRecord) -> int:
        return self.db.execute("""
            INSERT INTO attendance(officer_id, date, check_in, check_out, status, notes)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(officer_id, date) DO UPDATE SET
                check_in=excluded.check_in, check_out=excluded.check_out,
                status=excluded.status, notes=excluded.notes
        """, (rec.officer_id, rec.date, rec.check_in, rec.check_out, rec.status, rec.notes))

    def update(self, rec: AttendanceRecord) -> bool:
        self.db.execute("""
            UPDATE attendance SET check_in=?, check_out=?, status=?, notes=?
            WHERE id=?
        """, (rec.check_in, rec.check_out, rec.status, rec.notes, rec.id))
        return True

    def delete(self, att_id: int) -> bool:
        self.db.execute("DELETE FROM attendance WHERE id=?", (att_id,))
        return True

    def get_monthly_stats(self, year: int, month: int) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT o.officer_number, o.full_name,
                   SUM(CASE WHEN a.status='Present'  THEN 1 ELSE 0 END) as present_days,
                   SUM(CASE WHEN a.status='Late'     THEN 1 ELSE 0 END) as late_days,
                   SUM(CASE WHEN a.status='Absent'   THEN 1 ELSE 0 END) as absent_days,
                   SUM(CASE WHEN a.status='Leave'    THEN 1 ELSE 0 END) as leave_days
            FROM attendance a
            JOIN officers o ON o.id = a.officer_id
            WHERE strftime('%Y', a.date)=? AND strftime('%m', a.date)=?
            GROUP BY a.officer_id
            ORDER BY o.full_name
        """, (str(year), f"{month:02d}"))
        return [dict(r) for r in rows]

    @staticmethod
    def _to_record(row: sqlite3.Row) -> AttendanceRecord:
        d = dict(row)
        return AttendanceRecord(
            id=d.get("id", 0),
            officer_id=d.get("officer_id", 0),
            officer_name=d.get("officer_name", ""),
            officer_number=d.get("officer_number", ""),
            rank_name=d.get("rank_name", ""),
            date=d.get("date", ""),
            check_in=d.get("check_in", "") or "",
            check_out=d.get("check_out", "") or "",
            status=d.get("status", "Present"),
            notes=d.get("notes", "") or "",
            created_at=d.get("created_at", "")
        )


# ======================================================================
# Leave Repository
# ======================================================================

class LeaveRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self, officer_id: int = None, status: str = None,
                search: str = None) -> List[LeaveRequest]:
        sql = """
            SELECT lr.*, o.full_name as officer_name, o.officer_number,
                   r.name as rank_name, lt.name as leave_type_name
            FROM leave_requests lr
            JOIN officers o ON o.id = lr.officer_id
            LEFT JOIN ranks r    ON r.id = o.rank_id
            LEFT JOIN leave_types lt ON lt.id = lr.leave_type_id
            WHERE 1=1
        """
        params: list = []
        if officer_id:
            sql += " AND lr.officer_id=?"
            params.append(officer_id)
        if status:
            sql += " AND lr.approval_status=?"
            params.append(status)
        if search:
            sql += " AND (o.full_name LIKE ? OR o.officer_number LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s])
        sql += " ORDER BY lr.created_at DESC"
        return [self._to_leave(r) for r in self.db.fetchall(sql, tuple(params))]

    def get_by_id(self, leave_id: int) -> Optional[LeaveRequest]:
        row = self.db.fetchone("""
            SELECT lr.*, o.full_name as officer_name, o.officer_number,
                   r.name as rank_name, lt.name as leave_type_name
            FROM leave_requests lr
            JOIN officers o ON o.id = lr.officer_id
            LEFT JOIN ranks r    ON r.id = o.rank_id
            LEFT JOIN leave_types lt ON lt.id = lr.leave_type_id
            WHERE lr.id=?
        """, (leave_id,))
        return self._to_leave(row) if row else None

    def insert(self, lr: LeaveRequest) -> int:
        return self.db.execute("""
            INSERT INTO leave_requests(officer_id, leave_type_id, start_date,
                end_date, duration_days, use_accumulated, accumulated_days_used,
                approval_status, notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (lr.officer_id, lr.leave_type_id, lr.start_date, lr.end_date,
              lr.duration_days, int(lr.use_accumulated), lr.accumulated_days_used,
              lr.approval_status, lr.notes))

    def update(self, lr: LeaveRequest) -> bool:
        self.db.execute("""
            UPDATE leave_requests SET leave_type_id=?, start_date=?, end_date=?,
                duration_days=?, use_accumulated=?, accumulated_days_used=?,
                approval_status=?, approved_by=?, notes=?
            WHERE id=?
        """, (lr.leave_type_id, lr.start_date, lr.end_date, lr.duration_days,
              int(lr.use_accumulated), lr.accumulated_days_used,
              lr.approval_status, lr.approved_by, lr.notes, lr.id))
        return True

    def approve(self, leave_id: int, approved_by: str = "Admin") -> bool:
        self.db.execute(
            "UPDATE leave_requests SET approval_status='Approved', approved_by=? WHERE id=?",
            (approved_by, leave_id))
        return True

    def reject(self, leave_id: int) -> bool:
        self.db.execute(
            "UPDATE leave_requests SET approval_status='Rejected' WHERE id=?",
            (leave_id,))
        return True

    def delete(self, leave_id: int) -> bool:
        self.db.execute("DELETE FROM leave_requests WHERE id=?", (leave_id,))
        return True

    @staticmethod
    def _to_leave(row: sqlite3.Row) -> LeaveRequest:
        d = dict(row)
        return LeaveRequest(
            id=d.get("id", 0),
            officer_id=d.get("officer_id", 0),
            officer_name=d.get("officer_name", ""),
            officer_number=d.get("officer_number", ""),
            rank_name=d.get("rank_name", ""),
            leave_type_id=d.get("leave_type_id"),
            leave_type_name=d.get("leave_type_name", "") or "",
            start_date=d.get("start_date", ""),
            end_date=d.get("end_date", ""),
            duration_days=d.get("duration_days", 0) or 0,
            use_accumulated=bool(d.get("use_accumulated", 0)),
            accumulated_days_used=d.get("accumulated_days_used", 0) or 0,
            approval_status=d.get("approval_status", "Pending"),
            approved_by=d.get("approved_by", "") or "",
            request_date=d.get("request_date", ""),
            notes=d.get("notes", "") or "",
            created_at=d.get("created_at", "")
        )


# ======================================================================
# Leave Accumulation Repository
# ======================================================================

class LeaveAccumulationRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self, officer_id: int = None, status: str = None,
                search: str = None) -> List[LeaveAccumulationRequest]:
        sql = """
            SELECT lr.*, o.officer_number, o.full_name as officer_name,
                   r.name as rank_name
            FROM leave_accumulation_requests lr
            JOIN officers o ON o.id = lr.officer_id
            LEFT JOIN ranks r ON r.id = o.rank_id
            WHERE 1=1
        """
        params: list = []
        if officer_id:
            sql += " AND lr.officer_id = ?"
            params.append(officer_id)
        if status:
            sql += " AND lr.approval_status = ?"
            params.append(status)
        if search:
            sql += " AND (o.full_name LIKE ? OR o.officer_number LIKE ? OR lr.request_reason LIKE ? )"
            s = f"%{search}%"
            params.extend([s, s, s])
        sql += " ORDER BY lr.request_date DESC"
        rows = self.db.fetchall(sql, tuple(params))
        return [self._to_accumulation_request(row) for row in rows]

    def get_by_id(self, request_id: int) -> Optional[LeaveAccumulationRequest]:
        row = self.db.fetchone("""
            SELECT lr.*, o.officer_number, o.full_name as officer_name,
                   r.name as rank_name
            FROM leave_accumulation_requests lr
            JOIN officers o ON o.id = lr.officer_id
            LEFT JOIN ranks r ON r.id = o.rank_id
            WHERE lr.id = ?
        """, (request_id,))
        return self._to_accumulation_request(row) if row else None

    def get_balance(self, officer_id: int) -> Dict[str, int]:
        earned_row = self.db.fetchone(
            "SELECT COALESCE(SUM(requested_days), 0) as earned "
            "FROM leave_accumulation_requests "
            "WHERE officer_id = ? AND approval_status = 'Approved'",
            (officer_id,)
        )
        used_row = self.db.fetchone(
            "SELECT COALESCE(SUM(accumulated_days_used), 0) as used "
            "FROM leave_requests "
            "WHERE officer_id = ? AND approval_status = 'Approved' "
            "AND use_accumulated = 1",
            (officer_id,)
        )
        return {
            "earned_days": earned_row["earned"] if earned_row else 0,
            "used_days": used_row["used"] if used_row else 0,
        }

    def get_aggregate_balance(self) -> Dict[str, int]:
        earned_row = self.db.fetchone(
            "SELECT COALESCE(SUM(requested_days), 0) as total_earned "
            "FROM leave_accumulation_requests "
            "WHERE approval_status = 'Approved'"
        )
        used_row = self.db.fetchone(
            "SELECT COALESCE(SUM(accumulated_days_used), 0) as total_used "
            "FROM leave_requests "
            "WHERE approval_status = 'Approved' AND use_accumulated = 1"
        )
        total_earned = earned_row["total_earned"] if earned_row else 0
        total_used = used_row["total_used"] if used_row else 0
        return {
            "total_earned": total_earned,
            "total_used": total_used,
            "available": max(0, total_earned - total_used),
        }

    def insert(self, lr: LeaveAccumulationRequest) -> int:
        return self.db.execute("""
            INSERT INTO leave_accumulation_requests(
                officer_id, requested_days, request_reason,
                approval_status, notes
            ) VALUES (?,?,?,?,?)
        """, (lr.officer_id, lr.requested_days, lr.request_reason,
              lr.approval_status, lr.notes))

    def update(self, lr: LeaveAccumulationRequest) -> bool:
        self.db.execute("""
            UPDATE leave_accumulation_requests SET
                officer_id=?, requested_days=?, request_reason=?,
                approval_status=?, approved_by=?, reviewed_at=?, notes=?
            WHERE id=?
        """, (lr.officer_id, lr.requested_days, lr.request_reason,
              lr.approval_status, lr.approved_by, lr.reviewed_at,
              lr.notes, lr.id))
        return True

    def approve(self, request_id: int, approved_by: str = "Admin") -> bool:
        self.db.execute(
            "UPDATE leave_accumulation_requests SET approval_status='Approved', "
            "approved_by=?, reviewed_at=datetime('now') WHERE id=?",
            (approved_by, request_id))
        return True

    def reject(self, request_id: int) -> bool:
        self.db.execute(
            "UPDATE leave_accumulation_requests SET approval_status='Rejected', "
            "reviewed_at=datetime('now') WHERE id=?",
            (request_id,))
        return True

    def delete(self, request_id: int) -> bool:
        self.db.execute("DELETE FROM leave_accumulation_requests WHERE id=?", (request_id,))
        return True

    @staticmethod
    def _to_accumulation_request(row: sqlite3.Row) -> LeaveAccumulationRequest:
        d = dict(row)
        return LeaveAccumulationRequest(
            id=d.get("id", 0),
            officer_id=d.get("officer_id", 0),
            officer_name=d.get("officer_name", ""),
            officer_number=d.get("officer_number", ""),
            rank_name=d.get("rank_name", ""),
            requested_days=d.get("requested_days", 0) or 0,
            approval_status=d.get("approval_status", "Pending"),
            approved_by=d.get("approved_by", "") or "",
            request_reason=d.get("request_reason", "") or "",
            reviewed_at=d.get("reviewed_at", ""),
            request_date=d.get("request_date", ""),
            notes=d.get("notes", "") or "",
            created_at=d.get("created_at", "")
        )


class DutyRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self, date_filter: str = None, officer_id: int = None,
                status: str = None, search: str = None) -> List[DailyDuty]:
        sql = """
            SELECT dd.*, o.full_name as officer_name, o.officer_number,
                   r.name as rank_name
            FROM daily_duties dd
            JOIN officers o ON o.id = dd.officer_id
            LEFT JOIN ranks r ON r.id = o.rank_id
            WHERE 1=1
        """
        params: list = []
        if date_filter:
            sql += " AND dd.duty_date=?"
            params.append(date_filter)
        if officer_id:
            sql += " AND dd.officer_id=?"
            params.append(officer_id)
        if status:
            sql += " AND dd.completion_status=?"
            params.append(status)
        if search:
            sql += " AND (o.full_name LIKE ? OR dd.assignment LIKE ? OR dd.duty_location LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s])
        sql += " ORDER BY dd.duty_date DESC, o.full_name"
        return [self._to_duty(r) for r in self.db.fetchall(sql, tuple(params))]

    def get_by_id(self, duty_id: int) -> Optional[DailyDuty]:
        row = self.db.fetchone("""
            SELECT dd.*, o.full_name as officer_name, o.officer_number,
                   r.name as rank_name
            FROM daily_duties dd
            JOIN officers o ON o.id = dd.officer_id
            LEFT JOIN ranks r ON r.id = o.rank_id
            WHERE dd.id=?
        """, (duty_id,))
        return self._to_duty(row) if row else None

    def insert(self, d: DailyDuty) -> int:
        return self.db.execute("""
            INSERT INTO daily_duties(officer_id, duty_date, shift, assignment,
                                     duty_location, notes, completion_status)
            VALUES (?,?,?,?,?,?,?)
        """, (d.officer_id, d.duty_date, d.shift, d.assignment,
              d.duty_location, d.notes, d.completion_status))

    def update(self, d: DailyDuty) -> bool:
        self.db.execute("""
            UPDATE daily_duties SET duty_date=?, shift=?, assignment=?,
                duty_location=?, notes=?, completion_status=?
            WHERE id=?
        """, (d.duty_date, d.shift, d.assignment, d.duty_location,
              d.notes, d.completion_status, d.id))
        return True

    def delete(self, duty_id: int) -> bool:
        self.db.execute("DELETE FROM daily_duties WHERE id=?", (duty_id,))
        return True

    @staticmethod
    def _to_duty(row: sqlite3.Row) -> DailyDuty:
        d = dict(row)
        return DailyDuty(
            id=d.get("id", 0),
            officer_id=d.get("officer_id", 0),
            officer_name=d.get("officer_name", ""),
            officer_number=d.get("officer_number", ""),
            rank_name=d.get("rank_name", ""),
            duty_date=d.get("duty_date", ""),
            shift=d.get("shift", "") or "",
            assignment=d.get("assignment", "") or "",
            duty_location=d.get("duty_location", "") or "",
            notes=d.get("notes", "") or "",
            completion_status=d.get("completion_status", "Pending"),
            created_at=d.get("created_at", "")
        )


# ======================================================================
# Meals Repository
# ======================================================================

class MealRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self, date_filter: str = None, officer_id: int = None,
                meal_type: str = None, search: str = None) -> List[MealRecord]:
        sql = """
            SELECT ml.*, o.full_name as officer_name, o.officer_number,
                   r.name as rank_name
            FROM meals_log ml
            JOIN officers o ON o.id = ml.officer_id
            LEFT JOIN ranks r ON r.id = o.rank_id
            WHERE 1=1
        """
        params: list = []
        if date_filter:
            sql += " AND ml.meal_date=?"
            params.append(date_filter)
        if officer_id:
            sql += " AND ml.officer_id=?"
            params.append(officer_id)
        if meal_type:
            sql += " AND ml.meal_type=?"
            params.append(meal_type)
        if search:
            sql += " AND (o.full_name LIKE ? OR o.officer_number LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s])
        sql += " ORDER BY ml.meal_date DESC, o.full_name"
        return [self._to_meal(r) for r in self.db.fetchall(sql, tuple(params))]

    def get_by_id(self, meal_id: int) -> Optional[MealRecord]:
        row = self.db.fetchone("""
            SELECT ml.*, o.full_name as officer_name, o.officer_number,
                   r.name as rank_name
            FROM meals_log ml
            JOIN officers o ON o.id = ml.officer_id
            LEFT JOIN ranks r ON r.id = o.rank_id
            WHERE ml.id=?
        """, (meal_id,))
        return self._to_meal(row) if row else None

    def insert(self, m: MealRecord) -> int:
        return self.db.execute("""
            INSERT INTO meals_log(officer_id, meal_date, meal_type, quantity, notes)
            VALUES (?,?,?,?,?)
        """, (m.officer_id, m.meal_date, m.meal_type, m.quantity, m.notes))

    def update(self, m: MealRecord) -> bool:
        self.db.execute("""
            UPDATE meals_log SET meal_date=?, meal_type=?, quantity=?, notes=?
            WHERE id=?
        """, (m.meal_date, m.meal_type, m.quantity, m.notes, m.id))
        return True

    def delete(self, meal_id: int) -> bool:
        self.db.execute("DELETE FROM meals_log WHERE id=?", (meal_id,))
        return True

    def get_daily_summary(self, date_str: str) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT meal_type, SUM(quantity) as total
            FROM meals_log WHERE meal_date=?
            GROUP BY meal_type
        """, (date_str,))
        return [dict(r) for r in rows]

    def get_monthly_summary(self, year: int, month: int) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT o.full_name, o.officer_number,
                   SUM(CASE WHEN ml.meal_type='Breakfast' THEN ml.quantity ELSE 0 END) as breakfast,
                   SUM(CASE WHEN ml.meal_type='Lunch'     THEN ml.quantity ELSE 0 END) as lunch,
                   SUM(CASE WHEN ml.meal_type='Dinner'    THEN ml.quantity ELSE 0 END) as dinner,
                   SUM(ml.quantity) as total
            FROM meals_log ml
            JOIN officers o ON o.id = ml.officer_id
            WHERE strftime('%Y',ml.meal_date)=? AND strftime('%m',ml.meal_date)=?
            GROUP BY ml.officer_id ORDER BY o.full_name
        """, (str(year), f"{month:02d}"))
        return [dict(r) for r in rows]

    @staticmethod
    def _to_meal(row: sqlite3.Row) -> MealRecord:
        d = dict(row)
        return MealRecord(
            id=d.get("id", 0),
            officer_id=d.get("officer_id", 0),
            officer_name=d.get("officer_name", ""),
            officer_number=d.get("officer_number", ""),
            rank_name=d.get("rank_name", ""),
            meal_date=d.get("meal_date", ""),
            meal_type=d.get("meal_type", ""),
            quantity=d.get("quantity", 1),
            notes=d.get("notes", "") or "",
            created_at=d.get("created_at", "")
        )


# ======================================================================
# Global Search Repository
# ======================================================================
class GlobalSearchRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def search(self, query: str, filters: Dict[str, Any], limit: int = 200) -> List[Dict[str, Any]]:
        q = (query or "").strip()
        like = f"%{q}%"
        status = (filters.get("status") or "").strip()
        dept_id = filters.get("department_id")
        date_from = (filters.get("date_from") or "").strip()
        date_to = (filters.get("date_to") or "").strip()
        category = (filters.get("category") or "All").strip()

        per_bucket = max(25, min(80, limit // 4))
        rows: List[Dict[str, Any]] = []

        if category in ("All", "Officers"):
            sql = """
                SELECT o.id as record_id, o.full_name as title,
                       o.officer_number as code, o.current_status as status,
                       o.date_of_joining as date_value,
                       COALESCE(d.name, '') as department,
                       COALESCE(u.name, '') as unit_name,
                       COALESCE(r.name, '') as rank_name,
                       COALESCE(o.notes, '') as notes
                FROM officers o
                LEFT JOIN departments d ON d.id = o.department_id
                LEFT JOIN units u ON u.id = o.unit_id
                LEFT JOIN ranks r ON r.id = o.rank_id
                WHERE (? = '' OR o.full_name LIKE ? COLLATE NOCASE
                       OR o.officer_number LIKE ? COLLATE NOCASE
                       OR d.name LIKE ? COLLATE NOCASE
                       OR u.name LIKE ? COLLATE NOCASE
                       OR o.notes LIKE ? COLLATE NOCASE)
                  AND (? = '' OR o.current_status = ?)
                  AND (? IS NULL OR o.department_id = ?)
                ORDER BY o.updated_at DESC, o.full_name
                LIMIT ?
            """
            params = (q, like, like, like, like, like, status, status, dept_id, dept_id, per_bucket)
            for r in self.db.fetchall(sql, params):
                d = dict(r)
                d["category"] = "Officers"
                d["snippet"] = f"{d['rank_name']} • {d['department']} / {d['unit_name']} • #{d['code']}"
                rows.append(d)

        if category in ("All", "Leaves"):
            sql = """
                SELECT lr.id as record_id, o.full_name as title,
                       o.officer_number as code, lr.approval_status as status,
                       lr.start_date as date_value,
                       COALESCE(d.name, '') as department,
                       COALESCE(lt.name, 'Leave') as leave_type,
                       COALESCE(lr.notes, '') as notes
                FROM leave_requests lr
                JOIN officers o ON o.id = lr.officer_id
                LEFT JOIN departments d ON d.id = o.department_id
                LEFT JOIN leave_types lt ON lt.id = lr.leave_type_id
                WHERE (? = '' OR o.full_name LIKE ? COLLATE NOCASE
                       OR o.officer_number LIKE ? COLLATE NOCASE
                       OR lt.name LIKE ? COLLATE NOCASE
                       OR lr.notes LIKE ? COLLATE NOCASE
                       OR lr.start_date LIKE ? COLLATE NOCASE
                       OR lr.end_date LIKE ? COLLATE NOCASE)
                  AND (? = '' OR lr.approval_status = ?)
                  AND (? IS NULL OR o.department_id = ?)
                  AND (? = '' OR lr.start_date >= ?)
                  AND (? = '' OR lr.end_date <= ?)
                ORDER BY lr.created_at DESC
                LIMIT ?
            """
            params = (
                q, like, like, like, like, like, like,
                status, status, dept_id, dept_id, date_from, date_from, date_to, date_to, per_bucket
            )
            for r in self.db.fetchall(sql, params):
                d = dict(r)
                d["category"] = "Leaves"
                d["snippet"] = f"{d['leave_type']} • #{d['code']} • {d['notes']}"
                rows.append(d)

        if category in ("All", "Penalties"):
            sql = """
                SELECT p.id as record_id, o.full_name as title,
                       o.officer_number as code, p.status as status,
                       p.issue_date as date_value,
                       COALESCE(d.name, '') as department,
                       COALESCE(p.penalty_type, '') as penalty_type,
                       COALESCE(p.description, '') as notes
                FROM disciplinary_penalties p
                JOIN officers o ON o.id = p.officer_id
                LEFT JOIN departments d ON d.id = o.department_id
                WHERE (? = '' OR o.full_name LIKE ? COLLATE NOCASE
                       OR o.officer_number LIKE ? COLLATE NOCASE
                       OR p.penalty_type LIKE ? COLLATE NOCASE
                       OR p.description LIKE ? COLLATE NOCASE
                       OR p.issue_date LIKE ? COLLATE NOCASE)
                  AND (? = '' OR p.status = ?)
                  AND (? IS NULL OR o.department_id = ?)
                  AND (? = '' OR p.issue_date >= ?)
                  AND (? = '' OR p.issue_date <= ?)
                ORDER BY p.created_at DESC
                LIMIT ?
            """
            params = (
                q, like, like, like, like, like,
                status, status, dept_id, dept_id, date_from, date_from, date_to, date_to, per_bucket
            )
            for r in self.db.fetchall(sql, params):
                d = dict(r)
                d["category"] = "Penalties"
                d["snippet"] = f"{d['penalty_type']} • #{d['code']} • {d['notes']}"
                rows.append(d)

        if category in ("All", "Appeals"):
            sql = """
                SELECT a.id as record_id, o.full_name as title,
                       o.officer_number as code, a.status as status,
                       a.submission_date as date_value,
                       COALESCE(d.name, '') as department,
                       COALESCE(a.appeal_reason, '') as appeal_reason,
                       COALESCE(a.explanation, '') as notes
                FROM appeal_requests a
                JOIN officers o ON o.id = a.officer_id
                LEFT JOIN departments d ON d.id = o.department_id
                WHERE (? = '' OR o.full_name LIKE ? COLLATE NOCASE
                       OR o.officer_number LIKE ? COLLATE NOCASE
                       OR a.appeal_reason LIKE ? COLLATE NOCASE
                       OR a.explanation LIKE ? COLLATE NOCASE
                       OR a.submission_date LIKE ? COLLATE NOCASE)
                  AND (? = '' OR a.status = ?)
                  AND (? IS NULL OR o.department_id = ?)
                  AND (? = '' OR a.submission_date >= ?)
                  AND (? = '' OR a.submission_date <= ?)
                ORDER BY a.created_at DESC
                LIMIT ?
            """
            params = (
                q, like, like, like, like, like,
                status, status, dept_id, dept_id, date_from, date_from, date_to, date_to, per_bucket
            )
            for r in self.db.fetchall(sql, params):
                d = dict(r)
                d["category"] = "Appeals"
                d["snippet"] = f"{d['appeal_reason']} • #{d['code']} • {d['notes']}"
                rows.append(d)

        if category in ("All", "Accumulation"):
            sql = """
                SELECT ar.id as record_id, o.full_name as title,
                       o.officer_number as code, ar.approval_status as status,
                       ar.request_date as date_value,
                       COALESCE(d.name, '') as department,
                       CAST(ar.requested_days AS TEXT) as requested_days,
                       COALESCE(ar.request_reason, '') as notes
                FROM leave_accumulation_requests ar
                JOIN officers o ON o.id = ar.officer_id
                LEFT JOIN departments d ON d.id = o.department_id
                WHERE (? = '' OR o.full_name LIKE ? COLLATE NOCASE
                       OR o.officer_number LIKE ? COLLATE NOCASE
                       OR ar.request_reason LIKE ? COLLATE NOCASE
                       OR ar.request_date LIKE ? COLLATE NOCASE)
                  AND (? = '' OR ar.approval_status = ?)
                  AND (? IS NULL OR o.department_id = ?)
                  AND (? = '' OR ar.request_date >= ?)
                  AND (? = '' OR ar.request_date <= ?)
                ORDER BY ar.created_at DESC
                LIMIT ?
            """
            params = (
                q, like, like, like, like,
                status, status, dept_id, dept_id, date_from, date_from, date_to, date_to, per_bucket
            )
            for r in self.db.fetchall(sql, params):
                d = dict(r)
                d["category"] = "Accumulation"
                d["snippet"] = f"Requested {d['requested_days']} days • #{d['code']} • {d['notes']}"
                rows.append(d)

        return rows[:limit]
