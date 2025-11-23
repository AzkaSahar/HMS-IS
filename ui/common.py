import streamlit as st
from datetime import datetime
import pandas as pd
from backend.db import get_connection


def show_header(user):
    pass

def show_gdpr_notice():
    if "user" not in st.session_state or st.session_state["user"] is None:
        return False
    
    if "gdpr_consent_given" not in st.session_state:
        st.session_state["gdpr_consent_given"] = False
    
    if st.session_state["gdpr_consent_given"]:
        return True
    
    st.markdown(
        """
        <div style='background-color: #e8f5e9; padding: 20px; border-radius: 8px; border-left: 5px solid #6eb52f; margin: 20px 0;'>
            <h3 style='color: #2e7d32; margin-top: 0;'>🔒 GDPR Privacy Notice & Consent</h3>
            <p style='color: #1b5e20; margin-bottom: 15px; font-size: 16px;'>
                This Hospital Management System processes personal data in compliance with GDPR regulations. 
                By using this system, you consent to:
            </p>
            <ul style='color: #1b5e20; margin-bottom: 15px; font-size: 15px;'>
                <li>Data processing for hospital management and patient care purposes</li>
                <li>Role-based access control for data protection</li>
                <li>Audit logging of all system activities</li>
                <li>Data anonymization and encryption for privacy protection</li>
            </ul>
            <p style='color: #1b5e20; margin-bottom: 15px; font-size: 15px;'>
                <strong>Your Rights:</strong> You have the right to access, rectify, and erase your data. 
                Contact the administrator for data subject requests.
            </p>
            <p style='color: #1b5e20; margin-bottom: 0; font-size: 14px; font-style: italic;'>
                This consent is required each time you access the system.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("I Consent - Continue to Dashboard", use_container_width=True, key="gdpr_consent_btn", type="primary"):
            st.session_state["gdpr_consent_given"] = True
            st.rerun()
    
    return False


def show_footer():
    st.write("---")
    
    st.caption(
        "Last loaded: "
        + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


def show_sidebar_navigation(user):
    with st.sidebar:
        st.title("Hospital Management System")
        st.divider()
        
        st.write(f"**{user['username']}**")
        st.write(f"Role: {user['role']}")
        st.divider()
        
        if user["role"] == "admin":
            page = st.radio(
                "View",
                ["Dashboard", "Patient List", "Audit Logs"],
                key="page_selector",
                label_visibility="collapsed"
            )
        else:
            page = st.radio(
                "View",
                ["Dashboard", "Patient List"],
                key="page_selector",
                label_visibility="collapsed"
            )
        
        st.divider()
        
        if st.button("Logout", use_container_width=True, key="sidebar_logout"):
            st.session_state["user"] = None
            st.session_state["logged_in"] = False
            st.rerun()
        
        if "Dashboard" in page:
            return "dashboard"
        elif "Patient List" in page:
            return "patient_list"
        elif "Audit Logs" in page:
            return "logs"
        
        return "dashboard"


def show_dashboard_analytics(user):
    st.markdown("## Dashboard Analytics")
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM patients;")
        total_patients = cur.fetchone()[0]
        
        cur.execute(
            """
            SELECT diagnosis, COUNT(*) as count 
            FROM patients 
            GROUP BY diagnosis;
            """
        )
        diagnosis_data = cur.fetchall()
        
        if user["role"] == "doctor":
            cur.execute(
                """
                SELECT id, anonymized_name, diagnosis, created_at 
                FROM patients 
                ORDER BY created_at DESC 
                LIMIT 5;
                """
            )
            column_names = ["ID", "Anonymized Name", "Diagnosis", "Created At"]
        else:
            cur.execute(
                """
                SELECT id, name, diagnosis, created_at 
                FROM patients 
                ORDER BY created_at DESC 
                LIMIT 5;
                """
            )
            column_names = ["ID", "Name", "Diagnosis", "Created At"]
        
        recent_patients = cur.fetchall()
        
        if user["role"] == "admin":
            cur.execute(
                """
                SELECT date(created_at) as date, COUNT(*) as count
                FROM logs
                WHERE created_at >= datetime('now', '-30 days')
                GROUP BY date(created_at)
                ORDER BY date DESC;
                """
            )
            activity_data = cur.fetchall()
        else:
            activity_data = []
        
        conn.close()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Patients", total_patients)
        
        with col2:
            st.metric("System Status", "Operational")
        
        with col3:
            st.metric("Last Updated", datetime.now().strftime("%H:%M:%S"))
        
        st.divider()
        
        if user["role"] == "admin" and activity_data:
            st.markdown("### Real-Time Activity Graph (Last 30 Days)")
            df_activity = pd.DataFrame(activity_data, columns=["Date", "Actions"])
            df_activity["Date"] = pd.to_datetime(df_activity["Date"])
            df_activity = df_activity.set_index("Date").sort_index()
            st.line_chart(df_activity, color="#6eb52f", use_container_width=True)
            st.caption(f"Total actions in last 30 days: {df_activity['Actions'].sum()}")
            st.divider()
        
        if diagnosis_data:
            st.markdown("### Patients by Diagnosis")
            df_diagnosis = pd.DataFrame(diagnosis_data, columns=["Diagnosis", "Count"])
            st.bar_chart(
                df_diagnosis.set_index("Diagnosis"),
                color=["#6eb52f"]
            )
        
        if recent_patients:
            st.markdown("### Recent Patients")
            patients_data = [dict(p) for p in recent_patients]
            df_recent = pd.DataFrame(patients_data)
            st.dataframe(df_recent, use_container_width=True)
        
    except Exception as e:
        st.markdown(f"Error loading dashboard data: {e}")
        print(f"[DASHBOARD ERROR] {e}")
