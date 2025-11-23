import os
from cryptography.fernet import Fernet
from .db import get_connection


ENCRYPTION_KEY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", ".key")


def get_or_create_encryption_key() -> bytes:
    try:
        os.makedirs(os.path.dirname(ENCRYPTION_KEY_FILE), exist_ok=True)
        
        if os.path.exists(ENCRYPTION_KEY_FILE):
            with open(ENCRYPTION_KEY_FILE, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(ENCRYPTION_KEY_FILE, "wb") as f:
                f.write(key)
            print("[PRIVACY] Encryption key generated and stored.")
            return key
    except Exception as e:
        print(f"[PRIVACY ERROR] Failed to manage encryption key: {e}")
        raise


def encrypt_data(plaintext: str) -> str:
    try:
        if not plaintext:
            return None
        
        key = get_or_create_encryption_key()
        cipher_suite = Fernet(key)
        encrypted = cipher_suite.encrypt(plaintext.encode("utf-8"))
        return encrypted.decode("utf-8")
    except Exception as e:
        print(f"[PRIVACY ERROR] Encryption failed: {e}")
        return None


def decrypt_data(encrypted_text: str) -> str:
    try:
        if not encrypted_text:
            return None
        
        key = get_or_create_encryption_key()
        cipher_suite = Fernet(key)
        decrypted = cipher_suite.decrypt(encrypted_text.encode("utf-8"))
        return decrypted.decode("utf-8")
    except Exception as e:
        print(f"[PRIVACY ERROR] Decryption failed: {e}")
        return None


def anonymize_name(real_name: str, patient_id: int) -> str:
    try:
        if not real_name:
            return None
        return f"PAT_{patient_id:04d}"
    except Exception as e:
        print(f"[PRIVACY ERROR] Name anonymization failed: {e}")
        return None


def anonymize_contact(contact: str) -> str:
    try:
        if not contact or len(contact) < 4:
            return None
        return "XXX-XXX-" + contact[-4:]
    except Exception as e:
        print(f"[PRIVACY ERROR] Contact anonymization failed: {e}")
        return None


def anonymize_all_patients():
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, name, contact FROM patients;")
        rows = cur.fetchall()

        processed_count = 0
        for row in rows:
            anon_name = anonymize_name(row["name"], row["id"])
            anon_contact = anonymize_contact(row["contact"])
            enc_name = encrypt_data(row["name"])
            enc_contact = encrypt_data(row["contact"])
            
            cur.execute(
                """
                UPDATE patients
                SET anonymized_name = ?, anonymized_contact = ?, encrypted_name = ?, encrypted_contact = ?
                WHERE id = ?;
                """,
                (anon_name, anon_contact, enc_name, enc_contact, row["id"]),
            )
            processed_count += 1

        conn.commit()
        conn.close()
        print(f"[PRIVACY] Anonymization and encryption completed: {processed_count} patients processed.")
        
    except Exception as e:
        print(f"[PRIVACY ERROR] Batch anonymization failed: {e}")
        raise


def anonymize_single_patient(patient_id: int):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, name, contact FROM patients WHERE id = ?;", (patient_id,))
        row = cur.fetchone()

        if not row:
            print(f"[PRIVACY] Patient {patient_id} not found.")
            return False

        anon_name = anonymize_name(row["name"], row["id"])
        anon_contact = anonymize_contact(row["contact"])
        enc_name = encrypt_data(row["name"])
        enc_contact = encrypt_data(row["contact"])

        cur.execute(
            """
            UPDATE patients
            SET anonymized_name = ?, anonymized_contact = ?, encrypted_name = ?, encrypted_contact = ?
            WHERE id = ?;
            """,
            (anon_name, anon_contact, enc_name, enc_contact, patient_id),
        )

        conn.commit()
        conn.close()
        print(f"[PRIVACY] Patient {patient_id} anonymized and encrypted successfully.")
        return True

    except Exception as e:
        print(f"[PRIVACY ERROR] Single patient anonymization failed: {e}")
        return False
