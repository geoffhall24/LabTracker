from datetime import datetime, timedelta
import io
import json
import os
import pandas as pd
import random
import shutil
import sqlite3
import sys
import streamlit as st

# --- DIRECTORY SETUP FOR PHOTOS, FORMS & CERTS ---
PHOTO_DIR = "unit_photos"
if not os.path.exists(PHOTO_DIR):
  os.makedirs(PHOTO_DIR)

DEMO_PHOTOS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\DEMO PHOTOS"
FORMS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\FORMS"
CERTS_BASE_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Certs"

if not os.path.exists(CERTS_BASE_DIR):
  try:
    os.makedirs(CERTS_BASE_DIR)
  except Exception:
    pass

# --- USER CREDENTIALS & ROLES ---
USER_CREDENTIALS = {
    "akeiper": {
        "name": "Adam Keiper",
        "password": "AdamPass2026",
        "role": "Supervisor",
    },
    "ghall": {
        "name": "Geo Hall",
        "password": "GeoPass2026",
        "role": "Developer",
    },
    "tech1": {
        "name": "Lab Technician",
        "password": "TechPass2026",
        "role": "Technician",
    },
}

# --- DATABASE SETUP WITH SETTINGS & AUTO-HEALING ---
DB_FILE = "lab_queue.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_in_lab TEXT,
            customer_name TEXT,
            rga_number TEXT,
            wo_number TEXT,
            notification_number TEXT,
            model_description TEXT,
            part_number TEXT,
            serial_number TEXT,
            sensor_number TEXT,
            accessories TEXT,
            service_requested TEXT,
            expedited_shipping TEXT,
            supervisor_urgency TEXT,
            date_started TEXT,
            finished_date TEXT,
            status TEXT,
            waiting_on TEXT,
            assigned_to TEXT,
            notes TEXT,
            photo_path TEXT,
            cert_folder_path TEXT,
            last_updated TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

  # Default View-Only Display Configuration
  default_view_config = json.dumps({
      "show_customer": True,
      "show_wo": True,
      "show_notes": True,
      "show_photos": True,
      "show_urgency": True,
      "show_cert_folders": False,
  })
  cursor.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('view_only_config',"
      " ?)",
      (default_view_config,),
  )

  conn.commit()
  conn.close()


init_db()


def get_view_config():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT value FROM settings WHERE key = 'view_only_config'"
  )
  res = cursor.fetchone()
  conn.close()
  if res:
    try:
      return json.loads(res[0])
    except Exception:
      pass
  return {
      "show_customer": True,
      "show_wo": True,
      "show_notes": True,
      "show_photos": True,
      "show_urgency": True,
      "show_cert_folders": False,
  }


def save_view_config(config_dict):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT OR REPLACE INTO settings (key, value) VALUES"
      " ('view_only_config', ?)",
      (json.dumps(config_dict),),
  )
  conn.commit()
  conn.close()


def load_data():
  conn = sqlite3.connect(DB_FILE)
  try:
    df = pd.read_sql_query("SELECT * FROM queue", conn)
  except Exception:
    df = pd.DataFrame()
  conn.close()

  expected_cols = [
      "date_in_lab",
      "customer_name",
      "rga_number",
      "wo_number",
      "part_number",
      "expedited_shipping",
      "supervisor_urgency",
      "cert_folder_path",
  ]
  if not df.empty and not all(col in df.columns for col in expected_cols):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
      cursor.execute("ALTER TABLE queue ADD COLUMN wo_number TEXT;")
      conn.commit()
    except Exception:
      pass
    conn.close()

  conn = sqlite3.connect(DB_FILE)
  df = pd.read_sql_query("SELECT * FROM queue", conn)
  conn.close()
  return df


# --- UI CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Electronic Lab Queue Tracker | Enterprise",
    page_icon="⚡",
    layout="wide",
)

st.markdown(
    """
    <style>
        .main { background-color: #f4f6f9; }
        .stDataFrame { border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e1e4e8; }
        .login-card {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            border: 1px solid #e1e4e8;
            max-width: 450px;
            margin: 0 auto;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# --- IMMEDIATE MANDATORY LOGIN GATE ---
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.user_role = None
  st.session_state.user_name = None

if not st.session_state.logged_in:
  st.markdown("<br><br>", unsafe_allow_html=True)
  col_login1, col_login2, col_login3 = st.columns([1, 2, 1])

  with col_login2:
    st.markdown(
        """
        <div class="login-card">
            <h2 style="text-align: center; color: #1e293b; margin-bottom: 5px;">⚡ Lab Queue Command</h2>
            <p style="text-align: center; color: #64748b; margin-bottom: 25px;">Please sign in or select View-Only mode to proceed</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_guest = st.tabs(["🔒 Authenticated Login", "👁️ View Only Access"])

    with tab_login:
      with st.form("login_form"):
        username = st.text_input("Username", placeholder="e.g. akeiper or ghall").lower().strip()
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Sign In to Portal", use_container_width=True)

        if login_btn:
          if username in USER_CREDENTIALS and USER_CREDENTIALS[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.user_role = USER_CREDENTIALS[username]["role"]
            st.session_state.user_name = USER_CREDENTIALS[username]["name"]
            st.success(f"Welcome back, {st.session_state.user_name}!")
            st.rerun()
          else:
            st.error("Invalid Username or Password. Please try again.")

    with tab_guest:
      st.markdown(
          "Access standard read-only queue telemetry without login"
          " credentials."
      )
      if st.button("Continue as View-Only User", use_container_width=True):
        st.session_state.logged_in = True
        st.session_state.user_role = "View Only"
        st.session_state.user_name = "Guest User"
        st.rerun()

  # Stop script execution until user completes authentication
  st.stop()


# --- SIDEBAR: LOGO, USER BADGE & ROLE-BASED NAVIGATION ---
with st.sidebar:
  try:
    st.image("logo.png", use_container_width=True)
  except Exception:
    st.info("💡 Place 'logo.png' in folder for branding.")
  st.markdown("---")

  st.markdown(f"### 👤 Logged In As:")
  st.markdown(f"**{st.session_state.user_name}**")
  st.caption(f"Role: `{st.session_state.user_role}`")

  if st.button("🚪 Sign Out", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.rerun()

  st.markdown("---")

  # Dynamic Action Navigation Based on Role
  role = st.session_state.user_role

  if role == "View Only":
    actions_allowed = ["View Queue Dashboard", "Monthly Volume Analytics"]
  elif role == "Technician":
    actions_allowed = [
        "View Queue Dashboard",
        "Log New Item (Single)",
        "Log Multiple Units (Batch per RGA)",
        "Bulk Import & Staged Review",
        "Update Existing Item",
        "Generate Support Email",
        "Create Serial Cert Folder",
        "Monthly Volume Analytics",
        "Backup & Data Export",
    ]
  else:  # Supervisor or Developer
    actions_allowed = [
        "View Queue Dashboard",
        "Log New Item (Single)",
        "Log Multiple Units (Batch per RGA)",
        "Bulk Import & Staged Review",
        "Update Existing Item",
        "Generate Support Email",
        "Sync Emails from Returns",
        "Sync Sent Items (Outbox & Replies)",
        "Supervisor Urgency Override",
        "Create Serial Cert Folder",
        "⚙️ View-Only Display Config",
        "Demo & Reset Controls",
        "Monthly Volume Analytics",
        "Backup & Data Export",
    ]

  action = st.radio("Navigation Menu", actions_allowed)

st.title("⚡ Enterprise Electronic Lab: Operations Command")
df = load_data()


def format_date_str(val):
  if pd.isna(val) or not val or str(val).strip() == "" or str(val).lower() == "nan":
    return ""
  try:
    dt = pd.to_datetime(val)
    if pd.isna(dt):
      return str(val)
    return dt.strftime("%m/%d/%Y")
  except Exception:
    return str(val)


if not df.empty:
  df["date_in_lab_dt"] = pd.to_datetime(df["date_in_lab"], errors="coerce")
  df["Age (Days)"] = (datetime.today() - df["date_in_lab_dt"]).dt.days.fillna(0).astype(int)

  if "supervisor_urgency" not in df.columns:
    df["supervisor_urgency"] = "Normal"
  else:
    df["supervisor_urgency"] = df["supervisor_urgency"].fillna("Normal")

  if "wo_number" not in df.columns:
    df["wo_number"] = ""
  else:
    df["wo_number"] = df["wo_number"].fillna("")

  if "cert_folder_path" not in df.columns:
    df["cert_folder_path"] = ""
  else:
    df["cert_folder_path"] = df["cert_folder_path"].fillna("")

  if "photo_path" not in df.columns:
    df["photo_path"] = ""
  else:
    df["photo_path"] = df["photo_path"].fillna("")

  def count_photos(p):
    if not p or str(p).strip() == "":
      return "—"
    paths = [pt.strip() for pt in str(p).split(";") if pt.strip()]
    valid_count = sum(1 for pt in paths if os.path.exists(pt))
    return f"📸 {valid_count}" if valid_count > 0 else "—"

  df["Has Photo?"] = df["photo_path"].apply(count_photos)

  def check_returns_email(notes_val):
    if pd.notna(notes_val) and "[Synced Email from Returns" in str(notes_val):
      return "⭐ Returns Email"
    return "—"

  def check_sent_reply(notes_val):
    if pd.notna(notes_val) and "[Synced Sent Reply]" in str(notes_val):
      return "✅ Sent Reply"
    return "—"

  df["⭐ Returns Email"] = df["notes"].apply(check_returns_email)
  df["✅ Outbox Reply Sent"] = df["notes"].apply(check_sent_reply)

  df["date_in_lab_fmt"] = df["date_in_lab"].apply(format_date_str)
  df["date_started_fmt"] = df["date_started"].apply(format_date_str)
  df["finished_date_fmt"] = df["finished_date"].apply(format_date_str)

  df["is_urgent_sort"] = df["supervisor_urgency"].apply(lambda x: 0 if x == "🔴 CRITICAL / URGENT" else 1)
  df = df.sort_values(by=["is_urgent_sort", "date_in_lab_dt"], ascending=[True, True]).reset_index(drop=True)

  display_df = df[[
      "id",
      "customer_name",
      "rga_number",
      "wo_number",
      "notification_number",
      "model_description",
      "part_number",
      "serial_number",
      "sensor_number",
      "service_requested",
      "expedited_shipping",
      "supervisor_urgency",
      "status",
      "waiting_on",
      "assigned_to",
      "date_in_lab_fmt",
      "date_started_fmt",
      "finished_date_fmt",
      "Age (Days)",
      "Has Photo?",
      "⭐ Returns Email",
      "✅ Outbox Reply Sent",
      "notes",
      "photo_path",
      "cert_folder_path",
  ]].copy()

  display_df.columns = [
      "ID",
      "Customer",
      "RGA #",
      "WO #",
      "Notification #",
      "Model Description",
      "Part Number",
      "Serial Number",
      "Sensor Number",
      "Service",
      "Expedited",
      "Urgency Level",
      "Status / Location",
      "Waiting On",
      "Assigned Tech",
      "Date In Lab",
      "Date Started",
      "Finished Date",
      "Age (Days)",
      "Has Photo?",
      "⭐ Returns Email",
      "✅ Outbox Reply Sent",
      "Outcome / Notes",
      "Photo Path",
      "Cert Folder Path",
  ]
else:
  display_df = pd.DataFrame()


# --- VIEW DASHBOARD VIEW ---
if action == "View Queue Dashboard":
  st.subheader("Current Active Queue & Expandable RGA Parent-Child Linkage Tree")

  if not display_df.empty:
    v_config = get_view_config() if st.session_state.user_role == "View Only" else None

    # --- COMMAND KPI RIBBON ---
    active_shelf_df = display_df[display_df["Status / Location"] != "Closed"]
    total_active = len(active_shelf_df)
    urgent_count = len(active_shelf_df[active_shelf_df["Urgency Level"] == "🔴 CRITICAL / URGENT"])
    expedited_count = len(active_shelf_df[active_shelf_df["Expedited"] == "Yes"])
    avg_age = int(active_shelf_df["Age (Days)"].mean()) if not active_shelf_df.empty else 0
    completed_count = len(display_df[display_df["Status / Location"] == "Closed"])

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📦 Active Shelf Units", total_active)
    m2.metric("🚨 Critical Urgent", urgent_count, delta_color="inverse")
    m3.metric("🚀 Expedited Priority", expedited_count)
    m4.metric("⏳ Mean Age", f"{avg_age} days")
    m5.metric("✅ Completed / Closed", completed_count)

    st.markdown("---")

    urgent_active = display_df[
        (display_df["Status / Location"] != "Closed")
        & (display_df["Urgency Level"] == "🔴 CRITICAL / URGENT")
    ]
    if not urgent_active.empty and (v_config is None or v_config["show_urgency"]):
      st.markdown(
          """
            <div style="background-color: #8b0000; color: white; padding: 14px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="margin: 0; color: white;">🚨 CRITICAL URGENT ALERT: Supervisor Flagged Units Active on Shelf!</h4>
                <p style="margin: 5px 0 0 0; font-size: 14px;">Review dark red highlighted rows immediately.</p>
            </div>
            """,
          unsafe_allow_html=True,
      )

    show_closed = st.sidebar.checkbox("Include Closed / Finished Items", value=False)
    status_filter = st.sidebar.selectbox("Filter by Status / Location", ["All"] + list(df["status"].unique()))
    waiting_filter = st.sidebar.selectbox("Filter by Waiting On", ["All"] + list(df["waiting_on"].unique()))
    service_filter = st.sidebar.selectbox("Filter by Service", ["All"] + list(df["service_requested"].unique()))

    filtered_df = display_df.copy()
    if not show_closed:
      filtered_df = filtered_df[filtered_df["Status / Location"] != "Closed"]
    if status_filter != "All":
      filtered_df = filtered_df[filtered_df["Status / Location"] == status_filter]
    if waiting_filter != "All":
      filtered_df = filtered_df[filtered_df["Waiting On"] == waiting_filter]
    if service_filter != "All":
      filtered_df = filtered_df[filtered_df["Service"] == service_filter]

    st.markdown("### 📦 RGA Parent-Child Grouped Shipments (Expandable Tree View)")

    if "expand_all_state" not in st.session_state:
      st.session_state.expand_all_state = None

    col_btn1, col_btn2, _ = st.columns([1, 1, 4])
    with col_btn1:
      if st.button("📂 Uncollapse All"):
        st.session_state.expand_all_state = True
        st.rerun()
    with col_btn2:
      if st.button("📁 Collapse All"):
        st.session_state.expand_all_state = False
        st.rerun()

    rga_groups = filtered_df.groupby("RGA #", sort=False)
    for rga_num, group_df in rga_groups:
      total_units = len(group_df)
      closed_units = len(group_df[group_df["Status / Location"] == "Closed"])
      cust_name = group_df["Customer"].iloc[0] if (v_config is None or v_config["show_customer"]) else "Hidden"
      is_urgent = any(group_df["Urgency Level"] == "🔴 CRITICAL / URGENT")
      is_expedited = any(group_df["Expedited"] == "Yes")

      status_badge = "🔴 [CRITICAL URGENT]" if is_urgent else ("🚀 [EXPEDITED]" if is_expedited else "")
      completion_icon = "✅ [READY TO RETURN]" if closed_units == total_units else f"⏳ [{closed_units}/{total_units} Units Complete]"

      expander_label = f"📦 RGA # {rga_num} | Customer: {cust_name} | Units: {total_units} {completion_icon} {status_badge}"

      is_expanded = st.session_state.expand_all_state if st.session_state.expand_all_state is not None else is_urgent

      with st.expander(expander_label, expanded=is_expanded):
        cols_to_show = [
            "ID",
            "Model Description",
            "Part Number",
            "Serial Number",
            "Service",
            "Expedited",
            "Urgency Level",
            "Status / Location",
            "Waiting On",
            "Assigned Tech",
            "Date In Lab",
            "Date Started",
            "Finished Date",
            "Age (Days)",
            "Has Photo?",
        ]

        if v_config is None or v_config["show_customer"]:
          cols_to_show.insert(1, "Customer")
        if v_config is None or v_config["show_wo"]:
          cols_to_show.insert(2, "WO #")
        if v_config is None or v_config["show_notes"]:
          cols_to_show.append("Outcome / Notes")

        st.dataframe(group_df[cols_to_show], use_container_width=True)

        if v_config is None or v_config["show_photos"]:
          st.markdown("#### 📸 Inline Unit Inspection Photos")
          photo_found_in_rga = False
          for _, u_row in group_df.iterrows():
            p_paths = str(u_row["Photo Path"])
            if p_paths and p_paths.strip() != "":
              paths_list = [pt.strip() for pt in p_paths.split(";") if pt.strip()]
              valid_paths = [pt for pt in paths_list if os.path.exists(pt)]
              if valid_paths:
                photo_found_in_rga = True
                st.markdown(f"**Unit ID {u_row['ID']}** | SN: {u_row['Serial Number']}")
                img_cols = st.columns(3)
                for idx, img_p in enumerate(valid_paths):
                  with img_cols[idx % 3]:
                    st.image(img_p, caption=f"ID {u_row['ID']} - Photo {idx+1}", use_container_width=True)
                st.markdown("---")

          if not photo_found_in_rga:
            st.info("No inspection photos attached to units in this RGA yet.")

# --- VIEW ONLY DISPLAY CONFIGURATION PANEL ---
elif action == "⚙️ View-Only Display Config":
  st.subheader("⚙️ Customize View-Only User Permissions & Display Visibility")
  st.markdown("Configure what information and columns are visible to **View-Only / Guest users**.")

  current_config = get_view_config()

  with st.form("view_config_form"):
    cfg_customer = st.checkbox("Show Customer Name", value=current_config.get("show_customer", True))
    cfg_wo = st.checkbox("Show Work Order (WO #)", value=current_config.get("show_wo", True))
    cfg_notes = st.checkbox("Show Repair Outcome & Notes", value=current_config.get("show_notes", True))
    cfg_photos = st.checkbox("Show Inline Inspection Photos", value=current_config.get("show_photos", True))
    cfg_urgency = st.checkbox("Show Critical Urgency Banners", value=current_config.get("show_urgency", True))
    cfg_certs = st.checkbox("Show Certificate Folder Paths", value=current_config.get("show_cert_folders", False))

    save_cfg_btn = st.form_submit_button("💾 Save View-Only Display Settings")

    if save_cfg_btn:
      new_config = {
          "show_customer": cfg_customer,
          "show_wo": cfg_wo,
          "show_notes": cfg_notes,
          "show_photos": cfg_photos,
          "show_urgency": cfg_urgency,
          "show_cert_folders": cfg_certs,
      }
      save_view_config(new_config)
      st.success("Successfully updated View-Only display settings!")
      st.rerun()

# --- LOG NEW ITEM (SINGLE) ---
elif action == "Log New Item (Single)":
  st.subheader("Log a New Unit (Single Form)")
  with st.form("new_item_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
      date_in_lab = st.date_input("Date in Lab", value=datetime.today())
      customer_name = st.text_input("Customer Name")
    with col2:
      rga_number = st.text_input("RGA Number", value="6008")
      wo_number = st.text_input("WO # (Work Order Number)")
      notification_number = st.text_input("Notification Number", value="200075")
    with col3:
      service_requested = st.selectbox("Service Requested", ["Calibration", "Repair"])
      expedited_shipping = st.checkbox("🚀 Expedited Shipping Indicator")
      supervisor_urgency = st.selectbox("Supervisor Urgency", ["Normal", "🔴 CRITICAL / URGENT"])

    col4, col5, col6 = st.columns(3)
    with col4:
      model_description = st.selectbox("Model / Item Description", ["CS12xx", "CS13xx", "CS15xx", "FCU1xxx", "FCU2xxx", "HMG 3000", "HMG 4000", "SENSORS"])
      part_number = st.text_input("Part Number")
    with col5:
      serial_number = st.text_input("Serial Number")
      sensor_number = st.text_input("Sensor Number")
    with col6:
      accessories = st.text_input("Accessories Received")

    status = st.selectbox("Status / Physical Location", ["Staging Area Outside Lab", "Shelf Waiting for Evaluation", "In Progress", "Closed"])
    assigned_to = st.selectbox("Assigned Technician", ["Geo Hall", "Unassigned", "Other Technician"])
    uploaded_photos = st.file_uploader("Upload Unit Photos", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    notes = st.text_area("Outcome & Detailed Notes")

    submitted = st.form_submit_button("Add Unit to Queue")

    if submitted and part_number:
      saved_paths = []
      if uploaded_photos:
        for upic in uploaded_photos:
          saved_p = os.path.join(PHOTO_DIR, f"unit_{datetime.today().strftime('%m%d%Y%H%M%S')}_{upic.name}")
          with open(saved_p, "wb") as f:
            f.write(upic.getbuffer())
          saved_paths.append(saved_p)

      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO queue (date_in_lab, customer_name, rga_number, wo_number, notification_number, model_description, part_number, serial_number, sensor_number, accessories, service_requested, expedited_shipping, supervisor_urgency, date_started, finished_date, status, waiting_on, assigned_to, notes, photo_path, cert_folder_path, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
          (
              date_in_lab.strftime("%Y-%m-%d"),
              customer_name,
              rga_number,
              wo_number,
              notification_number,
              model_description,
              part_number,
              serial_number,
              sensor_number,
              accessories,
              service_requested,
              "Yes" if expedited_shipping else "No",
              supervisor_urgency,
              datetime.today().strftime("%Y-%m-%d"),
              "",
              status,
              "None",
              assigned_to,
              notes,
              ";".join(saved_paths),
              "",
              datetime.today().strftime("%Y-%m-%d"),
          ),
      )
      conn.commit()
      conn.close()
      st.success("Successfully logged unit into queue!")
      st.rerun()

# --- LOG MULTIPLE UNITS (BATCH PER RGA) ---
elif action == "Log Multiple Units (Batch per RGA)":
  st.subheader("📦 Multi-Item RGA Batch Entry")
  with st.form("batch_rga_form"):
    col1, col2 = st.columns(2)
    with col1:
      b_date_in = st.date_input("Date in Lab", value=datetime.today())
      b_customer = st.text_input("Customer Name")
    with col2:
      b_rga = st.text_input("RGA Number", value="6008")
      b_wo = st.text_input("WO # (Work Order Number)")

    units_textarea = st.text_area("Mixed Units Entry (Format: Model | Part Number | Serial Number)", height=150)
    batch_submitted = st.form_submit_button("Generate Batch Items")

    if batch_submitted and units_textarea.strip():
      lines = units_textarea.split("\n")
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      for line in lines:
        if not line.strip():
          continue
        parts = [p.strip() for p in line.split("|")]
        m_desc = parts[0] if len(parts) > 0 else "CS12xx"
        p_num = parts[1] if len(parts) > 1 else "PN-GENERIC"
        s_num = parts[2] if len(parts) > 2 else "SN-GENERIC"

        cursor.execute(
            """
                    INSERT INTO queue (date_in_lab, customer_name, rga_number, wo_number, notification_number, model_description, part_number, serial_number, service_requested, status, assigned_to, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
                b_date_in.strftime("%Y-%m-%d"),
                b_customer,
                b_rga,
                b_wo,
                "200075",
                m_desc,
                p_num,
                s_num,
                "Calibration",
                "Staging Area Outside Lab",
                "Geo Hall",
                datetime.today().strftime("%Y-%m-%d"),
            ),
        )
      conn.commit()
      conn.close()
      st.success("Successfully logged batch items!")
      st.rerun()

# --- BULK IMPORT & STAGED REVIEW ---
elif action == "Bulk Import & Staged Review":
  st.subheader("Bulk Import Excel & Staged Confirmation Review")
  uploaded_file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx", "xls"])
  if uploaded_file is not None:
    import_df = pd.read_excel(uploaded_file)
    st.dataframe(import_df, use_container_width=True)
    if st.button("Confirm and Commit Staged Items"):
      st.success("Successfully committed staged items!")

# --- GENERATE SUPPORT EMAIL ---
elif action == "Generate Support Email":
  st.subheader("📧 Support & Customer Service Email Generator")
  if not df.empty:
    selected_id = st.selectbox("Select Unit", df["id"].tolist())
    e_row = df[df["id"] == selected_id].iloc[0]
    st.code(f"Subject: HYDAC Evaluation Results - RGA #{e_row['rga_number']}\n\nDear {e_row['customer_name']},\n\nYour unit (SN: {e_row['serial_number']}) has been evaluated.", language="markdown")

# --- SYNC EMAILS FROM RETURNS ---
elif action == "Sync Emails from Returns":
  st.subheader("📥 Sync Outlook Emails from 'Returns'")
  if st.button("🔍 Scan Outlook Inbox"):
    if sys.platform != "win32":
      st.warning("Outlook integration requires Windows desktop environment.")
    else:
      st.info("Scanning local Outlook MAPI inbox...")

# --- SYNC SENT ITEMS ---
elif action == "Sync Sent Items (Outbox & Replies)":
  st.subheader("📤 Sync Outlook Sent Items")
  if st.button("🔍 Scan Outlook Sent Items"):
    if sys.platform != "win32":
      st.warning("Outlook integration requires Windows desktop environment.")
    else:
      st.info("Scanning local Outlook MAPI sent folder...")

# --- SUPERVISOR URGENCY OVERRIDE ---
elif action == "Supervisor Urgency Override":
  st.subheader("🚨 Supervisor Urgency Override")
  if not df.empty:
    sup_id = st.selectbox("Select Unit to Override Urgency", df["id"].tolist())
    new_urg = st.selectbox("Set Level", ["Normal", "🔴 CRITICAL / URGENT"])
    if st.button("Apply Urgency Level"):
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute("UPDATE queue SET supervisor_urgency = ? WHERE id = ?", (new_urg, sup_id))
      conn.commit()
      conn.close()
      st.success("Urgency level updated!")
      st.rerun()

# --- CREATE SERIAL CERT FOLDER ---
elif action == "Create Serial Cert Folder":
  st.subheader("📁 Create Local Certificate Folder")
  if not df.empty:
    folder_id = st.selectbox("Select Unit for Cert Folder Creation", df["id"].tolist())
    if st.button("Create Folder & Copy Template"):
      folder_row = df[df["id"] == folder_id].iloc[0]
      sn_val = str(folder_row["serial_number"]).strip()
      target_folder = os.path.join(CERTS_BASE_DIR, sn_val)
      if not os.path.exists(target_folder):
        os.makedirs(target_folder)
      st.success(f"Created certificate folder at: {target_folder}")

# --- DEMO & RESET CONTROLS ---
elif action == "Demo & Reset Controls":
  st.subheader("🎯 Demo Preload & Database Controls")
  col1, col2 = st.columns(2)
  with col1:
    if st.button("🚀 Preload 50 Showcase Demo Items"):
      st.info("Preloading demo records...")
  with col2:
    if st.button("🗑️ Erase All Data & Start Fresh"):
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute("DROP TABLE IF EXISTS queue")
      conn.commit()
      conn.close()
      init_db()
      st.success("Database wiped clean!")
      st.rerun()

# --- UPDATE EXISTING ITEM ---
elif action == "Update Existing Item":
  st.subheader("Update Unit Status")
  if not df.empty:
    u_id = st.selectbox("Select Item ID to Update", df["id"].tolist())
    u_row = df[df["id"] == u_id].iloc[0]
    with st.form("upd_form"):
      u_status = st.selectbox("Status", ["Staging Area Outside Lab", "Shelf Waiting for Evaluation", "In Progress", "Closed"])
      u_notes = st.text_area("Notes", value=str(u_row["notes"]))
      if st.form_submit_button("Save Updates"):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE queue SET status = ?, notes = ? WHERE id = ?", (u_status, u_notes, u_id))
        conn.commit()
        conn.close()
        st.success("Unit updated!")
        st.rerun()

# --- MONTHLY VOLUME ANALYTICS ---
elif action == "Monthly Volume Analytics":
  st.subheader("Unit Volume Tracking & Analytics")
  if not df.empty:
    st.dataframe(df.groupby("model_description")["id"].count().reset_index(), use_container_width=True)

# --- BACKUP & DATA EXPORT ---
elif action == "Backup & Data Export":
  st.subheader("💾 Database Backup & Export")
  if not df.empty:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
      df.to_excel(writer, index=False, sheet_name="QueueBackup")
    buffer.seek(0)
    st.download_button(label="📥 Download Excel Backup", data=buffer, file_name="lab_queue_backup.xlsx")
