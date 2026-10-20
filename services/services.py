"""
Services Layer - Officers Affairs Management System
Business logic and orchestration between repositories.
"""

import logging
import os
import shutil
import re
import unicodedata
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Dict
from pathlib import Path
from difflib import SequenceMatcher

from database.db_manager import DatabaseManager
from models.models import (
    Officer, Rank, Department, Unit, PromotionHistory,
    AttendanceRecord, LeaveType, LeaveRequest, LeaveAccumulationRequest,
    DailyDuty, MealRecord
)
from repositories.repositories import (
    OfficerRepository, ReferenceRepository, AttendanceRepository,
    LeaveRepository, LeaveAccumulationRepository, DutyRepository, MealRepository,
    GlobalSearchRepository
)

logger = logging.getLogger(__name__)


class ServiceLocator:
    """Simple dependency injection container."""

    def __init__(self, db_path: str = "data/officers_affairs.db"):
        self.db = DatabaseManager(db_path)
        self.officers     = OfficerService(self.db)
        self.attendance   = AttendanceService(self.db)
        self.leaves       = LeaveService(self.db)
        self.accumulation = LeaveAccumulationService(self.db)
        self.duties       = DutyService(self.db)
        self.meals        = MealService(self.db)
        self.reference    = ReferenceService(self.db)
        self.dashboard    = DashboardService(self.db)
        self.search       = SearchService(self.db)


# ======================================================================
class OfficerService:
    def __init__(self, db: DatabaseManager):
        self._repo = OfficerRepository(db)
        self._ref  = ReferenceRepository(db)

    def get_all(self, status=None, department_id=None, search=None):
        return self._repo.get_all(status, department_id, search)

    def get_by_id(self, officer_id: int):
        return self._repo.get_by_id(officer_id)

    def save(self, officer: Officer) -> Tuple[bool, str]:
        """Insert or update; returns (success, message)."""
        try:
            officer.marital_status = officer.marital_status or None
            officer.blood_type = officer.blood_type or None
            officer.current_status = officer.current_status or "Active"

            if not officer.full_name.strip():
                return False, "Full name is required."
            if not officer.officer_number.strip():
                return False, "Officer number is required."
            if officer.id:
                self._repo.update(officer)
                return True, f"Officer '{officer.full_name}' updated successfully."
            else:
                new_id = self._repo.insert(officer)
                officer.id = new_id
                return True, f"Officer '{officer.full_name}' added successfully."
        except Exception as e:
            logger.error(f"Save officer error: {e}")
            if "UNIQUE" in str(e):
                return False, "Officer number or National ID already exists."
            return False, str(e)

    def delete(self, officer_id: int) -> Tuple[bool, str]:
        try:
            self._repo.delete(officer_id)
            return True, "Officer deleted."
        except Exception as e:
            return False, str(e)

    def get_all_simple(self):
        return self._repo.get_all_simple()

    def get_promotion_history(self, officer_id: int):
        return self._repo.get_promotion_history(officer_id)

    def add_promotion(self, ph: PromotionHistory) -> Tuple[bool, str]:
        try:
            if not ph.previous_rank and ph.officer_id:
                officer = self._repo.get_by_id(ph.officer_id)
                ph.previous_rank = officer.rank_name if officer else ""

            self._repo.add_promotion(ph)
            # Update officer rank if new rank exists
            if ph.new_rank:
                for rank in self._ref.get_ranks():
                    if rank.name == ph.new_rank:
                        officer = self._repo.get_by_id(ph.officer_id)
                        if officer:
                            officer.rank_id = rank.id
                            self._repo.update(officer)
                        break
            return True, "Promotion recorded."
        except Exception as e:
            return False, str(e)

    def save_photo(self, officer_id: int, src_path: str) -> str:
        """Copy photo to photos directory and return new path."""
        photos_dir = Path("data/photos")
        photos_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(src_path).suffix
        dest = photos_dir / f"officer_{officer_id}{ext}"
        shutil.copy2(src_path, dest)
        return str(dest)


# ======================================================================
class ReferenceService:
    def __init__(self, db: DatabaseManager):
        self._repo = ReferenceRepository(db)

    def get_ranks(self):   return self._repo.get_ranks()
    def get_departments(self): return self._repo.get_departments()
    def get_units(self, dept_id=None): return self._repo.get_units(dept_id)
    def get_leave_types(self): return self._repo.get_leave_types()


# ======================================================================
class AttendanceService:
    def __init__(self, db: DatabaseManager):
        self._repo = AttendanceRepository(db)

    def get_all(self, date_filter=None, officer_id=None, status=None, search=None):
        return self._repo.get_all(date_filter, officer_id, status, search)

    def get_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return self._repo.get_all(date_filter=today)

    def get_by_id(self, att_id: int):
        return self._repo.get_by_id(att_id)

    def save(self, rec: AttendanceRecord) -> Tuple[bool, str]:
        try:
            if not rec.officer_id:
                return False, "Officer is required."
            if not rec.date:
                return False, "Date is required."
            rec.check_in = rec.check_in or None
            rec.check_out = rec.check_out or None
            rec.notes = rec.notes or None
            rec.status = rec.status or "Present"
            if rec.id:
                self._repo.update(rec)
            else:
                self._repo.insert(rec)
            return True, "Attendance record saved."
        except Exception as e:
            logger.error(f"Save attendance: {e}")
            return False, str(e)

    def delete(self, att_id: int) -> Tuple[bool, str]:
        try:
            self._repo.delete(att_id)
            return True, "Record deleted."
        except Exception as e:
            return False, str(e)

    def get_monthly_stats(self, year: int, month: int):
        return self._repo.get_monthly_stats(year, month)

    def bulk_mark(self, officer_ids: List[int], date_str: str,
                  status: str) -> Tuple[bool, str]:
        """Mark multiple officers' attendance at once."""
        try:
            for oid in officer_ids:
                rec = AttendanceRecord(officer_id=oid, date=date_str, status=status)
                self._repo.insert(rec)
            return True, f"Marked {len(officer_ids)} officers as {status}."
        except Exception as e:
            return False, str(e)


# ======================================================================
class LeaveService:
    def __init__(self, db: DatabaseManager):
        self._repo = LeaveRepository(db)
        self._acc_repo = LeaveAccumulationRepository(db)

    def get_all(self, officer_id=None, status=None, search=None):
        return self._repo.get_all(officer_id, status, search)

    def get_by_id(self, leave_id: int):
        return self._repo.get_by_id(leave_id)

    def save(self, lr: LeaveRequest) -> Tuple[bool, str]:
        try:
            if not lr.officer_id:
                return False, "Officer is required."
            if not lr.start_date or not lr.end_date:
                return False, "Start and end dates are required."
            lr.approval_status = lr.approval_status or "Pending"
            lr.notes = lr.notes or None
            # Calculate duration
            try:
                s = datetime.strptime(lr.start_date, "%Y-%m-%d")
                e = datetime.strptime(lr.end_date, "%Y-%m-%d")
                lr.duration_days = (e - s).days + 1
            except ValueError:
                return False, "Invalid date format (use YYYY-MM-DD)."
            if lr.duration_days < 1:
                return False, "End date must be after start date."
            if not lr.use_accumulated:
                lr.accumulated_days_used = 0
            if lr.use_accumulated:
                if lr.accumulated_days_used < 1:
                    return False, "Accumulated days used must be at least 1."
                if lr.accumulated_days_used > lr.duration_days:
                    return False, "Accumulated days used cannot exceed leave duration."
                balance = self._acc_repo.get_balance(lr.officer_id)
                available = max(0, balance["earned_days"] - balance["used_days"])
                if lr.accumulated_days_used > available:
                    return False, f"Insufficient accumulated balance. Available: {available} days."
            if lr.id:
                self._repo.update(lr)
            else:
                self._repo.insert(lr)
            return True, "Leave request saved."
        except Exception as e:
            return False, str(e)

    def approve(self, leave_id: int, approved_by: str = "Admin") -> Tuple[bool, str]:
        try:
            self._repo.approve(leave_id, approved_by)
            return True, "Leave request approved."
        except Exception as e:
            return False, str(e)

    def reject(self, leave_id: int) -> Tuple[bool, str]:
        try:
            self._repo.reject(leave_id)
            return True, "Leave request rejected."
        except Exception as e:
            return False, str(e)

    def delete(self, leave_id: int) -> Tuple[bool, str]:
        try:
            self._repo.delete(leave_id)
            return True, "Leave request deleted."
        except Exception as e:
            return False, str(e)


# ======================================================================
class LeaveAccumulationService:
    def __init__(self, db: DatabaseManager):
        self._repo = LeaveAccumulationRepository(db)
        self._officer_repo = OfficerRepository(db)
        self._leave_repo = LeaveRepository(db)

    def get_all(self, officer_id=None, status=None, search=None):
        return self._repo.get_all(officer_id, status, search)

    def get_by_id(self, request_id: int):
        return self._repo.get_by_id(request_id)

    def get_balance(self, officer_id: int):
        balance = self._repo.get_balance(officer_id)
        balance["available_days"] = max(0, balance["earned_days"] - balance["used_days"])
        return balance

    def get_aggregate_balance(self):
        balance = self._repo.get_aggregate_balance()
        return balance

    def save(self, lr: LeaveAccumulationRequest) -> Tuple[bool, str]:
        try:
            if not lr.officer_id:
                return False, "Officer is required."
            officer = self._officer_repo.get_by_id(lr.officer_id)
            if not officer:
                return False, "Officer not found."
            if not officer.eligible_for_accumulation:
                return False, "Officer is not eligible for leave accumulation."
            if lr.requested_days < 1:
                return False, "Requested days must be at least 1."
            balance = self.get_balance(lr.officer_id)
            available_days = balance["available_days"]
            if officer.accumulation_limit_days:
                max_allowed = officer.accumulation_limit_days
                if lr.approval_status == "Approved":
                    if available_days + lr.requested_days > max_allowed:
                        return False, (
                            f"Approval exceeds officer accumulation limit ({max_allowed} days). "
                            f"Current available: {available_days}."
                        )
                elif lr.requested_days > max_allowed:
                    return False, f"Requested days exceed officer's accumulation limit of {max_allowed}."
            lr.approval_status = lr.approval_status or "Pending"
            lr.notes = lr.notes or None
            if lr.id:
                self._repo.update(lr)
            else:
                self._repo.insert(lr)
            return True, "Accumulation request saved. Notification: balance/status updated."
        except Exception as e:
            return False, str(e)

    def approve(self, request_id: int, approved_by: str = "Admin") -> Tuple[bool, str]:
        try:
            req = self._repo.get_by_id(request_id)
            if not req:
                return False, "Accumulation request not found."
            officer = self._officer_repo.get_by_id(req.officer_id)
            if not officer:
                return False, "Officer not found."
            if not officer.eligible_for_accumulation:
                return False, "Officer is no longer eligible for accumulation."
            balance = self.get_balance(req.officer_id)
            available_days = balance["available_days"]
            if officer.accumulation_limit_days and available_days + req.requested_days > officer.accumulation_limit_days:
                return False, (
                    f"Cannot approve. Limit: {officer.accumulation_limit_days}, "
                    f"available now: {available_days}."
                )
            self._repo.approve(request_id, approved_by)
            updated = self.get_balance(req.officer_id)
            return True, (
                "Accumulation request approved. "
                f"Notification: Officer balance is now {updated['available_days']} available days."
            )
        except Exception as e:
            return False, str(e)

    def reject(self, request_id: int) -> Tuple[bool, str]:
        try:
            self._repo.reject(request_id)
            return True, "Accumulation request rejected. Notification: request status updated."
        except Exception as e:
            return False, str(e)

    def delete(self, request_id: int) -> Tuple[bool, str]:
        try:
            self._repo.delete(request_id)
            return True, "Accumulation request deleted."
        except Exception as e:
            return False, str(e)


# ======================================================================
class DutyService:
    def __init__(self, db: DatabaseManager):
        self._repo = DutyRepository(db)

    def get_all(self, date_filter=None, officer_id=None, status=None, search=None):
        return self._repo.get_all(date_filter, officer_id, status, search)

    def get_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return self._repo.get_all(date_filter=today)

    def get_by_id(self, duty_id: int):
        return self._repo.get_by_id(duty_id)

    def save(self, d: DailyDuty) -> Tuple[bool, str]:
        try:
            if not d.officer_id:
                return False, "Officer is required."
            if not d.duty_date:
                return False, "Duty date is required."
            d.shift = d.shift or None
            d.assignment = d.assignment or None
            d.duty_location = d.duty_location or None
            d.notes = d.notes or None
            d.completion_status = d.completion_status or "Pending"
            if d.id:
                self._repo.update(d)
            else:
                self._repo.insert(d)
            return True, "Duty record saved."
        except Exception as e:
            return False, str(e)

    def delete(self, duty_id: int) -> Tuple[bool, str]:
        try:
            self._repo.delete(duty_id)
            return True, "Duty deleted."
        except Exception as e:
            return False, str(e)


# ======================================================================
class MealService:
    def __init__(self, db: DatabaseManager):
        self._repo = MealRepository(db)

    def get_all(self, date_filter=None, officer_id=None, meal_type=None, search=None):
        return self._repo.get_all(date_filter, officer_id, meal_type, search)

    def get_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return self._repo.get_all(date_filter=today)

    def get_by_id(self, meal_id: int):
        return self._repo.get_by_id(meal_id)

    def save(self, m: MealRecord) -> Tuple[bool, str]:
        try:
            if not m.officer_id:
                return False, "Officer is required."
            if not m.meal_date:
                return False, "Date is required."
            if not m.meal_type:
                return False, "Meal type is required."
            m.meal_type = m.meal_type or None
            m.notes = m.notes or None
            if m.quantity is None:
                m.quantity = 1
            if m.id:
                self._repo.update(m)
            else:
                self._repo.insert(m)
            return True, "Meal record saved."
        except Exception as e:
            return False, str(e)

    def delete(self, meal_id: int) -> Tuple[bool, str]:
        try:
            self._repo.delete(meal_id)
            return True, "Meal record deleted."
        except Exception as e:
            return False, str(e)

    def get_daily_summary(self, date_str: str):
        return self._repo.get_daily_summary(date_str)

    def get_monthly_summary(self, year: int, month: int):
        return self._repo.get_monthly_summary(year, month)


# ======================================================================
class DashboardService:
    def __init__(self, db: DatabaseManager):
        self._db = db

    def get_stats(self) -> dict:
        return self._db.get_dashboard_stats()


# ======================================================================
class SearchService:
    def __init__(self, db: DatabaseManager):
        self._repo = GlobalSearchRepository(db)

    @staticmethod
    def _normalize_arabic_english(text: str) -> str:
        s = (text or "").strip().lower()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        trans = str.maketrans({
            "أ": "ا", "إ": "ا", "آ": "ا",
            "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي",
        })
        s = s.translate(trans)
        s = re.sub(r"\s+", " ", s)
        return s

    @staticmethod
    def _score(row: Dict[str, str], query: str) -> float:
        q = query.strip().lower()
        text = " ".join([
            str(row.get("title", "")),
            str(row.get("code", "")),
            str(row.get("department", "")),
            str(row.get("status", "")),
            str(row.get("snippet", "")),
            str(row.get("date_value", "")),
            str(row.get("category", "")),
        ]).lower()
        if not q:
            return 0.0
        score = 0.0
        if q in text:
            score += 50.0
        score += min(30.0, SequenceMatcher(None, q, text[:200]).ratio() * 30.0)
        if text.startswith(q):
            score += 15.0
        if row.get("status", "").lower() == q:
            score += 10.0
        return score

    @staticmethod
    def _highlight(text: str, query: str) -> str:
        if not text or not query:
            return text or ""
        q = re.escape(query.strip())
        if not q:
            return text
        return re.sub(f"({q})", r"[\1]", text, flags=re.IGNORECASE)

    def search(self, query: str, filters: Dict[str, str], limit: int = 200) -> List[Dict[str, str]]:
        rows = self._repo.search(query, filters, limit=limit * 2)
        norm_q = self._normalize_arabic_english(query)
        enriched = []
        for row in rows:
            t = str(row.get("title", ""))
            s = str(row.get("snippet", ""))
            norm_text = self._normalize_arabic_english(f"{t} {s}")
            score = self._score(row, query)
            if norm_q and norm_q in norm_text:
                score += 20.0
            if query and score < 14 and len(query) > 2:
                continue
            row["relevance"] = score
            row["title_h"] = self._highlight(t, query)
            row["snippet_h"] = self._highlight(s, query)
            enriched.append(row)
        enriched.sort(key=lambda x: (x.get("relevance", 0), x.get("date_value", "")), reverse=True)
        return enriched[:limit]

    def suggestions(self, query: str, filters: Dict[str, str], limit: int = 8) -> List[str]:
        if not query or len(query.strip()) < 2:
            return []
        rows = self.search(query, filters, limit=limit * 2)
        seen = set()
        out: List[str] = []
        for r in rows:
            label = f"{r.get('title','')} • {r.get('category','')}"
            if label not in seen:
                seen.add(label)
                out.append(label)
            if len(out) >= limit:
                break
        return out
