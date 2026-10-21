import os
import sqlite3
import pandas as pd
import streamlit as st
import io

# =========================================================
# PAGE CONFIGURATION & BRANDING
# =========================================================
st.set_page_config(
    page_title="HYDAC Lab Queue Tracker",
    page_icon="⚡",
    layout="wide"
)

DB_FILE = "lab_queue.db"
LOCAL_CERTS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Certs"

# Custom CSS for Synced Email Badges
st.markdown("""
    <style>
    .badge-email {
        background-color: #2e7d32;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .badge-reply {
        background-color: #1565c0;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# HELPER FUNCTIONS & DATA LOADING
# =========================================================
def load_data():
    """Loads the lab queue dataframe cleanly from the local SQLite database."""
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query("SELECT * FROM queue", conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

def build_unit_dropdown_options(df):
    """Formats dropdown labels into: RGA: X | Notif: Y | Model | SN: Z (Unit ID: N)."""
    options_map = {}
    if df is None or df.empty:
        return options_map

    for _, row in df.iterrows():
        unit_id = row.get("id", "")
        rga = str(row.get("rga_number", "")).replace("nan", "").strip() or "N/A"
        notif = str(row.get("notification_number", "")).replace("nan", "").strip() or "N/A"
        model = row.get("model_series") or row.get("model") or row.get("item_description") or "N/A"
        sn = str(row.get("serial_number", "")).replace("nan", "").strip() or "N/A"

        label = f"RGA: {rga} | Notif: {notif} | {model} | SN: {sn} (Unit ID: {unit_id})"
        options_map[label] = unit_id

    return options_map

# Load dataset into memory
df_queue = load_data()

# =========================================================
# HEADER & LOGO
# =========================================================
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=110)
    else:
        st.title("⚡")

with col_title:
    st.title("Enterprise Electronic Lab: Operations Command")

# =========================================================
# ENVIRONMENT TOGGLE (Cloud vs Local PC Mode)
# =========================================================
st.divider()
toggle_col, status_col = st.columns([2, 3])

with toggle_col:
    is_local_mode = st.toggle("🖥️ Enable Local PC Mode (Folder Creation)", value=False)

with status_col:
    if is_local_mode:
        st.success(f"Mode: **Local PC** — Direct folder creation enabled at:\n`{LOCAL_CERTS_DIR}`")
    else:
        st.info("Mode: **Streamlit Cloud** — Read-only web mode (Local folder creation disabled).")

st.divider()

# =========================================================
# SIDEBAR NAVIGATION
# =========================================================
st.sidebar.header("Navigation")
menu_choice = st.sidebar.radio(
    "Select Workflow",
    [
        "📊 View Queue Dashboard",
        "📁 Create Local Certificate Folder",
        "📩 Synced Email Threads",
        "📥 Backup & Data Export"
    ]
)

# =========================================================
# WORKFLOW 1: VIEW QUEUE DASHBOARD
# =========================================================
if menu_choice == "📊 View Queue Dashboard":
    st.subheader("📊 Active Lab Queue Dashboard")

    if df_queue.empty:
        st.warning("No records found in `lab_queue.db`.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Units in Queue", len(df_queue))
        
        synced_emails_count = df_queue['notes'].dropna().apply(lambda x: '[Synced Email' in str(x)).sum() if 'notes' in df_queue.columns else 0
        m2.metric("Units with Synced Emails", synced_emails_count)
        
        rga_count = df_queue['rga_number'].dropna().replace("nan", "").ne("").sum() if 'rga_number' in df_queue.columns else 0
        m3.metric("RGAs Active", rga_count)

        notif_count = df_queue['notification_number'].dropna().replace("nan", "").ne("").sum() if 'notification_number' in df_queue.columns else 0
        m4.metric("Notifications Active", notif_count)

        st.markdown("---")
        search_term = st.text_input("🔍 Filter Queue (RGA, Notification, Customer, Model, Serial Number):")
        
        if search_term:
            filter_mask = df_queue.astype(str).apply(lambda col: col.str.contains(search_term, case=False)).any(axis=1)
            display_df = df_queue[filter_mask]
        else:
            display_df = df_queue

        st.dataframe(display_df, use_container_width=True)

        st.markdown("### 🔎 Unit Detail & Outcome Notes Inspection")
        unit_map = build_unit_dropdown_options(display_df)
        
        if unit_map:
            selected_inspect_label = st.selectbox("Select Unit to Inspect Details & Synced Notes:", options=list(unit_map.keys()), key="inspect_select")
            selected_id = unit_map[selected_inspect_label]
            selected_row = display_df[display_df["id"] == selected_id].iloc[0]

            with st.expander(f"📋 Details for Unit ID {selected_id}", expanded=True):
                c1, c2, c3 = st.columns(3)
                c1.write(f"**RGA Number:** {selected_row.get('rga_number', 'N/A')}")
                c2.write(f"**Notification Number:** {selected_row.get('notification_number', 'N/A')}")
                c3.write(f"**Customer Name:** {selected_row.get('customer_name', 'N/A')}")

                c4, c5, c6 = st.columns(3)
                c4.write(f"**Model / Item:** {selected_row.get('model_series') or selected_row.get('model') or selected_row.get('item_description') or 'N/A'}")
                c5.write(f"**Serial Number:** {selected_row.get('serial_number', 'N/A')}")
                c6.write(f"**Status / Location:** {selected_row.get('status', 'N/A')}")

                notes_val = str(selected_row.get('notes', '') or '')
                if "[Synced Email from Returns" in notes_val:
                    st.markdown('<span class="badge-email">⭐ Returns Email Synced</span>', unsafe_allow_html=True)
                if "[Synced Sent Reply" in notes_val:
                    st.markdown('<span class="badge-reply">✅ Outbox Reply Sent</span>', unsafe_allow_html=True)

                st.text_area("Outcome / Notes History:", value=notes_val, height=220, disabled=True)

# =========================================================
# WORKFLOW 2: CREATE LOCAL CERTIFICATE FOLDER
# =========================================================
elif menu_choice == "📁 Create Local Certificate Folder":
    st.subheader("📁 Create Local Certificate Folder")

    if df_queue.empty:
        st.warning("No unit records available to generate folders.")
    else:
        unit_map = build_unit_dropdown_options(df_queue)

        if unit_map:
            selected_label = st.selectbox(
                "Select Unit for Cert Folder Creation:",
                options=list(unit_map.keys()),
                key="cert_folder_select"
            )

            selected_id = unit_map[selected_label]
            selected_row = df_queue[df_queue["id"] == selected_id].iloc[0]

            st.markdown("---")
            st.markdown("#### Selected Unit Summary")
            c1, c2, c3 = st.columns(3)
            c1.write(f"**RGA Number:** `{selected_row.get('rga_number', 'N/A')}`")
            c2.write(f"**Notification:** `{selected_row.get('notification_number', 'N/A')}`")
            c3.write(f"**Serial Number:** `{selected_row.get('serial_number', 'N/A')}`")

            st.markdown("---")

            if is_local_mode:
                if st.button("📁 Create Folder Structure on Local PC", type="primary"):
                    rga_clean = str(selected_row.get("rga_number", "UNKNOWN")).replace("nan", "").strip() or "NO_RGA"
                    sn_clean = str(selected_row.get("serial_number", "UNKNOWN")).replace("nan", "").strip() or "NO_SN"
                    folder_title = f"RGA_{rga_clean}_SN_{sn_clean}"
                    target_dir = os.path.join(LOCAL_CERTS_DIR, folder_title)

                    try:
                        os.makedirs(target_dir, exist_ok=True)
                        st.success(f"✅ Folder successfully created locally:\n`{target_dir}`")
                    except Exception as err:
                        st.error(f"❌ Failed to create folder directory: {err}")
            else:
                st.warning(
                    "⚠️ **Local Folder Creation is disabled in Cloud Mode.**\n\n"
                    "To create folders on your local PC:\n"
                    "1. Run the app locally on your PC via `run_app.bat`.\n"
                    "2. Switch the **Enable Local PC Mode** toggle at the top of the page to **ON**."
                )

# =========================================================
# WORKFLOW 3: SYNCED EMAIL THREADS
# =========================================================
elif menu_choice == "📩 Synced Email Threads":
    st.subheader("📩 Synced Outlook Email Communications")

    if df_queue.empty:
        st.warning("No records found in `lab_queue.db`.")
    else:
        email_units = df_queue[df_queue['notes'].fillna('').str.contains('\\[Synced', case=False)]
        
        if email_units.empty:
            st.info("No Outlook emails have been synced for any unit yet. Run `sync_and_push.bat` on your PC to scan Outlook.")
        else:
            unit_map = build_unit_dropdown_options(email_units)
            selected_label = st.selectbox("Select Unit with Synced Emails:", options=list(unit_map.keys()))
            selected_id = unit_map[selected_label]
            selected_row = email_units[email_units["id"] == selected_id].iloc[0]

            st.markdown(f"### Synced Correspondence for Unit ID {selected_id}")
            st.text_area("Full Synced Outlook Thread:", value=str(selected_row.get("notes", "")), height=350, disabled=True)

# =========================================================
# WORKFLOW 4: BACKUP & DATA EXPORT
# =========================================================
elif menu_choice == "📥 Backup & Data Export":
    st.subheader("📥 Data Export & Database Backup")

    if not df_queue.empty:
        st.markdown("Download a full snapshot of your current lab queue database records:")
        
        c_csv, c_excel = st.columns(2)
        
        with c_csv:
            csv_bytes = df_queue.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV Export",
                data=csv_bytes,
                file_name="lab_queue_backup.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with c_excel:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_queue.to_excel(writer, index=False, sheet_name='Lab Queue')
            excel_bytes = output.getvalue()
            
            st.download_button(
                label="📥 Download Excel Backup (.xlsx)",
                data=excel_bytes,
                file_name="lab_queue_backup.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.warning("No data currently available to export.")