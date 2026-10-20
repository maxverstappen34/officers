"""
Database Manager - Officers Affairs Management System
Handles SQLite connection, migrations, and query execution.
"""

import sqlite3
import logging
import os
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Thread-safe SQLite database manager with connection pooling and migration support.
    """

    def __init__(self, db_path: str = "officers_affairs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def get_connection(self) -> sqlite3.Connection:
        """Return a configured SQLite connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -8000")  # 8 MB cache
        return conn

    @contextmanager
    def connection(self):
        """Context manager providing a transactional connection."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Initialisation & Migrations
    # ------------------------------------------------------------------

    def _init_database(self):
        """Create tables and seed reference data on first run."""
        schema_sqlite = Path(__file__).parent / "schema.sqlite"
        schema_sql = Path(__file__).parent / "schema.sql"
        if schema_sqlite.exists():
            schema_file = schema_sqlite
        elif schema_sql.exists():
            schema_file = schema_sql
        else:
            self._create_tables_inline()
            return

        with open(schema_file, "r", encoding="utf-8") as f:
            sql = f.read()
        with self.connection() as conn:
            conn.executescript(sql)
        self._run_migrations()
        logger.info(f"Database initialised from {schema_file.name}")

    def _run_migrations(self):
        """Apply lightweight schema migrations for leave accumulation support."""
        with self.connection() as conn:
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(officers)").fetchall()}
            if "eligible_for_accumulation" not in cols:
                conn.execute(
                    "ALTER TABLE officers ADD COLUMN eligible_for_accumulation INTEGER NOT NULL DEFAULT 0"
                )
            if "accumulation_limit_days" not in cols:
                conn.execute(
                    "ALTER TABLE officers ADD COLUMN accumulation_limit_days INTEGER NOT NULL DEFAULT 0"
                )

            leave_cols = {r["name"] for r in conn.execute("PRAGMA table_info(leave_requests)").fetchall()}
            if "use_accumulated" not in leave_cols:
                conn.execute(
                    "ALTER TABLE leave_requests ADD COLUMN use_accumulated INTEGER NOT NULL DEFAULT 0"
                )
            if "accumulated_days_used" not in leave_cols:
                conn.execute(
                    "ALTER TABLE leave_requests ADD COLUMN accumulated_days_used INTEGER NOT NULL DEFAULT 0"
                )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leave_accumulation_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    officer_id INTEGER NOT NULL REFERENCES officers(id) ON DELETE CASCADE,
                    requested_days INTEGER NOT NULL,
                    request_reason TEXT,
                    approval_status TEXT NOT NULL DEFAULT 'Pending',
                    approved_by TEXT,
                    reviewed_at TEXT,
                    request_date TEXT DEFAULT (datetime('now')),
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )

            # Global-search performance indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_officers_search_name ON officers(full_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_officers_search_number ON officers(officer_number)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leave_dates ON leave_requests(start_date, end_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leave_acc_dates ON leave_accumulation_requests(request_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_penalties_date ON disciplinary_penalties(issue_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_appeals_date ON appeal_requests(submission_date)")

    def _create_tables_inline(self):
        """Fallback: create tables programmatically if schema file missing."""
        ddl = """
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS ranks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            order_level INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS officers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            officer_number TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            rank_id INTEGER REFERENCES ranks(id) ON DELETE SET NULL,
            national_id TEXT UNIQUE,
            date_of_birth TEXT,
            address TEXT,
            phone TEXT,
            emergency_contact TEXT,
            marital_status TEXT,
            blood_type TEXT,
            photo_path TEXT,
            department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
            unit_id INTEGER REFERENCES units(id) ON DELETE SET NULL,
            job_position TEXT,
            date_of_joining TEXT,
            current_status TEXT NOT NULL DEFAULT 'Active',
            eligible_for_accumulation INTEGER NOT NULL DEFAULT 0,
            accumulation_limit_days INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_officers_number ON officers(officer_number);
        CREATE INDEX IF NOT EXISTS idx_officers_name ON officers(full_name);
        CREATE TABLE IF NOT EXISTS promotion_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            officer_id INTEGER NOT NULL REFERENCES officers(id) ON DELETE CASCADE,
            previous_rank TEXT,
            new_rank TEXT NOT NULL,
            promotion_date TEXT NOT NULL,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            officer_id INTEGER NOT NULL REFERENCES officers(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            status TEXT NOT NULL DEFAULT 'Present',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(officer_id, date)
        );
        CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
        CREATE TABLE IF NOT EXISTS leave_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            max_days INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            officer_id INTEGER NOT NULL REFERENCES officers(id) ON DELETE CASCADE,
            leave_type_id INTEGER REFERENCES leave_types(id) ON DELETE SET NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            duration_days INTEGER,
            use_accumulated INTEGER NOT NULL DEFAULT 0,
            accumulated_days_used INTEGER NOT NULL DEFAULT 0,
            approval_status TEXT NOT NULL DEFAULT 'Pending',
            approved_by TEXT,
            request_date TEXT DEFAULT (datetime('now')),
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS leave_accumulation_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            officer_id INTEGER NOT NULL REFERENCES officers(id) ON DELETE CASCADE,
            requested_days INTEGER NOT NULL,
            request_reason TEXT,
            approval_status TEXT NOT NULL DEFAULT 'Pending',
            approved_by TEXT,
            reviewed_at TEXT,
            request_date TEXT DEFAULT (datetime('now')),
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS daily_duties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            officer_id INTEGER NOT NULL REFERENCES officers(id) ON DELETE CASCADE,
            duty_date TEXT NOT NULL,
            shift TEXT,
            assignment TEXT,
            duty_location TEXT,
            notes TEXT,
            completion_status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS meals_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            officer_id INTEGER NOT NULL REFERENCES officers(id) ON DELETE CASCADE,
            meal_date TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS disciplinary_penalties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            officer_id INTEGER NOT NULL REFERENCES officers(id) ON DELETE CASCADE,
            penalty_type TEXT NOT NULL,
            description TEXT,
            issue_date TEXT NOT NULL,
            severity_level TEXT NOT NULL CHECK(severity_level IN ('Low','Medium','High','Critical')),
            status TEXT NOT NULL DEFAULT 'Issued' CHECK(status IN ('Issued','In Effect','Resolved','Waived')),
            supporting_document TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS appeal_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            penalty_id INTEGER NOT NULL REFERENCES disciplinary_penalties(id) ON DELETE CASCADE,
            officer_id INTEGER NOT NULL REFERENCES officers(id) ON DELETE CASCADE,
            appeal_reason TEXT NOT NULL,
            explanation TEXT,
            attachment_path TEXT,
            submission_date TEXT DEFAULT (datetime('now')),
            status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','Under Review','Approved','Rejected')),
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS appeal_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appeal_id INTEGER NOT NULL REFERENCES appeal_requests(id) ON DELETE CASCADE,
            reviewer TEXT NOT NULL,
            review_date TEXT DEFAULT (datetime('now')),
            status TEXT NOT NULL CHECK(status IN ('Approved','Rejected')),
            comments TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_type TEXT NOT NULL CHECK(record_type IN ('penalty','appeal')),
            record_id INTEGER NOT NULL,
            file_name TEXT,
            file_path TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            username TEXT DEFAULT 'system',
            timestamp TEXT DEFAULT (datetime('now'))
        );
        """
        with self.connection() as conn:
            conn.executescript(ddl)
            # Seed reference data
            conn.executemany(
                "INSERT OR IGNORE INTO ranks(name, order_level) VALUES (?,?)",
                [('General',10),('Brigadier General',9),('Colonel',8),
                 ('Lieutenant Colonel',7),('Major',6),('Captain',5),
                 ('First Lieutenant',4),('Lieutenant',3),
                 ('Warrant Officer',2),('Sergeant',1)]
            )
            conn.executemany(
                "INSERT OR IGNORE INTO departments(name, code) VALUES (?,?)",
                [('Operations','OPS'),('Criminal Investigation','CID'),
                 ('Traffic','TRF'),('Administration','ADM'),
                 ('Intelligence','INT'),('Community Policing','CMP'),
                 ('Forensics','FOR'),('K9 Unit','K9')]
            )
            conn.executemany(
                "INSERT OR IGNORE INTO leave_types(name, max_days) VALUES (?,?)",
                [('Annual Leave',30),('Sick Leave',15),('Emergency Leave',7),
                 ('Official Leave',14),('Special Leave',10),('Accumulated Leave',0)]
            )

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def fetchall(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        with self.connection() as conn:
            return conn.execute(sql, params).fetchall()

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        with self.connection() as conn:
            return conn.execute(sql, params).fetchone()

    def execute(self, sql: str, params: tuple = ()) -> int:
        """Execute DML; returns last inserted rowid or rowcount."""
        with self.connection() as conn:
            cur = conn.execute(sql, params)
            return cur.lastrowid or cur.rowcount

    def executemany(self, sql: str, params_list: List[tuple]) -> None:
        with self.connection() as conn:
            conn.executemany(sql, params_list)

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    def log_audit(self, table_name: str, record_id: int,
                  action: str, details: str = "", username: str = "system"):
        self.execute(
            "INSERT INTO audit_log(table_name,record_id,action,details,username) "
            "VALUES (?,?,?,?,?)",
            (table_name, record_id, action, details, username)
        )

    # ------------------------------------------------------------------
    # Stats (for dashboard)
    # ------------------------------------------------------------------

    def get_dashboard_stats(self) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        stats = {}

        row = self.fetchone("SELECT COUNT(*) as c FROM officers WHERE current_status='Active'")
        stats["active_officers"] = row["c"] if row else 0

        row = self.fetchone("SELECT COUNT(*) as c FROM officers")
        stats["total_officers"] = row["c"] if row else 0

        row = self.fetchone(
            "SELECT COUNT(*) as c FROM attendance WHERE date=? AND status='Present'", (today,))
        stats["present_today"] = row["c"] if row else 0

        row = self.fetchone(
            "SELECT COUNT(*) as c FROM attendance WHERE date=? AND status='Absent'", (today,))
        stats["absent_today"] = row["c"] if row else 0

        row = self.fetchone(
            "SELECT COUNT(*) as c FROM leave_requests WHERE approval_status='Approved' "
            "AND start_date<=? AND end_date>=?", (today, today))
        stats["on_leave"] = row["c"] if row else 0

        row = self.fetchone(
            "SELECT COUNT(*) as c FROM daily_duties WHERE duty_date=?", (today,))
        stats["duties_today"] = row["c"] if row else 0

        row = self.fetchone(
            "SELECT COUNT(*) as c FROM leave_requests WHERE approval_status='Pending'")
        stats["pending_leaves"] = row["c"] if row else 0

        # Attendance rate (last 30 days)
        rate_row = self.fetchone("""
            SELECT
                ROUND(100.0 * SUM(CASE WHEN status IN ('Present','Late') THEN 1 ELSE 0 END)
                      / MAX(COUNT(*), 1), 1) as rate
            FROM attendance
            WHERE date >= date('now','-30 days')
        """)
        stats["attendance_rate"] = rate_row["rate"] if rate_row and rate_row["rate"] else 0.0

        # Department distribution
        dept_rows = self.fetchall("""
            SELECT d.name, COUNT(o.id) as cnt
            FROM departments d
            LEFT JOIN officers o ON o.department_id = d.id AND o.current_status='Active'
            GROUP BY d.id ORDER BY cnt DESC LIMIT 8
        """)
        stats["dept_distribution"] = [(r["name"], r["cnt"]) for r in dept_rows]

        # Status distribution
        status_rows = self.fetchall("""
            SELECT current_status, COUNT(*) as cnt
            FROM officers GROUP BY current_status
        """)
        stats["status_distribution"] = [(r["current_status"], r["cnt"]) for r in status_rows]

        # Attendance last 7 days
        att_rows = self.fetchall("""
            SELECT date,
                   SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present,
                   SUM(CASE WHEN status='Late'    THEN 1 ELSE 0 END) as late,
                   SUM(CASE WHEN status='Absent'  THEN 1 ELSE 0 END) as absent
            FROM attendance
            WHERE date >= date('now','-6 days')
            GROUP BY date ORDER BY date
        """)
        stats["weekly_attendance"] = [
            (r["date"], r["present"], r["late"], r["absent"]) for r in att_rows
        ]

        # Recent activity
        recent = self.fetchall("""
            SELECT al.timestamp, al.action, al.table_name,
                   al.details, al.username
            FROM audit_log al
            ORDER BY al.timestamp DESC LIMIT 10
        """)
        stats["recent_activity"] = [dict(r) for r in recent]

        return stats
