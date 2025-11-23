import sqlite3
import os
import shutil
from datetime import datetime
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "data", "hospital.db"))
DB_BACKUP_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "data", "backups"))


def ensure_backup_directory():
    try:
        os.makedirs(DB_BACKUP_DIR, exist_ok=True)
    except OSError as e:
        print(f"[DB WARNING] Could not create backup directory: {e}")


def create_database_backup():
    try:
        ensure_backup_directory()
        
        if not os.path.exists(DB_PATH):
            print("[DB] No database file to backup.")
            return None
        
        existing_backups = []
        if os.path.exists(DB_BACKUP_DIR):
            for file in os.listdir(DB_BACKUP_DIR):
                if file.startswith("hospital_db_") and file.endswith(".db"):
                    file_path = os.path.join(DB_BACKUP_DIR, file)
                    if os.path.isfile(file_path):
                        existing_backups.append(file_path)
        
        existing_backups.sort(reverse=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(DB_BACKUP_DIR, f"hospital_db_{timestamp}.db")
        
        shutil.copy2(DB_PATH, backup_path)
        print(f"[DB] Database backed up to: {backup_path}")
        
        all_backups = []
        if os.path.exists(DB_BACKUP_DIR):
            for file in os.listdir(DB_BACKUP_DIR):
                if file.startswith("hospital_db_") and file.endswith(".db"):
                    file_path = os.path.join(DB_BACKUP_DIR, file)
                    if os.path.isfile(file_path):
                        all_backups.append(file_path)
        
        all_backups.sort()
        
        MAX_BACKUPS = 5
        
        if len(all_backups) > MAX_BACKUPS:
            backups_to_delete = all_backups[:-MAX_BACKUPS]
            for old_backup in backups_to_delete:
                try:
                    os.remove(old_backup)
                    print(f"[DB] Deleted old backup (limit exceeded): {os.path.basename(old_backup)}")
                except Exception as e:
                    print(f"[DB WARNING] Could not delete old backup {old_backup}: {e}")
        
        return backup_path
        
    except Exception as e:
        print(f"[DB ERROR] Backup failed: {e}")
        return None


def restore_from_backup(backup_path: str) -> bool:
    try:
        if not os.path.exists(backup_path):
            print(f"[DB ERROR] Backup file not found: {backup_path}")
            return False
        
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        shutil.copy2(backup_path, DB_PATH)
        print(f"[DB] Database restored from: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"[DB ERROR] Restore failed: {e}")
        return False


def check_database_availability() -> bool:
    try:
        if not os.path.exists(DB_PATH):
            print("[DB WARNING] Database file does not exist. Will create on first connection.")
            return False
        
        if not os.access(DB_PATH, os.R_OK):
            print("[DB ERROR] Database file exists but is not readable.")
            return False
        
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        required_tables = ["users", "patients", "logs"]
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cur.fetchall()]
        
        conn.close()
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        if missing_tables:
            print(f"[DB ERROR] Missing tables: {missing_tables}")
            return False
        
        print("[DB] Database availability check: OK")
        return True
        
    except sqlite3.DatabaseError as e:
        print(f"[DB ERROR] Database corruption detected: {e}")
        return False
    except Exception as e:
        print(f"[DB ERROR] Availability check failed: {e}")
        return False


def get_connection() -> sqlite3.Connection:
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=5)
        conn.row_factory = sqlite3.Row
        
        print(f"[DB] Connected to database: {DB_PATH}")
        return conn
        
    except sqlite3.OperationalError as e:
        print(f"[DB ERROR] Cannot open database file: {e}")
        print(f"[DB ERROR] Database path: {DB_PATH}")
        raise
    except sqlite3.Error as e:
        print(f"[DB ERROR] Connection failed: {e}")
        raise
    except OSError as e:
        print(f"[DB ERROR] Directory creation failed: {e}")
        raise


def init_db() -> None:
    try:
        ensure_backup_directory()
        
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','doctor','receptionist')),
                gdpr_consent INTEGER DEFAULT 0
            );
            """
        )
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN gdpr_consent INTEGER DEFAULT 0;")
        except sqlite3.OperationalError:
            pass

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                contact TEXT,
                diagnosis TEXT,
                anonymized_name TEXT,
                anonymized_contact TEXT,
                encrypted_name TEXT,
                encrypted_contact TEXT,
                created_at TEXT
            );
            """
        )
        
        try:
            cur.execute("ALTER TABLE patients ADD COLUMN encrypted_name TEXT;")
        except sqlite3.OperationalError:
            pass
        
        try:
            cur.execute("ALTER TABLE patients ADD COLUMN encrypted_contact TEXT;")
        except sqlite3.OperationalError:
            pass

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                role TEXT,
                action TEXT,
                details TEXT,
                created_at TEXT
            );
            """
        )

        conn.commit()
        conn.close()
        
        if check_database_availability():
            print("[DB] Database initialization completed successfully.")
        else:
            print("[DB WARNING] Database created but availability check failed.")
        
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to initialize database: {e}")
        raise
    except Exception as e:
        print(f"[DB ERROR] Unexpected error during initialization: {e}")
        raise
