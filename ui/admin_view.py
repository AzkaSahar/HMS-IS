import streamlit as st
import pandas as pd

from backend.db import get_connection
from backend.logs import get_logs, log_action, export_logs_to_csv, cleanup_old_data
from backend.privacy import anonymize_all_patients, decrypt_data
from backend.db import check_database_availability, create_database_backup, restore_from_backup
import os
from ui.common import show_sidebar_navigation, show_dashboard_analytics


def render_admin_view(user):
    selected_page = show_sidebar_navigation(user)
    
    if selected_page == "dashboard":
        try:
            show_dashboard_analytics(user)
        except Exception as e:
            st.error(f"Error loading dashboard analytics: {e}")
            try:
                log_action(
                    user["username"],
                    user["role"],
                    "dashboard_error",
                    f"Failed to load dashboard: {str(e)[:100]}",
                )
            except:
                pass
        
        st.divider()
        st.markdown("### Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Run Anonymization for All Patients", use_container_width=True):
                try:
                    backup = create_database_backup()
                    if backup:
                        st.info(f"Backup created: {os.path.basename(backup)}")
                    
                    anonymize_all_patients()
                    log_action(
                        user["username"],
                        user["role"],
                        "anonymize_all_patients",
                        "Admin triggered anonymization for all patients",
                    )
                    
                    st.success("Anonymization Completed Successfully!")
                    
                except Exception as e:
                    st.error(f"Anonymization failed: {e}")
                    log_action(
                        user["username"],
                        user["role"],
                        "anonymize_all_patients_failed",
                        f"Anonymization error: {str(e)[:100]}",
                    )
        
        with col2:
            if st.button("Check Database Status", use_container_width=True):
                if check_database_availability():
                    st.success("Database is available and healthy")
                    log_action(
                        user["username"],
                        user["role"],
                        "check_database_status",
                        "Database availability check: OK",
                    )
                else:
                    st.error("Database is not available or corrupted")
                    log_action(
                        user["username"],
                        user["role"],
                        "check_database_status_failed",
                        "Database availability check: FAILED",
                    )
        
        st.divider()
        st.markdown("### System Management")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            if st.button("Create Database Backup", use_container_width=True):
                try:
                    backup_path = create_database_backup()
                    if backup_path:
                        st.success(f"Backup created: {os.path.basename(backup_path)}")
                        log_action(
                            user["username"],
                            user["role"],
                            "create_backup",
                            f"Backup created: {backup_path}",
                        )
                    else:
                        st.warning("Backup creation failed")
                except Exception as e:
                    st.error(f"Backup failed: {e}")
                    log_action(
                        user["username"],
                        user["role"],
                        "backup_failed",
                        f"Backup error: {str(e)[:100]}",
                    )
        
        with col4:
            st.markdown("**Restore from Backup**")
            backup_dir = os.path.normpath(os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "data", "backups"
            ))
            
            if os.path.exists(backup_dir):
                backups = sorted(os.listdir(backup_dir), reverse=True)
                if backups:
                    selected_backup = st.selectbox(
                        "Select backup to restore",
                        backups,
                        key="backup_select"
                    )
                    
                    if st.button("Restore Selected Backup", use_container_width=True):
                        backup_path = os.path.join(backup_dir, selected_backup)
                        try:
                            if restore_from_backup(backup_path):
                                st.success(f"Restored from: {selected_backup}")
                                log_action(
                                    user["username"],
                                    user["role"],
                                    "restore_backup",
                                    f"Restored from: {selected_backup}",
                                )
                                st.rerun()
                            else:
                                st.error("Restore failed")
                                log_action(
                                    user["username"],
                                    user["role"],
                                    "restore_backup_failed",
                                    f"Failed to restore: {selected_backup}",
                                )
                        except Exception as e:
                            st.error(f"Restore error: {e}")
                            log_action(
                                user["username"],
                                user["role"],
                                "restore_backup_error",
                                f"Restore error: {str(e)[:100]}",
                            )
                else:
                    st.info("No backups available yet")
            else:
                st.info("Backup directory not created yet")
        
        with col5:
            st.markdown("**Data Retention Timer**")
            retention_days = st.number_input(
                "Retention Period (days)",
                min_value=1,
                max_value=365,
                value=90,
                key="retention_days",
                help="Delete data older than specified days (GDPR compliance)"
            )
            
            if st.button("Run Data Cleanup", use_container_width=True):
                try:
                    result = cleanup_old_data(retention_days)
                    if result:
                        st.success(
                            f"Cleanup completed:\n"
                            f"- {result['logs_deleted']} log entries deleted\n"
                            f"- {result['patients_deleted']} patient records deleted"
                        )
                        log_action(
                            user["username"],
                            user["role"],
                            "data_retention_cleanup",
                            f"Deleted data older than {retention_days} days",
                        )
                    else:
                        st.warning("Cleanup failed or no data to delete")
                except Exception as e:
                    st.error(f"Cleanup error: {e}")
                    log_action(
                        user["username"],
                        user["role"],
                        "data_retention_error",
                        f"Cleanup error: {str(e)[:100]}",
                    )
    
    elif selected_page == "patient_list":
        st.header("Patient Records")
        st.subheader("Full View (Decrypted + Anonymized)")
        
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, name, contact, diagnosis, anonymized_name, anonymized_contact, 
                       encrypted_name, encrypted_contact, created_at
                FROM patients;
                """
            )
            patients = cur.fetchall()
            conn.close()

            if patients:
                patients_data = []
                for p in patients:
                    patient_dict = dict(p)
                    if patient_dict.get("encrypted_name"):
                        patient_dict["decrypted_name"] = decrypt_data(patient_dict["encrypted_name"]) or patient_dict.get("name", "N/A")
                    else:
                        patient_dict["decrypted_name"] = patient_dict.get("name", "N/A")
                    
                    if patient_dict.get("encrypted_contact"):
                        patient_dict["decrypted_contact"] = decrypt_data(patient_dict["encrypted_contact"]) or patient_dict.get("contact", "N/A")
                    else:
                        patient_dict["decrypted_contact"] = patient_dict.get("contact", "N/A")
                    
                    patients_data.append(patient_dict)
                
                df_patients = pd.DataFrame(patients_data)
                display_columns = ["id", "decrypted_name", "decrypted_contact", "diagnosis", 
                                  "anonymized_name", "anonymized_contact", "created_at"]
                df_display = df_patients[[col for col in display_columns if col in df_patients.columns]]
                df_display.rename(columns={
                    "decrypted_name": "Name (Decrypted)",
                    "decrypted_contact": "Contact (Decrypted)"
                }, inplace=True)
                st.dataframe(df_display, use_container_width=True)
                
                csv_data = df_patients.to_csv(index=False)
                st.download_button(
                    label="Download Patients as CSV",
                    data=csv_data,
                    file_name="patient_records.csv",
                    mime="text/csv",
                )
                
                st.markdown(f"Showing {len(patients)} patients (with Fernet decryption)")
            else:
                st.markdown("No patients in the system yet.")
                
        except Exception as e:
            st.error(f"Error loading patient data: {e}")
            try:
                log_action(
                    user["username"],
                    user["role"],
                    "patient_list_error",
                    f"Failed to load patients: {str(e)[:100]}",
                )
            except:
                pass
    
    elif selected_page == "logs":
        st.header("Audit Logs")
        st.write("Complete audit trail of all system activities for GDPR compliance and forensic analysis.")
        
        try:
            logs = get_logs(100)
            
            if logs:
                logs_data = [dict(log) for log in logs]
                df_logs = pd.DataFrame(logs_data)
                st.dataframe(df_logs, use_container_width=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    csv_data = df_logs.to_csv(index=False)
                    st.download_button(
                        label="Download Logs as CSV",
                        data=csv_data,
                        file_name="audit_logs.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("SELECT * FROM patients;")
                        patients = cur.fetchall()
                        conn.close()
                        
                        if patients:
                            patients_data = [dict(p) for p in patients]
                            df_patients = pd.DataFrame(patients_data)
                            csv_patients = df_patients.to_csv(index=False)
                            st.download_button(
                                label="Download Patients as CSV",
                                data=csv_patients,
                                file_name="patients.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    except Exception as e:
                        st.warning(f"Could not export patients: {e}")
                
                st.divider()
                
                st.markdown("### Activity Overview")
                if "action" in df_logs.columns:
                    action_counts = df_logs["action"].value_counts()
                    st.bar_chart(
                        action_counts,
                        use_container_width=True,
                        color="#6eb52f"
                    )
                else:
                    st.warning("Action column not found in logs")
                
                st.markdown(f"Showing {len(logs)} most recent log entries")
            else:
                st.markdown("No log entries yet.")
                
        except Exception as e:
            st.error(f"Error loading audit logs: {e}")
            try:
                log_action(
                    user["username"],
                    user["role"],
                    "logs_view_error",
                    f"Failed to load logs: {str(e)[:100]}",
                )
            except:
                pass
    
    try:
        log_action(
            user["username"],
            user["role"],
            "view_admin_dashboard",
            f"Admin viewed {selected_page} page.",
        )
    except Exception as e:
        print(f"Could not log dashboard view: {e}")
