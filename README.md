# 🛡 Officers Affairs Management System

A complete, professional desktop application for managing police officers' administrative and operational records. Built with **Python + SQLite** and a **Tkinter** desktop interface.

---

## ✨ Features

### Modules
| Module | Features |
|--------|----------|
| **Dashboard** | Live stats, charts, weekly attendance, activity feed, dark/light mode |
| **Officers Management** | Full CRUD, search, filters, officer profile, promotion history, photo upload |
| **Attendance Management** | Daily tracking, check-in/out, bulk marking, monthly reports |
| **Leave & Vacations** | Request management, approve/reject workflow, leave types |
| **Daily Duties** | Shift assignments, locations, completion tracking, history |
| **Meals Log** | Meal tracking per officer, daily & monthly summaries |

### Technical Highlights
- 🗄 **SQLite** with WAL mode, foreign keys, and indexed queries
- 🔄 **Repository Pattern** — clean data access layer
- 🧩 **Services Layer** — business logic separated from UI
- 💉 **ServiceLocator** — simple dependency injection
- 🌙 **Dark / Light** theme toggle
- 🔒 **Audit logging** — every INSERT/UPDATE/DELETE recorded
- 📄 **Pagination-ready** architecture

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Python 3.9+ required
python --version

# Install tkinter (if not already present)
# Linux (Debian/Ubuntu):
sudo apt-get install python3-tk

# macOS:
brew install python-tk

# Windows: included with standard Python installer
```

### 2. Install Python dependencies

```bash
cd officers_affairs
pip install -r requirements.txt
```

### 3. (Optional) Seed sample data

```bash
python seed_data.py
```
This creates 50 sample officers with attendance, leave, duties, and meal records.

### 4. Launch the application

```bash
python main.py
```

---

## 📁 Project Structure

```
officers_affairs/
│
├── main.py                    # Entry point
├── seed_data.py               # Sample data seeder
├── requirements.txt
│
├── data/                      # SQLite database (auto-created)
│   └── officers_affairs.db
│
├── logs/                      # Daily log files (auto-created)
│
├── database/
│   ├── db_manager.py          # Connection and migrations
│   └── schema.sqlite          # Full DDL + seed reference data
│
├── models/
│   └── models.py              # Pure dataclasses (Officer, Attendance, etc.)
│
├── repositories/
│   └── repositories.py        # Data access layer (Repository Pattern)
│
├── services/
│   └── services.py            # Business logic
│
├── ui/
│   ├── theme.py               # Light/Dark theme colours & fonts
│   ├── main_window.py         # App shell: sidebar, header, routing
│   ├── components/
│   │   └── widgets.py         # Reusable widgets (Button, DataTable, etc.)
│   └── views/
│       ├── dashboard_view.py  # Dashboard with charts
│       ├── officers_view.py   # Officers CRUD + profile
│       └── module_views.py    # Attendance, Leave, Duties, Meals
│
└── utils/
    └── logger.py              # Logging configuration
```

---

## 🗄 Database Schema

```
officers          ← core officer records
ranks             ← rank reference table
departments       ← department reference
units             ← unit reference (linked to department)
promotion_history ← officer promotion log
attendance        ← daily attendance records
leave_types       ← leave type reference
leave_requests    ← officer leave requests
daily_duties      ← daily duty assignments
meals_log         ← officer meal records
audit_log         ← system audit trail
```

---

## 🎨 UI Overview

### Sidebar Navigation
- Dashboard → Officers → Attendance → Leave → Duties → Meals
- Dark/Light mode toggle
- Live clock in header

### Common Controls
- **Search bar** — real-time filtering
- **Sortable columns** — click any column header
- **Status filters** — dropdown filters per module
- **Add / Edit / Delete** toolbar buttons

---

## 🔒 Security & Reliability

- Input validation before every save
- SQLite foreign key constraints
- Unique constraints on officer number, national ID
- Cascade deletes (officer deleted → all related records cleaned)
- Global exception handler with logging
- Audit trail for all data changes

---

## ⚙️ Configuration

Edit `main.py` to change the database path:
```python
db_path = os.path.join(BASE_DIR, "data", "officers_affairs.db")
```

Edit `ui/theme.py` to customise colours, fonts, or add new themes.

---

## 📦 Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| tkinter | GUI framework | stdlib |
| sqlite3 | Database | stdlib |
| Pillow | Photo handling | ≥ 10.0 |

---

## 🛠 Build / Distribution

### Create standalone executable (Windows/Linux/macOS)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "OfficersAffairs" main.py
```

The executable will be in `dist/OfficersAffairs`.

### Create installer (Windows)
Use [Inno Setup](https://jrsoftware.org/isinfo.php) with the PyInstaller output.

---

## 📝 License

Internal use — Officers Affairs Department.
