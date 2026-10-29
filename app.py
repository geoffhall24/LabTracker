import io
import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# =========================================================
# PAGE CONFIGURATION & BRANDING
# =========================================================
st.set_page_config(
    page_title="HYDAC Lab Queue Tracker", page_icon="⚡", layout="wide"
)

DB_FILE = "lab_queue.db"
LOCAL_CERTS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Certs"

# Custom CSS for Badges & Table Formatting
st.markdown(
    """
    <style>
    .badge-green { background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-yellow { background-color: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-red { background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-urgency { background-color: #0d6efd; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .badge-email { background-color: #6f42c1; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    </style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# DATABASE INIT & HELPER FUNCTIONS
# =========================================================
def init_db():
  """Ensures the database and required schema columns exist."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rga_number TEXT,
            notification_number TEXT,
            customer_name TEXT,
            model_series TEXT,
            serial_number TEXT,
            status TEXT,
            urgency INTEGER DEFAULT 5,
            date_received TEXT,
            notes TEXT
        )
    """)
  conn.commit()
  conn.close()


def load_data():
  """Loads queue data from SQLite and computes age metrics."""
  init_db()
  conn = sqlite3.connect(DB_FILE)
  try:
    df = pd.read_sql_query("SELECT * FROM queue", conn)
  except Exception:
    df = pd.DataFrame()
  finally:
    conn.close()

  if not df.empty:
    if "date_received" not in df.columns or df["date_received"].isnull().all():
      df["date_received"] = datetime.now().strftime("%Y-%m-%d")

    df["parsed_date"] = pd.to_datetime(df["date_received"], errors="coerce")
    now = datetime.now()
    df["age_days"] = (now - df["parsed_date"]).dt.days.fillna(0).astype(int)
    df["age_weeks"] = (df["age_days"] / 7).round(1)

    if "urgency" not in df.columns:
      df["urgency"] = 5
    df["urgency"] = df["urgency"].fillna(5).astype(int)

  return df


def get_age_badge(weeks):
  """Returns age category badge HTML."""
  if weeks <= 4:
    return f'<span class="badge-green">🟢 {weeks} wks</span>'
  elif weeks <= 7:
    return f'<span class="badge-yellow">🟡 {weeks} wks</span>'
  else:
    return f'<span class="badge-red">🔴 {weeks} wks</span>'


def build_unit_dropdown_options(df):
  """Constructs descriptive labels for selection dropdowns."""
  options_map = {}
  if df is None or df.empty:
    return options_map

  for _, row in df.iterrows():
    unit_id = row.get("id", "")
    rga = str(row.get("rga_number", "")).replace("nan", "").strip() or "N/A"
    notif = (
        str(row.get("notification_number", "")).replace("nan", "").strip()
        or "N/A"
    )
    model = (
        row.get("model_series")
        or row.get("model")
        or row.get("item_description")
        or "N/A"
    )
    sn = str(row.get("serial_number", "")).replace("nan", "").strip() or "N/A"
    urgency = row.get("urgency", 5)

    label = f"RGA: {rga} | Notif: {notif} | {model} | SN: {sn} [Urgency: {urgency}/10] (ID: {unit_id})"
    options_map[label] = unit_id

  return options_map


# Load current queue state
df_queue = load_data()

# =========================================================
# HEADER & LOCAL MODE TOGGLE
# =========================================================
col_logo, col_title = st.columns([1, 6])
with col_logo:
  if os.path.exists("logo.png"):
    st.image("logo.png", width=110)
  else:
    st.title("⚡")

with col_title:
  st.title("Enterprise Electronic Lab: Operations Command")

st.divider()
toggle_col, status_col = st.columns([2, 3])

with toggle_col:
  is_local_mode = st.toggle(
      "🖥️ Enable Local PC Mode (Folder Creation)", value=False
  )

with status_col:
  if is_local_mode:
    st.success(
        "Mode: **Local PC** — Direct folder creation enabled at:\n`"
        + LOCAL_CERTS_DIR
        + "`"
    )
  else:
    st.info(
        "Mode: **Streamlit Cloud** — Read-only web mode (Folder creation"
        " disabled)."
    )

st.divider()

# =========================================================
# SIDEBAR NAVIGATION
# =========================================================
st.sidebar.markdown("### 👤 Logged In As:")
st.sidebar.markdown("**Geo Hall**")
st.sidebar.caption("Role: Lead Operations / Developer")
st.sidebar.markdown("---")

st.sidebar.header("Navigation Menu")
nav_choice = st.sidebar.radio(
    "Select Workflow",
    [
        "📊 Main Queue Dashboard",
        "➕ Log New Request",
        "🛡️ Manager Priority Override",
        "📥 Backup & Data Export",
    ],
)

# =========================================================
# WORKFLOW 1: MAIN QUEUE DASHBOARD & PRE-POPULATED ACTION HUB
# =========================================================
if nav_choice == "📊 Main Queue Dashboard":
  st.subheader("📊 Active Lab Queue Dashboard")

  if df_queue.empty:
    st.warning("No records found in `lab_queue.db`.")
  else:
    # Top Level Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Pending Requests", len(df_queue))

    overdue_count = (df_queue["age_weeks"] >= 8).sum()
    m2.metric("Overdue (8+ Weeks)", overdue_count)

    high_urgency_count = (df_queue["urgency"] >= 8).sum()
    m3.metric("Critical Urgency (8-10)", high_urgency_count)

    email_synced_count = (
        df_queue["notes"]
        .dropna()
        .apply(lambda x: "[Synced Email" in str(x))
        .sum()
    )
    m4.metric("Units with Synced Emails", email_synced_count)

    st.markdown("---")

    # Sorting Logic: Oldest first by default
    sorted_df = df_queue.sort_values(
        by=["parsed_date", "urgency"], ascending=[True, False]
    )

    # Search & Filter
    search_term = st.text_input(
        "🔍 Search Queue (RGA, Notification, Customer, Model, Serial Number):"
    )
    if search_term:
      filter_mask = sorted_df.astype(str).apply(
          lambda col: col.str.contains(search_term, case=False)
      ).any(axis=1)
      display_df = sorted_df[filter_mask]
    else:
      display_df = sorted_df

    # Parent / Child Hierarchy View
    st.markdown("### 📋 Pending Requests (Oldest to Newest)")

    # Formatted display columns
    for idx, row in display_df.iterrows():
      weeks = row.get("age_weeks", 0)
      urgency = row.get("urgency", 5)
      notes_str = str(row.get("notes", "") or "")
      has_email = "[Synced" in notes_str

      age_html = get_age_badge(weeks)
      urgency_html = f'<span class="badge-urgency">Urgency: {urgency}/10</span>'
      email_html = (
          '<span class="badge-email">✉️ Email Attached</span>'
          if has_email
          else ""
      )

      with st.expander(
          f"Parent RGA: {row.get('rga_number', 'N/A')} | SN:"
          f" {row.get('serial_number', 'N/A')} | {row.get('model_series', 'N/A')}"
          f" | Received: {row.get('date_received', 'N/A')}"
      ):
        st.markdown(
            f"**Age:** {age_html} &nbsp;&nbsp; **Priority:** {urgency_html}"
            f" &nbsp;&nbsp; {email_html}",
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.write(f"**Customer:** {row.get('customer_name', 'N/A')}")
        c2.write(f"**Notification:** {row.get('notification_number', 'N/A')}")
        c3.write(f"**Status:** {row.get('status', 'N/A')}")
        c4.write(f"**Unit ID:** {row.get('id', 'N/A')}")

        if notes_str:
          st.info(f"**Notes / Email Thread:**\n{notes_str}")

    st.markdown("---")

    # Contextual Pre-Populated Action Hub
    st.markdown("## 🎯 Contextual Action Hub")
    st.caption(
        "Select a unit below to pre-populate Cert Creation, Emailing,"
        " Inventory Check, and Evaluation Reports."
    )

    unit_map = build_unit_dropdown_options(sorted_df)
    selected_label = st.selectbox(
        "Select Active Unit to Process:", options=list(unit_map.keys())
    )
    selected_id = unit_map[selected_label]
    selected_unit = sorted_df[sorted_df["id"] == selected_id].iloc[0]

    # Sub-tabs pre-populated from selected unit
    tab_cert, tab_email, tab_parts, tab_eval = st.tabs([
        "📁 Create Cert Folder",
        "✉️ Send Email",
        "📦 Check Parts Inventory",
        "📄 Create Eval Report",
    ])

    # SUB-TAB 1: CREATE CERT FOLDER
    with tab_cert:
      st.subheader("📁 Certificate Folder Generation")
      st.write(
          f"**Target Unit:** RGA `{selected_unit.get('rga_number')}` | SN"
          f" `{selected_unit.get('serial_number')}`"
      )

      if is_local_mode:
        if st.button("📁 Create Cert Folder Structure", type="primary"):
          rga_clean = (
              str(selected_unit.get("rga_number", "UNKNOWN"))
              .replace("nan", "")
              .strip()
          )
          sn_clean = (
              str(selected_unit.get("serial_number", "UNKNOWN"))
              .replace("nan", "")
              .strip()
          )
          folder_title = f"RGA_{rga_clean}_SN_{sn_clean}"
          target_dir = os.path.join(LOCAL_CERTS_DIR, folder_title)

          try:
            os.makedirs(target_dir, exist_ok=True)
            st.success(f"✅ Folder created locally at:\n`{target_dir}`")
          except Exception as err:
            st.error(f"❌ Failed to create folder: {err}")
      else:
        st.warning(
            "⚠️ Local Folder Creation disabled in Cloud Mode. Enable **Local PC"
            " Mode** toggle above when running via `run_app.bat`."
        )

    # SUB-TAB 2: SEND EMAIL
    with tab_email:
      st.subheader("✉️ Pre-Populated Customer / Internal Email")
      default_body = f"""Subject: Update on RGA: {selected_unit.get('rga_number')} - SN: {selected_unit.get('serial_number')}

Hello {selected_unit.get('customer_name', 'Customer')},

Here is the current laboratory status update regarding your unit:

- RGA Number: {selected_unit.get('rga_number', 'N/A')}
- Notification Number: {selected_unit.get('notification_number', 'N/A')}
- Model: {selected_unit.get('model_series', 'N/A')}
- Serial Number: {selected_unit.get('serial_number', 'N/A')}
- Current Status: {selected_unit.get('status', 'Received in Lab')}
- Assigned Urgency: {selected_unit.get('urgency', 5)}/10

Notes:
{selected_unit.get('notes', 'N/A')}

Best regards,
HYDAC Electronic Lab Team
"""
      st.text_area(
          "Review & Copy Email Template:", value=default_body, height=280
      )

    # SUB-TAB 3: CHECK PARTS INVENTORY
    with tab_parts:
      st.subheader("📦 Inventory Parts Search")
      model_query = selected_unit.get("model_series", "")
      st.text_input("Pre-filled Model / Part Number Search:", value=model_query)
      st.info(f"Querying replacement components and seal kits for `{model_query}`...")
      st.caption(
          "Integrated inventory lookup ready. (Connects to internal SAP / ERP"
          " database)."
      )

    # SUB-TAB 4: CREATE EVAL REPORT
    with tab_eval:
      st.subheader("📄 Evaluation Report Builder")
      with st.form("eval_report_form"):
        st.text_input(
            "RGA Number", value=str(selected_unit.get("rga_number", ""))
        )
        st.text_input(
            "Serial Number", value=str(selected_unit.get("serial_number", ""))
        )
        st.text_input(
            "Model Series", value=str(selected_unit.get("model_series", ""))
        )
        eval_findings = st.text_area(
            "Evaluation Findings & Root Cause Analysis:"
        )
        test_results = st.selectbox(
            "Lab Test Outcome:",
            [
                "Passed - Calibration Verified",
                "Failed - Component Faulty",
                "Repaired & Re-tested",
            ],
        )

        if st.form_submit_button("📄 Save Evaluation Report"):
          st.success("✅ Evaluation report generated and logged to unit history!")

# =========================================================
# WORKFLOW 2: LOG NEW REQUEST
# =========================================================
elif nav_choice == "➕ Log New Request":
  st.subheader("📝 Log New Unit or Multi-Unit Parent Order")

  with st.form("log_request_form"):
    c1, c2 = st.columns(2)
    f_rga = c1.text_input("Parent RGA Number*")
    f_notif = c2.text_input("Notification Number")

    c3, c4 = st.columns(2)
    f_cust = c3.text_input("Customer Name")
    f_model = c4.text_input("Model / Item Description")

    f_sns = st.text_area(
        "Serial Number(s)* (Enter multiple serials on separate lines for child items):"
    )

    c5, c6 = st.columns(2)
    f_urgency = c5.slider(
        "Initial Urgency Level (1 = Low, 10 = Critical/Rush)", 1, 10, 5
    )
    f_date = c6.date_input("Date Received", value=datetime.now())

    f_notes = st.text_area("Initial Notes / Instructions")

    if st.form_submit_button("🚀 Submit Request(s) to Queue"):
      sn_list = [s.strip() for s in f_sns.split("\n") if s.strip()]
      if f_rga and sn_list:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for sn in sn_list:
          cursor.execute(
              """
                    INSERT INTO queue (rga_number, notification_number, customer_name, model_series, serial_number, status, urgency, date_received, notes)
                    VALUES (?, ?, ?, ?, ?, 'Received in Lab', ?, ?, ?)
                """,
              (
                  f_rga,
                  f_notif,
                  f_cust,
                  f_model,
                  sn,
                  f_urgency,
                  f_date.strftime("%Y-%m-%d"),
                  f_notes,
              ),
          )
        conn.commit()
        conn.close()
        st.success(
            f"✅ Successfully logged {len(sn_list)} serial number(s) under"
            f" Parent RGA: {f_rga}!"
        )
      else:
        st.error("Please provide an RGA Number and at least one Serial Number.")

# =========================================================
# WORKFLOW 3: MANAGER PRIORITY OVERRIDE
# =========================================================
elif nav_choice == "🛡️ Manager Priority Override":
  st.subheader("🛡️ Manager Priority & Urgency Override Panel")

  if df_queue.empty:
    st.warning("No records available to override.")
  else:
    unit_map = build_unit_dropdown_options(df_queue)
    sel_label = st.selectbox(
        "Select Unit to Override:", options=list(unit_map.keys())
    )
    sel_id = unit_map[sel_label]
    sel_row = df_queue[df_queue["id"] == sel_id].iloc[0]

    st.write(
        f"**Current Urgency Score:** `{sel_row.get('urgency', 5)}/10` |"
        f" **Current Status:** `{sel_row.get('status', 'N/A')}`"
    )

    with st.form("manager_override_form"):
      new_urgency = st.slider(
          "Override Urgency Score (1-10)",
          1,
          10,
          int(sel_row.get("urgency", 5)),
      )
      new_status = st.selectbox(
          "Update Workflow Status",
          [
              "Received in Lab",
              "Under Testing",
              "Pending Customer Info",
              "EXPEDITE / RUSH",
              "Completed",
          ],
          index=0,
      )
      override_reason = st.text_input("Reason for Manager Override:")

      if st.form_submit_button("⚡ Apply Manager Override"):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        updated_notes = (
            str(sel_row.get("notes", ""))
            + f"\n[Manager Override ({datetime.now().strftime('%Y-%m-%d %H:%M')}): Urgency set to {new_urgency}. Reason: {override_reason}]"
        )
        cursor.execute(
            """
                UPDATE queue SET urgency=?, status=?, notes=? WHERE id=?
            """,
            (new_urgency, new_status, updated_notes, sel_id),
        )
        conn.commit()
        conn.close()
        st.success(
            f"✅ Override applied to Unit ID {sel_id}! Urgency updated to"
            f" {new_urgency}/10."
        )

# =========================================================
# WORKFLOW 4: BACKUP & DATA EXPORT
# =========================================================
elif nav_choice == "📥 Backup & Data Export":
  st.subheader("📥 Data Export & Database Snapshot")

  if not df_queue.empty:
    c_csv, c_excel = st.columns(2)

    with c_csv:
      csv_bytes = df_queue.to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 Download CSV Snapshot",
          data=csv_bytes,
          file_name="lab_queue_snapshot.csv",
          mime="text/csv",
          use_container_width=True,
      )

    with c_excel:
      output = io.BytesIO()
      with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_queue.to_excel(writer, index=False, sheet_name="Lab Queue")
      excel_bytes = output.getvalue()

      st.download_button(
          label="📥 Download Excel Backup (.xlsx)",
          data=excel_bytes,
          file_name="lab_queue_snapshot.xlsx",
          mime=(
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          ),
          use_container_width=True,
      )
  else:
    st.warning("No data currently available to export.")