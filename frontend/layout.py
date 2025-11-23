import streamlit as st
from datetime import datetime
import pandas as pd
from backend.db import get_connection

# --------------------------
# 🎨 GLOBAL STYLING
# --------------------------
st.markdown("""
<style>
/* Background */
body, .reportview-container, .css-18e3th9 {
    background-color: #A2A9F6 !important;
}

/* Sidebar */
.css-1d391kg {
    background-color: #dbe3fc !important;
    color: #1e3a8a !important;
}

/* Sidebar Radio & Buttons */
.stRadio>div { background-color: #dbe3fc !important; }
.stRadio>div>label:hover { color: #1d4ed8 !important; }
.stButton>button { background-color: #2563eb !important; color: white !important; border-radius: 8px; font-weight: 600; font-size: 16px; border: none; padding: 8px 0; }
.stButton>button:hover { background-color: #1d4ed8 !important; }

/* Titles */
h1, h2, h3, h4 { color: #1e3a8a !important; font-weight: 700 !important; }

/* GDPR Notice */
.gdpr-notice {
    background-color: #dbe3fc !important;
    border-left: 5px solid #dc2626 !important;
    border-radius: 10px !important;
    padding: 20px !important;
    margin: 20px 0 !important;
    color: #1e3a8a !important;
}

/* Input Fields */
.stTextInput>div>div>input {
    border-radius: 10px;
    border: 1px solid #1e40af;
    padding: 10px;
}

/* Links */
a { color: #2563eb !important; }
a:hover { text-decoration: underline; }

/* Selection */
::selection { background: #dc2626 !important; color: white !important; }

/* Divider */
hr { border-top: 1px solid #1d4ed8 !important; }
</style>
""", unsafe_allow_html=True)

# --------------------------
# HEADER
# --------------------------
def show_header(user):
    st.markdown(
        f"<h2 style='text-align:center; color:#1e3a8a; margin-bottom:10px;'>Welcome, {user['username'].title()}</h2>", 
        unsafe_allow_html=True
    )
    st.divider()

# --------------------------
# GDPR NOTICE
# --------------------------
def show_gdpr_notice():
    if "user" not in st.session_state or st.session_state["user"] is None:
        return False
    if "gdpr_consent_given" not in st.session_state:
        st.session_state["gdpr_consent_given"] = False
    if st.session_state["gdpr_consent_given"]:
        return True

    st.markdown("""
    <div class='gdpr-notice'>
        <h3 style='margin-top:0;'>🔒 GDPR Privacy Notice & Consent</h3>
        <p>This Hospital Management System processes personal data in compliance with GDPR.</p>
        <ul>
            <li>Data processing for hospital management</li>
            <li>Role-based access control</li>
            <li>Audit logging of all activities</li>
            <li>Data anonymization and encryption</li>
        </ul>
        <p><strong>Your Rights:</strong> You can access, rectify, or erase your data. Contact admin for requests.</p>
        <p style='font-style:italic;'>Consent required each time you access the system.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("I Consent - Continue to Dashboard", use_container_width=True):
            st.session_state["gdpr_consent_given"] = True
            st.rerun()
    return False

# --------------------------
# FOOTER
# --------------------------
def show_footer():
    st.divider()
    st.caption("Last loaded: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def show_sidebar_navigation(user):
    with st.sidebar:
        st.markdown(f"### 🏥 Hospital System")
        st.markdown(f"**User:** {user['username']}")
        st.markdown(f"**Role:** {user['role']}")

        # Use button-style navigation cards instead of radio buttons
        pages = ["Dashboard", "Patient List"]
        if user["role"] == "admin":
            pages.append("Audit Logs")

        selected_page = None
        for page in pages:
            if st.button(page, key=f"nav_{page.replace(' ','_')}", use_container_width=True):
                st.session_state["selected_page"] = page
                st.rerun()

        # Highlight currently selected page
        if "selected_page" not in st.session_state:
            st.session_state["selected_page"] = pages[0]

        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state["user"] = None
            st.session_state.pop("selected_page", None)
            st.rerun()

        # Return internal page identifier
        mapping = {"Dashboard": "dashboard", "Patient List": "patient_list", "Audit Logs": "logs"}
        return mapping.get(st.session_state["selected_page"], "dashboard")

# --------------------------
# DASHBOARD ANALYTICS
# --------------------------
def show_dashboard_analytics(user):
    st.markdown("## Dashboard Analytics")
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM patients;")
        total_patients = cur.fetchone()[0]

        cur.execute("SELECT diagnosis, COUNT(*) FROM patients GROUP BY diagnosis;")
        diagnosis_data = cur.fetchall()
        conn.close()

        col1, col2 = st.columns(2)
        with col1: st.metric("Total Patients", total_patients)
        with col2: st.metric("System Status", "Operational")
        st.divider()

        if diagnosis_data:
            st.markdown("### Patients by Diagnosis")
            df_diag = pd.DataFrame(diagnosis_data, columns=["Diagnosis", "Count"])
            st.bar_chart(df_diag.set_index("Diagnosis"), color="#dc2626")

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        print(f"[DASHBOARD ERROR] {e}")
