import streamlit as st
import pandas as pd
import os

from backend.db import get_connection, check_database_availability, create_database_backup, restore_from_backup
from backend.logs import get_logs, log_action, cleanup_old_data
from backend.data_protection import anonymize_all_patients, decrypt_data
from ui.common import show_sidebar_navigation, show_dashboard_analytics


def render_admin_view(user):
    selected_page = show_sidebar_navigation(user)

    # -------------------
    # DASHBOARD PAGE
    # -------------------
    if selected_page == "dashboard":
        try:
            show_dashboard_analytics(user)
        except Exception as e:
            st.error(f"Error loading dashboard analytics: {e}")
            try:
                log_action(user["username"], user["role"], "dashboard_error", str(e)[:100])
            except: pass

        st.divider()
        st.markdown("### Quick Actions & System Management")

        # Organize Quick Actions and System Management in 2 sections
        quick_col, sys_col = st.columns([1, 2])

        # -------------------
        # Quick Actions
        # -------------------
        with quick_col:
            st.markdown("#### Patient Data")
            if st.button("Anonymize All Patients", use_container_width=True):
                try:
                    backup = create_database_backup()
                    if backup:
                        st.info(f"Backup created: {os.path.basename(backup)}")
                    anonymize_all_patients()
                    log_action(user["username"], user["role"], "anonymize_all_patients", "Anonymization run")
                    st.success("Anonymization Completed!")
                except Exception as e:
                    st.error(f"Anonymization failed: {e}")
                    log_action(user["username"], user["role"], "anonymize_all_patients_failed", str(e)[:100])

            if st.button("Check Database Status", use_container_width=True):
                available = check_database_availability()
                if available:
                    st.success("Database is healthy ✅")
                    log_action(user["username"], user["role"], "check_database_status", "OK")
                else:
                    st.error("Database unavailable ❌")
                    log_action(user["username"], user["role"], "check_database_status_failed", "FAILED")

        # -------------------
        # System Management
        # -------------------
        with sys_col:
            st.markdown("#### Database & Retention")
            sys1, sys2, sys3 = st.columns(3)

            with sys1:
                if st.button("Create Backup", use_container_width=True):
                    try:
                        backup_path = create_database_backup()
                        if backup_path:
                            st.success(f"Backup created: {os.path.basename(backup_path)}")
                            log_action(user["username"], user["role"], "create_backup", backup_path)
                        else:
                            st.warning("Backup failed")
                    except Exception as e:
                        st.error(f"Backup failed: {e}")
                        log_action(user["username"], user["role"], "backup_failed", str(e)[:100])

            with sys2:
                st.markdown("**Restore Backup**")
                backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "backups")
                if os.path.exists(backup_dir):
                    backups = sorted(os.listdir(backup_dir), reverse=True)
                    if backups:
                        selected_backup = st.selectbox("Select backup", backups, key="backup_select")
                        if st.button("Restore", use_container_width=True):
                            backup_path = os.path.join(backup_dir, selected_backup)
                            try:
                                if restore_from_backup(backup_path):
                                    st.success(f"Restored: {selected_backup}")
                                    log_action(user["username"], user["role"], "restore_backup", selected_backup)
                                    st.rerun()
                                else:
                                    st.error("Restore failed")
                            except Exception as e:
                                st.error(f"Restore error: {e}")
                                log_action(user["username"], user["role"], "restore_backup_error", str(e)[:100])
                    else:
                        st.info("No backups available")
                else:
                    st.info("Backup directory not created")

            with sys3:
                st.markdown("**Data Retention**")
                retention_days = st.number_input(
                    "Retention (days)", min_value=1, max_value=365, value=90,
                    help="Delete old data for GDPR compliance"
                )
                if st.button("Run Cleanup", use_container_width=True):
                    try:
                        result = cleanup_old_data(retention_days)
                        if result:
                            st.success(
                                f"Logs deleted: {result['logs_deleted']}\nPatients deleted: {result['patients_deleted']}"
                            )
                            log_action(user["username"], user["role"], "data_retention_cleanup", f"{retention_days} days")
                        else:
                            st.warning("Nothing to delete")
                    except Exception as e:
                        st.error(f"Cleanup error: {e}")
                        log_action(user["username"], user["role"], "data_retention_error", str(e)[:100])

    # -------------------
    # PATIENT LIST PAGE
    # -------------------
    elif selected_page == "patient_list":
        st.header("Patient Records")
        st.subheader("Full View (Decrypted + Anonymized)")

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, contact, diagnosis, anonymized_name, anonymized_contact,
                       encrypted_name, encrypted_contact, created_at
                FROM patients;
            """)
            patients = cur.fetchall()
            conn.close()

            if patients:
                patients_data = []
                for p in patients:
                    pdict = dict(p)
                    pdict["decrypted_name"] = decrypt_data(pdict.get("encrypted_name")) or pdict.get("name", "N/A")
                    pdict["decrypted_contact"] = decrypt_data(pdict.get("encrypted_contact")) or pdict.get("contact", "N/A")
                    patients_data.append(pdict)

                df_patients = pd.DataFrame(patients_data)
                display_cols = ["id", "decrypted_name", "decrypted_contact", "diagnosis",
                                "anonymized_name", "anonymized_contact", "created_at"]
                df_display = df_patients[[c for c in display_cols if c in df_patients.columns]]
                df_display.rename(columns={
                    "decrypted_name": "Name (Decrypted)",
                    "decrypted_contact": "Contact (Decrypted)"
                }, inplace=True)

                st.dataframe(df_display, use_container_width=True)
                st.download_button("Download CSV", df_patients.to_csv(index=False), "patient_records.csv", "text/csv")
                st.markdown(f"Showing {len(patients)} patients")
            else:
                st.info("No patients yet")

        except Exception as e:
            st.error(f"Error loading patient data: {e}")
            try:
                log_action(user["username"], user["role"], "patient_list_error", str(e)[:100])
            except: pass

    # -------------------
    # AUDIT LOGS PAGE
    # -------------------
    elif selected_page == "logs":
        st.header("Audit Logs")
        st.markdown("Complete audit trail of system activities for GDPR compliance.")

        try:
            logs = get_logs(100)
            if logs:
                df_logs = pd.DataFrame([dict(l) for l in logs])
                st.dataframe(df_logs, use_container_width=True)

                dl_col1, dl_col2 = st.columns(2)
                with dl_col1:
                    st.download_button("Download Logs CSV", df_logs.to_csv(index=False), "audit_logs.csv", "text/csv")
                with dl_col2:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("SELECT * FROM patients;")
                        patients = cur.fetchall()
                        conn.close()
                        if patients:
                            df_pat = pd.DataFrame([dict(p) for p in patients])
                            st.download_button("Download Patients CSV", df_pat.to_csv(index=False), "patients.csv", "text/csv")
                    except Exception as e:
                        st.warning(f"Could not export patients: {e}")

                st.divider()
                st.markdown("### Activity Overview")
                if "action" in df_logs.columns:
                    st.bar_chart(df_logs["action"].value_counts(), color="#dc2626")
                st.markdown(f"Showing {len(logs)} recent entries")
            else:
                st.info("No logs yet")
        except Exception as e:
            st.error(f"Error loading audit logs: {e}")
            try:
                log_action(user["username"], user["role"], "logs_view_error", str(e)[:100])
            except: pass

    try:
        log_action(user["username"], user["role"], "view_admin_dashboard", f"Viewed {selected_page}")
    except Exception as e:
        print(f"Log failed: {e}")
