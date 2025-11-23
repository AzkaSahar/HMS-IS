from datetime import datetime, timedelta
from .db import get_connection


def log_action(username: str, role: str, action: str, details: str = ""):
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cur.execute(
            """
            INSERT INTO logs (username, role, action, details, created_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (username, role, action, details, current_time),
        )
        
        conn.commit()
        conn.close()
        print(f"[LOG] Action logged: {username} ({role}) - {action}")
        
    except Exception as e:
        print(f"[LOG ERROR] Failed to log action: {e}")


def get_logs(limit: int = 100):
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute(
            """
            SELECT * FROM logs
            ORDER BY created_at DESC
            LIMIT ?;
            """,
            (limit,),
        )
        
        rows = cur.fetchall()
        conn.close()
        
        print(f"[LOG] Retrieved {len(rows)} log entries.")
        return rows
        
    except Exception as e:
        print(f"[LOG ERROR] Failed to retrieve logs: {e}")
        return []


def export_logs_to_csv(filename: str = "audit_logs.csv") -> bool:
    try:
        import csv
        
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM logs ORDER BY created_at DESC;")
        rows = cur.fetchall()
        conn.close()
        
        if not rows:
            print("[LOG] No logs to export.")
            return False
        
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Username", "Role", "Action", "Details", "Timestamp"])
            for row in rows:
                writer.writerow([row["id"], row["username"], row["role"], 
                               row["action"], row["details"], row["created_at"]])
        
        print(f"[LOG] Logs exported to {filename}")
        return True
        
    except Exception as e:
        print(f"[LOG ERROR] Failed to export logs: {e}")
        return False


def cleanup_old_data(retention_days: int = 90):
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=retention_days)).strftime("%Y-%m-%d %H:%M:%S")
        
        cur.execute(
            """
            DELETE FROM logs
            WHERE created_at < ?;
            """,
            (cutoff_date,)
        )
        
        deleted_logs = cur.rowcount
        
        cur.execute(
            """
            DELETE FROM patients
            WHERE created_at < ?;
            """,
            (cutoff_date,)
        )
        
        deleted_patients = cur.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"[RETENTION] Cleaned up {deleted_logs} old log entries and {deleted_patients} old patient records (older than {retention_days} days)")
        return {"logs_deleted": deleted_logs, "patients_deleted": deleted_patients}
        
    except Exception as e:
        print(f"[RETENTION ERROR] Failed to cleanup old data: {e}")
        return None
