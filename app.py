import streamlit as st
from backend.db import init_db, check_database_availability, create_database_backup
from backend.auth import create_default_users, authenticate
from backend.logs import log_action
from ui.common import show_header, show_footer, show_gdpr_notice
from ui.admin_view import render_admin_view
from ui.doctor_view import render_doctor_view
from ui.receptionist_view import render_receptionist_view


st.markdown(
    """
    <style>
        ::selection {
            background-color: #6eb52f;
            color: white;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #6eb52f;
        }
        
        a {
            color: #6eb52f;
        }
        
        a:hover {
            color: #5a9024;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.set_page_config(
    page_title="Hospital Management System",
    page_icon="H",
    layout="wide",
    initial_sidebar_state="expanded",
)


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
        st.warning(
            "Database initialization failed. "
            "Please check permissions and ensure the data directory is writable."
        )


if "user" not in st.session_state:
    st.session_state["user"] = None


def render_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("Hospital Management System")
        st.subheader("Login")

        username = st.text_input(
            "Username",
            help="Enter your username (e.g., 'admin', 'doctor', 'reception')"
        )

        password = st.text_input(
            "Password",
            type="password",
            help="Enter your password"
        )

        if st.button("Login", use_container_width=True):
            username_clean = username.strip()
            password_clean = password.strip()
            
            if not username_clean or not password_clean:
                st.error("Please enter both username and password.")
            else:
                try:
                    user = authenticate(username_clean, password_clean)
                    
                    if user:
                        st.session_state["user"] = user
                        st.session_state["gdpr_consent_given"] = False
                        
                        log_action(
                            user["username"],
                            user["role"],
                            "login",
                            "User successfully authenticated",
                        )
                        
                        st.success(f"Welcome, {user['username']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                        
                        try:
                            log_action(
                                username_clean,
                                "unknown",
                                "failed_login",
                                "Failed authentication attempt",
                            )
                        except:
                            pass
                            
                except Exception as e:
                    st.error(f"Login error: {e}")
                    print(f"[LOGIN ERROR] Authentication failed: {e}")

        show_footer()


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
        print(f"[DASHBOARD ERROR] Failed to render dashboard: {e}")

    show_footer()


def main():
    initialize_app()

    if st.session_state["user"] is None:
        render_login_page()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
