import streamlit as st
import pandas as pd

from backend.db import get_connection
from backend.logs import log_action
from ui.common import show_sidebar_navigation, show_dashboard_analytics


def render_doctor_view(user):
    selected_page = show_sidebar_navigation(user)
    
    if selected_page == "dashboard":
        show_dashboard_analytics(user)
    
    elif selected_page == "patient_list":
        st.header("Patient Records")
        st.markdown(
            "You are viewing anonymized patient data only. "
            "Real names and contacts are masked for privacy protection."
        )

        try:
            conn = get_connection()
            cur = conn.cursor()
            
            cur.execute(
                """
                SELECT id, anonymized_name, anonymized_contact, diagnosis, created_at
                FROM patients;
                """
            )
            patients = cur.fetchall()
            conn.close()

            if patients:
                patients_data = [dict(p) for p in patients]
                df = pd.DataFrame(patients_data)
                st.dataframe(df, use_container_width=True)
                st.markdown(f"Viewing {len(patients)} patient records (anonymized)")
            else:
                st.markdown("No patients in the system yet.")
                
        except Exception as e:
            st.error(f"Error loading patient data: {e}")
            try:
                log_action(
                    user["username"],
                    user["role"],
                    "patient_list_error",
                    f"Failed to load anonymized patients: {str(e)[:100]}",
                )
            except:
                pass
            print(f"[DOCTOR VIEW ERROR] Failed to load patients: {e}")
    
    try:
        log_action(
            user["username"],
            user["role"],
            "view_doctor_dashboard",
            f"Doctor viewed {selected_page} page.",
        )
    except Exception as e:
        print(f"Could not log dashboard view: {e}")
