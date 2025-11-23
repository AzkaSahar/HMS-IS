import streamlit as st
import pandas as pd
from datetime import datetime

from backend.db import get_connection
from backend.logs import log_action
from backend.data_protection import anonymize_name, anonymize_contact, encrypt_data
from frontend.layout import show_sidebar_navigation, show_dashboard_analytics


def render_receptionist_view(user):
    selected_page = show_sidebar_navigation(user)
    
    if selected_page == "dashboard":
        show_dashboard_analytics(user)
    
    elif selected_page == "patient_list":
        st.header("Patient Management")
        st.markdown(
            "As a receptionist, you can add new patients and see all records. "
            "Patient records are automatically anonymized for privacy protection."
        )

        # ------------------------------
        # Display all patients first
        # ------------------------------
        st.subheader("All Patients")
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, name, contact, diagnosis, created_at
                FROM patients;
                """
            )
            patients = cur.fetchall()
            conn.close()

            if patients:
                patients_data = [dict(p) for p in patients]
                df = pd.DataFrame(patients_data)
                
                df['contact_masked'] = df['contact'].apply(anonymize_contact)
                df = df[['id', 'name', 'contact_masked', 'diagnosis', 'created_at']]
                df.rename(columns={'contact_masked': 'contact'}, inplace=True)
                
                st.dataframe(df, use_container_width=True)
                st.markdown(f"Total patients: {len(patients)}")
            else:
                st.markdown("No patients in the system yet.")
                
        except Exception as e:
            st.error(f"Error loading patient list: {e}")
            try:
                log_action(
                    user["username"],
                    user["role"],
                    "patient_list_error",
                    f"Failed to load patient list: {str(e)[:100]}",
                )
            except:
                pass

        # ------------------------------
        # Collapsible form below the table
        # ------------------------------
        with st.expander("➕ Add New Patient"):
            with st.form("add_patient_form"):
                name = st.text_input(
                    "Full Name",
                    help="Patient's legal name"
                )
                
                contact = st.text_input(
                    "Contact Number",
                    help="Phone number or email address for follow-up"
                )
                
                diagnosis = st.text_input(
                    "Diagnosis / Reason for visit",
                    help="Brief description of chief complaint or reason for visit"
                )
                
                submitted = st.form_submit_button("Save Patient")

            if submitted:
                if not name or not contact:
                    st.error("Name and contact are required.")
                else:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cur.execute(
                            """
                            INSERT INTO patients (name, contact, diagnosis, created_at)
                            VALUES (?, ?, ?, ?);
                            """,
                            (name, contact, diagnosis, current_time),
                        )
                        
                        patient_id = cur.lastrowid

                        anon_name = anonymize_name(name, patient_id)
                        anon_contact = anonymize_contact(contact)
                        enc_name = encrypt_data(name)
                        enc_contact = encrypt_data(contact)

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

                        st.success(f"Patient saved with ID {patient_id}.")

                        log_action(
                            user["username"],
                            user["role"],
                            "add_patient",
                            f"Receptionist added patient {patient_id}: {name}",
                        )
                        
                        st.experimental_rerun()  # Refresh to show the new patient immediately
                        
                    except Exception as e:
                        st.error(f"Error saving patient: {e}")
                        try:
                            log_action(
                                user["username"],
                                user["role"],
                                "add_patient_error",
                                f"Failed to add patient: {str(e)[:100]}",
                            )
                        except:
                            pass
                        print(f"[RECEPTIONIST VIEW ERROR] Failed to add patient: {e}")

    try:
        log_action(
            user["username"],
            user["role"],
            "view_receptionist_dashboard",
            f"Receptionist viewed {selected_page} page.",
        )
    except Exception as e:
        print(f"Could not log dashboard view: {e}")
