import hashlib
from .db import get_connection

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

USE_BCRYPT = True


def hash_password(password: str) -> str:
    if USE_BCRYPT and BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        if not password_hash:
            return False
        
        if USE_BCRYPT and BCRYPT_AVAILABLE:
            if password_hash.startswith("$2") or password_hash.startswith("$2a$") or password_hash.startswith("$2b$"):
                return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
            else:
                provided_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
                return provided_hash == password_hash
        else:
            provided_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            return provided_hash == password_hash
    except Exception as e:
        print(f"[AUTH ERROR] Password verification failed: {e}")
        return False


def create_default_users():
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) AS c FROM users;")
        count = cur.fetchone()["c"]

        if count == 0:
            users = [
                ("admin", hash_password("admin123"), "admin"),
                ("doctor", hash_password("doctor123"), "doctor"),
                ("reception", hash_password("reception123"), "receptionist"),
            ]
            
            cur.executemany(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?);",
                users,
            )
            conn.commit()
            print("[AUTH] Default users created successfully.")
        else:
            print("[AUTH] Users already exist; skipping default user creation.")

        conn.close()
        
    except Exception as e:
        print(f"[AUTH ERROR] Failed to create default users: {e}")
        raise


def authenticate(username: str, password: str) -> dict:
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM users WHERE username = ?;", (username,))
        row = cur.fetchone()

        if not row:
            conn.close()
            print(f"[AUTH] Login attempt: username '{username}' not found")
            return None

        password_hash = row["password_hash"]
        
        if not verify_password(password, password_hash):
            conn.close()
            print(f"[AUTH] Login attempt: incorrect password for '{username}'")
            return None

        if USE_BCRYPT and BCRYPT_AVAILABLE:
            if not (password_hash.startswith("$2") or password_hash.startswith("$2a$") or password_hash.startswith("$2b$")):
                new_hash = hash_password(password)
                cur.execute(
                    "UPDATE users SET password_hash = ? WHERE username = ?;",
                    (new_hash, username)
                )
                conn.commit()
                print(f"[AUTH] Upgraded password hash to bcrypt for user '{username}'")

        conn.close()
        print(f"[AUTH] Login successful: {username} ({row['role']})")
        return {"username": row["username"], "role": row["role"]}
        
    except Exception as e:
        print(f"[AUTH ERROR] Authentication failed: {e}")
        return None
