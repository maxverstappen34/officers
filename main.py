"""
Officers Affairs Management System
Entry point — initialises services and launches the GUI.

Requirements:
    pip install pillow

Run:
    python main.py
""" 

import sys
import os
import traceback
import logging

# ── path setup ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── logging ─────────────────────────────────────────────────────────────
from utils.logger import setup_logging
log = setup_logging(log_dir=os.path.join(BASE_DIR, "logs"))
log.info("=" * 60)
log.info("Officers Affairs Management System — Starting")
log.info("=" * 60)

# ── tkinter availability check ──────────────────────────────────────────
try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("ERROR: tkinter is not available.")
    print("Install it via your package manager, e.g.:")
    print("  sudo apt-get install python3-tk   (Debian/Ubuntu)")
    print("  brew install python-tk            (macOS)")
    sys.exit(1)

# ── services ────────────────────────────────────────────────────────────
from services.services import ServiceLocator

# ── main ────────────────────────────────────────────────────────────────
def main():
    db_path = os.path.join(BASE_DIR, "data", "officers_affairs.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    log.info(f"Database path: {db_path}")

    try:
        services = ServiceLocator(db_path)
        log.info("Services initialised OK")
    except Exception as e:
        log.critical(f"Failed to initialise services: {e}", exc_info=True)
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Startup Error",
                             f"Failed to connect to database:\n{e}")
        sys.exit(1)

    try:
        from ui.main_window import MainApp
        app = MainApp(services)

        # Global exception handler for Tk events
        def _tk_error(exc, val, tb):
            log.error("Unhandled Tk error", exc_info=(exc, val, tb))
            messagebox.showerror("Unexpected Error",
                                  f"{exc.__name__}: {val}\n\nSee logs for details.")
        app.report_callback_exception = _tk_error

        log.info("Main window launched")
        app.mainloop()

    except Exception as e:
        log.critical(f"Fatal error: {e}", exc_info=True)
        try:
            root = tk.Tk(); root.withdraw()
            messagebox.showerror("Fatal Error", traceback.format_exc())
        except Exception:
            print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
