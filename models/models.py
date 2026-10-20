"""
Data Models - Officers Affairs Management System
Pure dataclasses representing domain entities.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import date, datetime


@dataclass
class Rank:
    id: int = 0
    name: str = ""
    order_level: int = 0


@dataclass
class Department:
    id: int = 0
    name: str = ""
    code: str = ""


@dataclass
class Unit:
    id: int = 0
    name: str = ""
    department_id: Optional[int] = None
    department_name: str = ""


@dataclass
class Officer:
    id: int = 0
    officer_number: str = ""
    full_name: str = ""
    rank_id: Optional[int] = None
    rank_name: str = ""
    national_id: str = ""
    date_of_birth: str = ""
    address: str = ""
    phone: str = ""
    emergency_contact: str = ""
    photo_path: str = ""
    job_position: str = ""
    current_status: str = "Active"
    eligible_for_accumulation: bool = False
    accumulation_limit_days: int = 0
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    @property
    def display_name(self) -> str:
        if self.rank_name:
            return f"{self.rank_name} / {self.full_name}"
        return self.full_name

    @property
    def age(self) -> str:
        if not self.date_of_birth:
            return ""
        try:
            dob = datetime.strptime(self.date_of_birth, "%Y-%m-%d")
            today = datetime.today()
            years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return str(years)
        except ValueError:
            return ""


@dataclass
class PromotionHistory:
    id: int = 0
    officer_id: int = 0
    officer_name: str = ""
    previous_rank: str = ""
    new_rank: str = ""
    promotion_date: str = ""
    notes: str = ""
    created_at: str = ""


@dataclass
class AttendanceRecord:
    id: int = 0
    officer_id: int = 0
    officer_name: str = ""
    officer_number: str = ""
    rank_name: str = ""
    date: str = ""
    check_in: str = ""
    check_out: str = ""
    status: str = "Present"
    notes: str = ""
    created_at: str = ""

    STATUS_COLORS = {
        "Present":  "#22c55e",
        "Late":     "#f59e0b",
        "Absent":   "#ef4444",
        "Leave":    "#3b82f6",
    }

    @property
    def status_color(self) -> str:
        return self.STATUS_COLORS.get(self.status, "#6b7280")


@dataclass
class LeaveType:
    id: int = 0
    name: str = ""
    max_days: Optional[int] = None


@dataclass
class LeaveRequest:
    id: int = 0
    officer_id: int = 0
    officer_name: str = ""
    officer_number: str = ""
    rank_name: str = ""
    leave_type_id: Optional[int] = None
    leave_type_name: str = ""
    start_date: str = ""
    end_date: str = ""
    duration_days: int = 0
    use_accumulated: bool = False
    accumulated_days_used: int = 0
    approval_status: str = "Pending"
    approved_by: str = ""
    request_date: str = ""
    notes: str = ""
    created_at: str = ""

    STATUS_COLORS = {
        "Pending":  "#f59e0b",
        "Approved": "#22c55e",
        "Rejected": "#ef4444",
    }

    @property
    def status_color(self) -> str:
        return self.STATUS_COLORS.get(self.approval_status, "#6b7280")


@dataclass
class LeaveAccumulationRequest:
    id: int = 0
    officer_id: int = 0
    officer_name: str = ""
    officer_number: str = ""
    rank_name: str = ""
    requested_days: int = 0
    approval_status: str = "Pending"
    approved_by: str = ""
    request_reason: str = ""
    reviewed_at: str = ""
    request_date: str = ""
    notes: str = ""
    created_at: str = ""

    STATUS_COLORS = {
        "Pending":  "#f59e0b",
        "Approved": "#22c55e",
        "Rejected": "#ef4444",
    }

    @property
    def status_color(self) -> str:
        return self.STATUS_COLORS.get(self.approval_status, "#6b7280")


@dataclass
class DailyDuty:
    id: int = 0
    officer_id: int = 0
    officer_name: str = ""
    officer_number: str = ""
    rank_name: str = ""
    duty_date: str = ""
    shift: str = ""
    assignment: str = ""
    duty_location: str = ""
    notes: str = ""
    completion_status: str = "Pending"
    created_at: str = ""

    STATUS_COLORS = {
        "Pending":   "#f59e0b",
        "Completed": "#22c55e",
        "Cancelled": "#ef4444",
        "Partial":   "#3b82f6",
    }

    @property
    def status_color(self) -> str:
        return self.STATUS_COLORS.get(self.completion_status, "#6b7280")


@dataclass
class MealRecord:
    id: int = 0
    officer_id: int = 0
    officer_name: str = ""
    officer_number: str = ""
    rank_name: str = ""
    meal_date: str = ""
    meal_type: str = ""
    quantity: int = 1
    notes: str = ""
    created_at: str = ""

    MEAL_COLORS = {
        "Breakfast": "#f59e0b",
        "Lunch":     "#22c55e",
        "Dinner":    "#3b82f6",
        "Snack":     "#a855f7",
    }

    @property
    def meal_color(self) -> str:
        return self.MEAL_COLORS.get(self.meal_type, "#6b7280")


@dataclass
class DisciplinaryPenalty:
    id: int = 0
    officer_id: int = 0
    officer_name: str = ""
    officer_number: str = ""
    penalty_type: str = ""
    description: str = ""
    issue_date: str = ""
    severity_level: str = "Low"
    status: str = "Issued"
    supporting_document: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class AppealRequest:
    id: int = 0
    penalty_id: int = 0
    officer_id: int = 0
    officer_name: str = ""
    officer_number: str = ""
    penalty_type: str = ""
    appeal_reason: str = ""
    explanation: str = ""
    attachment_path: str = ""
    submission_date: str = ""
    status: str = "Pending"
    created_at: str = ""
    updated_at: str = ""


@dataclass
class AppealReview:
    id: int = 0
    appeal_id: int = 0
    reviewer: str = ""
    review_date: str = ""
    status: str = ""
    comments: str = ""
    created_at: str = ""


@dataclass
class Attachment:
    id: int = 0
    record_type: str = ""
    record_id: int = 0
    file_name: str = ""
    file_path: str = ""
    created_at: str = ""
