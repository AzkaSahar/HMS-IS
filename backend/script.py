import sqlite3
from datetime import datetime
from backend.db import get_connection

# Define 10 new patients with unique diseases
new_patients = [
    {"name": "Aisha Khan", "contact": "0300-111-0001", "diagnosis": "Migraine"},
    {"name": "Bilal Riaz", "contact": "0300-111-0002", "diagnosis": "Diabetes"},
    {"name": "Hina Shah", "contact": "0300-111-0003", "diagnosis": "Asthma"},
    {"name": "Omar Siddiqui", "contact": "0300-111-0004", "diagnosis": "Allergic Rhinitis"},
    {"name": "Sania Malik", "contact": "0300-111-0005", "diagnosis": "Diabetes"},
    {"name": "Fahad Iqbal", "contact": "0300-111-0006", "diagnosis": "Arthritis"},
    {"name": "Kiran Ali", "contact": "0300-111-0007", "diagnosis": "Diabetes"},
    {"name": "Usman Tariq", "contact": "0300-111-0008", "diagnosis": "Migraine"},
    {"name": "Zoya Hassan", "contact": "0300-111-0009", "diagnosis": "Hyperthyroidism"},
    {"name": "Danish Nawaz", "contact": "0300-111-0010", "diagnosis": "Anemia"},
]

# Connect to database
conn = get_connection()
cur = conn.cursor()

# Delete all existing patients
cur.execute("DELETE FROM patients;")
conn.commit()
print("[INFO] All existing patients deleted.")

# Insert new patients
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
for patient in new_patients:
    cur.execute(
        """
        INSERT INTO patients (name, contact, diagnosis, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (patient["name"], patient["contact"], patient["diagnosis"], current_time)
    )

conn.commit()
conn.close()
print("[INFO] 10 new patients added successfully.")
