import streamlit as st
from backend.db import init_db, check_database_availability, create_database_backup
from backend.auth import create_default_users, authenticate
from backend.logs import log_action
from frontend.layout import show_header, show_footer, show_gdpr_notice
from frontend.admin_view import render_admin_view
from frontend.doctor_view import render_doctor_view
from frontend.receptionist_view import render_receptionist_view


# -------------------------
# 🎨 CUSTOM GLOBAL CSS THEME
# -------------------------
st.markdown("""
<style>

/* ---------------- GLOBAL STYLING ---------------- */

body {
    background-color: #404362 !important; /* light gray hospital-like */
}

/* MAIN APP BACKGROUND */
.reportview-container {
    background-color: #404362 !important;
}

/* HEADERS (Blue shades) */
h1, h2, h3, h4 {
    color: #1e3a8a !important;   /* navy-blue */
    font-weight: 700 !important;
}

/* SUBHEADERS */
h3 {
    color: #1d4ed8 !important;  /* royal blue */
}


/* ----------------- INPUT FIELDS ----------------- */
.stTextInput>div>div>input {
    border-radius: 10px;
    border: 1px solid #cbd5e1;
    padding: 10px;
}

/* ----------------- BUTTONS (Hospital Blue) ----------------- */

.stButton>button {
    background-color: #2563eb !important; /* blue */
    color: white !important;
    padding: 10px 0;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 16px;
    border: none;
}

.stButton>button:hover {
    background-color: #1d4ed8 !important;
}

/* ---------------- LINKS ---------------- */
a { color: #2563eb !important; }
a:hover { text-decoration: underline; }

/* ---------------- HIGHLIGHT SELECTION ---------------- */
::selection {
    background: #dc2626 !important; /* soft red highlight */
    color: white !important;
}

/* ---------------- SCROLLBAR ---------------- */
::-webkit-scrollbar-thumb:hover {
    background: #2563eb !important; 
}

/* ---------------- SIDEBAR ---------------- */
.css-1d391kg {  
    background-color: #e2e8f0 !important; 
}
/* RADIO BUTTONS */
[data-baseweb="radio"] > div > label > div:first-child {
    border-color: #2563eb !important;  /* blue border */
}
[data-baseweb="radio"] > div > label:hover > div:first-child {
    border-color: #1d4ed8 !important;
}

/* NUMBER INPUT (+/-) BUTTONS */
.stNumberInput>div>div>button {
    background-color: #2563eb !important;
    color: white !important;
    border-radius: 6px;
    border: none;
}
.stNumberInput>div>div>button:hover {
    background-color: #1d4ed8 !important;
}

/* INPUT FOCUS BORDER (text, password) */
.stTextInput>div>div>input:focus {
    border: 2px solid #2563eb !important;
    outline: none !important;
}

/* RADIO SELECTED DOT */
[data-baseweb="radio"] input:checked + div {
    border-color: #2563eb !important;
}

/* SCROLLBAR */
::-webkit-scrollbar-thumb:hover {
    background: #1d4ed8 !important;
}
</style>
""", unsafe_allow_html=True)



# -------------------------
# STREAMLIT PAGE SETTINGS
# -------------------------
st.set_page_config(
    page_title="Hospital Management System",
    page_icon="🏥",
    layout="centered",
)


# -------------------------
# INITIALIZATION
# -------------------------
def initialize_app():
    try:
        db_available = check_database_availability()
        init_db()
        create_default_users()
        backup_path = create_database_backup()

        if db_available and backup_path:
            print("[APP] Application initialized with backup protection.")
        elif db_available:
            print("[APP] Application initialized (backup not created).")
        else:
            print("[APP] Application initialized with new database created.")

    except Exception as e:
        st.error(f"Failed to initialize application: {e}")
        print(f"[APP ERROR] Initialization failed: {e}")


if "user" not in st.session_state:
    st.session_state["user"] = None


# -------------------------
# LOGIN PAGE (NEW LAYOUT)
# -------------------------
def render_login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:

        st.markdown("<h1 style='text-align:center;'>🏥 Hospital System</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center; margin-bottom:30px;'>Login</h3>", unsafe_allow_html=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        login_btn = st.button("Login", use_container_width=True)

        if login_btn:
            username_clean = username.strip()
            password_clean = password.strip()

            if not username_clean or not password_clean:
                st.error("Please enter both username and password.")
            else:
                try:
                    user = authenticate(username_clean, password_clean)

                    if user:
                        st.session_state["user"] = user
                        st.success(f"Welcome, {user['username']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

                except Exception as e:
                    st.error(f"Login error: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

        show_footer()


# -------------------------
# DASHBOARD
# -------------------------
def render_dashboard():
    user = st.session_state["user"]

    consent_given = show_gdpr_notice()
    if not consent_given:
        st.stop()

    show_header(user)

    try:
        if user["role"] == "admin":
            render_admin_view(user)
        elif user["role"] == "doctor":
            render_doctor_view(user)
        elif user["role"] == "receptionist":
            render_receptionist_view(user)
        else:
            st.error(f"Unknown role: {user['role']}")

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

    show_footer()


def main():
    initialize_app()

    if st.session_state["user"] is None:
        render_login_page()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
