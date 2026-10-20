from datetime import datetime, timedelta
import io
import os
import pandas as pd
import random
import shutil
import sqlite3
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

# --- DATABASE SETUP WITH AUTO-HEALING ---
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
  conn.commit()
  conn.close()


init_db()


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


# --- UI CONFIGURATION & FORTUNE 100 ENTERPRISE STYLING ---
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
        
        /* Enterprise Metric Cards */
        .metric-card {
            background: #ffffff;
            border: 1px solid #e1e4e8;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            text-align: center;
        }

        @keyframes flash {
            0% { opacity: 1; }
            50% { opacity: 0.3; }
            100% { opacity: 1; }
        }
        .flashing-star {
            animation: flash 1s infinite;
            font-size: 18px;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SIDEBAR: LOGO, AUTH & NAVIGATION ---
with st.sidebar:
  try:
    st.image("logo.png", use_container_width=True)
  except Exception:
    st.info("💡 Place 'logo.png' in folder for branding.")
  st.markdown("---")

  st.header("Enterprise Access")
  if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

  if not st.session_state.authenticated:
    pwd_input = st.text_input("Enter Admin Password", type="password")
    if st.button("Unlock Admin Controls"):
      if pwd_input == "LabPass2026":
        st.session_state.authenticated = True
        st.success("Unlocked!")
        st.rerun()
      else:
        st.error("Incorrect Password")

    action = st.selectbox(
        "Select Action", ["View Queue Dashboard", "Monthly Volume Analytics"]
    )
  else:
    st.success("🔓 Admin Mode Active")
    if st.button("Lock Admin Controls"):
      st.session_state.authenticated = False
      st.rerun()

    action = st.radio(
        "Select Action",
        [
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
            "Demo & Reset Controls",
            "Monthly Volume Analytics",
            "Backup & Data Export",
        ],
    )

st.title("⚡ Enterprise Electronic Lab: Operations & Volume Command")
st.markdown(
    "Precision shelf telemetry, calibration workflows, automated RGA tracking,"
    " and cert audit readiness."
)

df = load_data()


def format_date_str(val):
  if (
      pd.isna(val)
      or not val
      or str(val).strip() == ""
      or str(val).lower() == "nan"
  ):
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
  df["Age (Days)"] = (
      datetime.today() - df["date_in_lab_dt"]
  ).dt.days.fillna(0).astype(int)

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
    if (
        pd.notna(notes_val)
        and "[Synced Email from Returns" in str(notes_val)
    ):
      return "⭐ Returns Email"
    return "—"


  def check_sent_reply(notes_val):
    if pd.notna(notes_val) and "[Synced Sent Reply]" in str(notes_val):
      return "✅ Sent Reply"
    return "—"


  df["⭐ Returns Email"] = df["notes"].apply(check_returns_email)
  df["✅ Outbox Reply Sent"] = df["notes"].apply(check_sent_reply)

  # Format date columns to MM/DD/YYYY
  df["date_in_lab_fmt"] = df["date_in_lab"].apply(format_date_str)
  df["date_started_fmt"] = df["date_started"].apply(format_date_str)
  df["finished_date_fmt"] = df["finished_date"].apply(format_date_str)

  # --- PRIORITY SORTING: Critical Urgent First, then Oldest to Newest ---
  df["is_urgent_sort"] = df["supervisor_urgency"].apply(
      lambda x: 0 if x == "🔴 CRITICAL / URGENT" else 1
  )
  df = df.sort_values(
      by=["is_urgent_sort", "date_in_lab_dt"], ascending=[True, True]
  ).reset_index(drop=True)

  display_df = df[
      [
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
      ]
  ].copy()
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


def save_item(data):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO queue (date_in_lab, customer_name, rga_number, wo_number, notification_number, model_description, part_number, serial_number, sensor_number, accessories, service_requested, expedited_shipping, supervisor_urgency, date_started, finished_date, status, waiting_on, assigned_to, notes, photo_path, cert_folder_path, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
      data,
  )
  conn.commit()
  conn.close()


def update_item_status(
    item_id,
    status,
    waiting_on,
    assigned_to,
    expedited_shipping,
    supervisor_urgency,
    date_started,
    finished_date,
    notes,
    photo_path,
    cert_folder_path,
    wo_number,
):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  today = datetime.today().strftime("%Y-%m-%d")

  if finished_date and str(finished_date).strip() != "":
    status = "Closed"

  cursor.execute(
      """
        UPDATE queue 
        SET status = ?, waiting_on = ?, assigned_to = ?, expedited_shipping = ?, supervisor_urgency = ?, date_started = ?, finished_date = ?, notes = ?, photo_path = ?, cert_folder_path = ?, wo_number = ?, last_updated = ?
        WHERE id = ?
    """,
      (
          status,
          waiting_on,
          assigned_to,
          expedited_shipping,
          supervisor_urgency,
          str(date_started),
          str(finished_date),
          notes,
          photo_path,
          cert_folder_path,
          wo_number,
          today,
          item_id,
      ),
  )
  conn.commit()
  conn.close()


# --- VIEW DASHBOARD ---
if action == "View Queue Dashboard":
  st.subheader(
      "Current Active Queue & Expandable RGA Parent-Child Linkage Tree"
  )

  if not display_df.empty:
    # --- COMMAND KPI RIBBON (EXECUTIVE OVERVIEW) ---
    active_shelf_df = display_df[display_df["Status / Location"] != "Closed"]
    total_active = len(active_shelf_df)
    urgent_count = len(
        active_shelf_df[
            active_shelf_df["Urgency Level"] == "🔴 CRITICAL / URGENT"
        ]
    )
    expedited_count = len(
        active_shelf_df[active_shelf_df["Expedited"] == "Yes"]
    )
    avg_age = (
        int(active_shelf_df["Age (Days)"].mean())
        if not active_shelf_df.empty
        else 0
    )
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
    if not urgent_active.empty:
      st.markdown(
          """
            <div style="background-color: #8b0000; color: white; padding: 14px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h4 style="margin: 0; color: white;">🚨 CRITICAL URGENT ALERT: Supervisor Flagged Units Active on Shelf!</h4>
                <p style="margin: 5px 0 0 0; font-size: 14px;">Review dark red highlighted rows immediately.</p>
            </div>
            """,
          unsafe_allow_html=True,
      )

    col1, col2, col3 = st.sidebar.columns(3)
    show_closed = st.sidebar.checkbox(
        "Include Closed / Finished Items", value=False
    )

    status_filter = st.sidebar.selectbox(
        "Filter by Status / Location", ["All"] + list(df["status"].unique())
    )
    waiting_filter = st.sidebar.selectbox(
        "Filter by Waiting On", ["All"] + list(df["waiting_on"].unique())
    )
    service_filter = st.sidebar.selectbox(
        "Filter by Service", ["All"] + list(df["service_requested"].unique())
    )
    expedited_filter = st.sidebar.selectbox(
        "Filter Expedited", ["All", "Yes", "No"]
    )
    urgency_filter = st.sidebar.selectbox(
        "Filter Urgency", ["All", "🔴 CRITICAL / URGENT", "Normal"]
    )

    filtered_df = display_df.copy()
    if not show_closed:
      filtered_df = filtered_df[filtered_df["Status / Location"] != "Closed"]
    if status_filter != "All":
      filtered_df = filtered_df[
          filtered_df["Status / Location"] == status_filter
      ]
    if waiting_filter != "All":
      filtered_df = filtered_df[filtered_df["Waiting On"] == waiting_filter]
    if service_filter != "All":
      filtered_df = filtered_df[filtered_df["Service"] == service_filter]
    if expedited_filter != "All":
      filtered_df = filtered_df[
          filtered_df["Expedited"] == expedited_filter
      ]
    if urgency_filter != "All":
      filtered_df = filtered_df[
          filtered_df["Urgency Level"] == urgency_filter
      ]

    st.markdown(
        "### 📦 RGA Parent-Child Grouped Shipments (Expandable Tree View)"
    )

    # --- COLLAPSE ALL / UNCOLLAPSE ALL COMMAND BAR ---
    if "expand_all_state" not in st.session_state:
      st.session_state.expand_all_state = None

    col_btn1, col_btn2, col_spacer = st.columns([1, 1, 4])
    with col_btn1:
      if st.button("📂 Uncollapse All"):
        st.session_state.expand_all_state = True
        st.rerun()
    with col_btn2:
      if st.button("📁 Collapse All"):
        st.session_state.expand_all_state = False
        st.rerun()

    st.markdown(
        "Each parent RGA container groups all child units. Expand any RGA to"
        " view unit details and **inline inspection photos**."
    )

    rga_groups = filtered_df.groupby("RGA #", sort=False)
    for rga_num, group_df in rga_groups:
      total_units = len(group_df)
      closed_units = len(
          group_df[group_df["Status / Location"] == "Closed"]
      )
      cust_name = group_df["Customer"].iloc[0]
      is_urgent = any(group_df["Urgency Level"] == "🔴 CRITICAL / URGENT")
      is_expedited = any(group_df["Expedited"] == "Yes")
      has_returns_email_group = any(
          group_df["⭐ Returns Email"] == "⭐ Returns Email"
      )
      has_sent_reply_group = any(group_df["✅ Outbox Reply Sent"] == "✅ Sent Reply")

      status_badge = (
          "🔴 [CRITICAL URGENT]"
          if is_urgent
          else ("🚀 [EXPEDITED]" if is_expedited else "")
      )
      email_badge = "⭐ [EMAIL ATTACHED]" if has_returns_email_group else ""
      sent_reply_badge = "✅ [REPLY SENT]" if has_sent_reply_group else ""
      completion_icon = (
          "✅ [READY TO RETURN]"
          if closed_units == total_units
          else f"⏳ [{closed_units}/{total_units} Units Complete]"
      )

      expander_label = f"📦 RGA # {rga_num} | Customer: {cust_name} | Units: {total_units} {completion_icon} {email_badge} {sent_reply_badge} {status_badge}"

      # Determine expander expanded state based on buttons or defaults
      if st.session_state.expand_all_state is not None:
        is_expanded = st.session_state.expand_all_state
      else:
        is_expanded = (
            is_urgent or has_returns_email_group or has_sent_reply_group
        )

      with st.expander(expander_label, expanded=is_expanded):
        if closed_units < total_units:
          st.warning(
              f"⚠️ Incomplete Shipment: {total_units - closed_units} unit(s)"
              " still pending in lab. All units must be completed before"
              " returning RGA shipment."
          )
        else:
          st.success(
              "🎉 All units under this RGA are fully completed and ready for"
              " customer return!"
          )


        def highlight_child_rows(row):
          if row["Status / Location"] != "Closed" and row["Urgency Level"] == (
              "🔴 CRITICAL / URGENT"
          ):
            return [
                "background-color: #8b0000; color: white; font-weight: bold;"
            ] * len(row)
          elif row["Status / Location"] != "Closed" and row["Age (Days)"] > 45:
            return ["background-color: #ffcccc; color: black;"] * len(row)
          elif row["Status / Location"] != "Closed" and row["Age (Days)"] > 30:
            return ["background-color: #fff3cd; color: black;"] * len(row)
          elif row["Status / Location"] != "Closed" and row["Expedited"] == (
              "Yes"
          ):
            return ["background-color: #ffe6e6; color: black;"] * len(row)
          return [""] * len(row)


        cols_to_show = [
            "ID",
            "Customer",
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
        ]

        st.dataframe(
            group_df[cols_to_show].style.apply(
                highlight_child_rows, axis=1
            ),
            use_container_width=True,
        )

        st.markdown("#### 📸 Inline Unit Inspection Photos for this RGA")
        photo_found_in_rga = False
        for _, u_row in group_df.iterrows():
          p_paths = str(u_row["Photo Path"])
          if p_paths and p_paths.strip() != "":
            paths_list = [
                pt.strip() for pt in p_paths.split(";") if pt.strip()
            ]
            valid_paths = [pt for pt in paths_list if os.path.exists(pt)]
            if valid_paths:
              photo_found_in_rga = True
              st.markdown(
                  f"**Unit ID {u_row['ID']}** | Model: {u_row['Model Description']} | SN: {u_row['Serial Number']} | WO: {u_row['WO #']}"
              )
              # Render uniform responsive columns for evenly sized photos
              img_cols = st.columns(3)
              for idx, img_p in enumerate(valid_paths):
                with img_cols[idx % 3]:
                  st.image(
                      img_p,
                      caption=f"ID {u_row['ID']} - Photo {idx+1}",
                      use_container_width=True,
                  )
              st.markdown("---")

        if not photo_found_in_rga:
          st.info("No inspection photos attached to units in this RGA yet.")

    st.markdown("---")
    st.markdown("### 📁 Generated Certificate Folders")
    for _, row in filtered_df.iterrows():
      cf_path = row["Cert Folder Path"]
      if cf_path and os.path.exists(cf_path):
        st.text(f"ID {row['ID']} (SN: {row['Serial Number']}) -> {cf_path}")

    st.caption(
        "🎨 **Color Key**: Dark Red = Supervisor Urgent | Red (>45 Days) |"
        " Yellow (>30 Days) | Pink = Expedited"
    )
  else:
    st.info(
        "No items currently logged in the queue. Go to Admin -> Demo & Reset"
        " Controls to preload demo data."
    )

# --- LOG NEW ITEM (SINGLE) ---
elif action == "Log New Item (Single)":
  st.subheader("Log a New Unit (Single Form)")

  with st.form("new_item_form"):
    st.markdown("### 1️⃣ Tracking & Identifiers")
    col1, col2, col3 = st.columns(3)
    with col1:
      date_in_lab = st.date_input("Date in Lab", value=datetime.today())
      customer_name = st.text_input("Customer Name")
    with col2:
      rga_number = st.text_input(
          "RGA Number (8 digits, starts with 6008)", value="6008"
      )
      wo_number = st.text_input("WO # (Work Order Number)")
      notification_number = st.text_input(
          "Notification Number (8 digits, starts with 200075)", value="200075"
      )
    with col3:
      service_requested = st.selectbox(
          "Service Requested", ["Calibration", "Repair"]
      )
      expedited_shipping = st.checkbox("🚀 Expedited Shipping Indicator")
      supervisor_urgency = st.selectbox(
          "Supervisor Urgency", ["Normal", "🔴 CRITICAL / URGENT"]
      )

    st.markdown("### 2️⃣ Equipment Specifications")
    col4, col5, col6 = st.columns(3)
    with col4:
      model_options_list = [
          "CS12xx",
          "CS13xx",
          "CS15xx",
          "FCU1xxx",
          "FCU2xxx",
          "HMG 3000",
          "HMG 4000",
          "SENSORS",
          "Pressure Transmitter",
          "Flow Sensor",
          "Pressure Switch",
          "Temperature Sensor",
          "Contamination Sensor",
      ]
      model_description = st.selectbox(
          "Model / Item Type Description", model_options_list
      )
      part_number = st.text_input("Part Number")
    with col5:
      serial_number = st.text_input(
          "Serial Number", value="000sS01831K"
      )
      sensor_number = st.text_input("Sensor Number")
    with col6:
      accessories = st.text_input(
          "Accessories Received", placeholder="e.g., cables, power supply..."
      )

    st.markdown("### 3️⃣ Shelf Location / Status, Tech & Multiple Photo Uploads")
    col7, col8, col9 = st.columns(3)
    with col7:
      status = st.selectbox(
          "Status / Physical Location",
          [
              "Staging Area Outside Lab",
              "Shelf Waiting for Evaluation",
              "Shelf Waiting for Customer Response",
              "In Progress",
              "Closed",
          ],
      )
      waiting_on = st.selectbox(
          "Waiting On / Hold Reason",
          [
              "None",
              "Awaiting Customer Response",
              "Issue Found with Unit",
              "Waiting on Replacement Parts/Third Party",
          ],
      )
    with col8:
      assigned_to = st.selectbox(
          "Assigned Technician", ["Geo Hall", "Unassigned", "Other Technician"]
      )
      date_started = st.date_input("Date Started", value=datetime.today())
    with col9:
      finished_date_input = st.date_input("Finished Date (Optional)", value=None)

    uploaded_photos = st.file_uploader(
        "Upload Multiple Unit Photos",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    notes = st.text_area(
        "Outcome & Detailed Notes",
        placeholder="Enter initial diagnostics, customer comments, or part requirements...",
    )

    submitted = st.form_submit_button("Add Unit to Queue")

    if submitted and part_number:
      saved_paths = []
      if uploaded_photos:
        for upic in uploaded_photos:
          saved_p = os.path.join(
              PHOTO_DIR,
              f"unit_{datetime.today().strftime('%m%d%Y%H%M%S')}_{upic.name}",
          )
          with open(saved_p, "wb") as f:
            f.write(upic.getbuffer())
          saved_paths.append(saved_p)

      photo_path_str = ";".join(saved_paths) if saved_paths else ""
      date_in_str = date_in_lab.strftime("%Y-%m-%d")
      date_start_str = date_started.strftime("%Y-%m-%d")
      fin_str = (
          finished_date_input.strftime("%Y-%m-%d")
          if finished_date_input
          else ""
      )
      today_str = datetime.today().strftime("%Y-%m-%d")
      exp_val = "Yes" if expedited_shipping else "No"

      save_item((
          date_in_str,
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
          exp_val,
          supervisor_urgency,
          date_start_str,
          fin_str,
          status,
          waiting_on,
          assigned_to,
          notes,
          photo_path_str,
          "",
          today_str,
      ))
      st.success(f"Successfully logged Part # {part_number}!")
      st.rerun()

# --- LOG MULTIPLE UNITS (BATCH PER RGA WITH DIFFERENT DEVICES) ---
elif action == "Log Multiple Units (Batch per RGA)":
  st.subheader("📦 Multi-Item RGA Batch Entry (Different Models & Devices)")
  st.markdown(
      "Enter the shared RGA, WO, and customer info once, then add multiple"
      " unit rows with their own **Model, Part Number, and Serial Number**."
  )

  with st.form("batch_rga_form"):
    st.markdown("### 1️⃣ Shared RGA & Customer Header")
    col1, col2, col3 = st.columns(3)
    with col1:
      b_date_in = st.date_input("Date in Lab", value=datetime.today())
      b_customer = st.text_input("Customer Name")
    with col2:
      b_rga = st.text_input(
          "RGA Number (8 digits, starts with 6008)", value="6008"
      )
      b_wo = st.text_input("WO # (Work Order Number)")
      b_notif = st.text_input(
          "Notification Number (8 digits, starts with 200075)", value="200075"
      )
    with col3:
      b_service = st.selectbox(
          "Service Requested", ["Calibration", "Repair"], key="b_srv"
      )
      b_urgency = st.selectbox(
          "Supervisor Urgency", ["Normal", "🔴 CRITICAL / URGENT"], key="b_urg"
      )
      b_exp = st.checkbox("🚀 Expedited Shipping Indicator", key="b_ex")

    st.markdown(
        "### 2️⃣ Units List (Format: `Model | Part Number | Serial Number` per"
        " line)"
    )
    units_textarea = st.text_area(
        "Mixed Units Entry",
        placeholder=(
            "CS12xx | PN-101 | SN-A001\nHMG 4000 | PN-400 | SN-B992\nSENSORS |"
            " PN-500 | SN-C883"
        ),
        height=150,
    )

    b_tech = st.selectbox(
        "Assigned Technician",
        ["Geo Hall", "Unassigned", "Other Technician"],
        key="b_tch",
    )
    b_notes = st.text_area(
        "Batch Notes / Reason for Return",
        placeholder="e.g. Mixed shipment of various contamination and data loggers...",
        key="b_nts",
    )

    batch_submitted = st.form_submit_button(
        "🚀 Generate and Save All Mixed Units under this RGA"
    )

    if batch_submitted and units_textarea.strip():
      lines = units_textarea.split("\n")
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      today_str = datetime.today().strftime("%Y-%m-%d")
      d_in_str = b_date_in.strftime("%Y-%m-%d")
      exp_val = "Yes" if b_exp else "No"

      created_count = 0
      for line in lines:
        if not line.strip():
          continue
        parts = (
            [p.strip() for p in line.split("|")]
            if "|" in line
            else [p.strip() for p in line.split(",")]
        )

        if len(parts) >= 3:
          m_desc = parts[0]
          p_num = parts[1]
          s_num = parts[2]
        elif len(parts) == 2:
          m_desc = parts[0]
          p_num = "GENERAL-PN"
          s_num = parts[1]
        else:
          m_desc = "CS12xx"
          p_num = "GENERAL-PN"
          s_num = parts[0]

        cursor.execute(
            """
                    INSERT INTO queue (
                        date_in_lab, customer_name, rga_number, wo_number, notification_number, 
                        model_description, part_number, serial_number, sensor_number, 
                        accessories, service_requested, expedited_shipping, supervisor_urgency, 
                        date_started, finished_date, status, waiting_on, assigned_to, notes, photo_path, cert_folder_path, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
                d_in_str,
                b_customer,
                b_rga,
                b_wo,
                b_notif,
                m_desc,
                p_num,
                s_num,
                "",
                "None",
                b_service,
                exp_val,
                b_urgency,
                d_in_str,
                "",
                "Staging Area Outside Lab",
                "None",
                b_tech,
                b_notes,
                "",
                "",
                today_str,
            ),
        )
        created_count += 1

      conn.commit()
      conn.close()
      st.success(
          f"Successfully created {created_count} mixed device records under RGA"
          f" {b_rga}!"
      )
      st.rerun()

# --- BULK IMPORT & STAGED REVIEW ---
elif action == "Bulk Import & Staged Review":
  st.subheader("Bulk Import Excel & Staged Confirmation Review")
  uploaded_file = st.file_uploader(
      "Upload Excel File (.xlsx)", type=["xlsx", "xls"]
  )

  if uploaded_file is not None:
    try:
      import_df = pd.read_excel(uploaded_file)
      st.markdown("### 📋 Step 1: Preview Uploaded Data")
      st.dataframe(import_df, use_container_width=True)

      st.markdown("### ✅ Step 2: Confirm Items Before Adding to Database")
      if st.button("Confirm and Commit Staged Items to Database"):
        today_str = datetime.today().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        imported_count = 0
        for _, row in import_df.iterrows():
          cursor.execute(
              """
                        INSERT INTO queue (date_in_lab, customer_name, rga_number, wo_number, notification_number, model_description, part_number, serial_number, sensor_number, accessories, service_requested, expedited_shipping, supervisor_urgency, date_started, finished_date, status, waiting_on, assigned_to, notes, photo_path, cert_folder_path, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
              (
                  str(row.get("date_in_lab", today_str)),
                  str(row.get("customer_name", "")),
                  str(row.get("rga_number", "")),
                  str(row.get("wo_number", "")),
                  str(row.get("notification_number", "")),
                  str(row.get("model_description", "")),
                  str(row.get("part_number", "")),
                  str(row.get("serial_number", "")),
                  str(row.get("sensor_number", "")),
                  str(row.get("accessories", "")),
                  str(row.get("service_requested", "Calibration")),
                  str(row.get("expedited_shipping", "No")),
                  str(row.get("supervisor_urgency", "Normal")),
                  str(row.get("date_started", today_str)),
                  str(row.get("finished_date", "")),
                  str(row.get("status", "Staging Area Outside Lab")),
                  str(row.get("waiting_on", "None")),
                  str(row.get("assigned_to", "Geo Hall")),
                  str(row.get("notes", "")),
                  "",
                  "",
                  today_str,
              ),
          )
          imported_count += 1

        conn.commit()
        conn.close()
        st.success(
            f"Successfully committed {imported_count} items from staged"
            " review into the queue!"
        )
        st.rerun()
    except Exception as e:
      st.error(f"Error reading file: {e}")

# --- GENERATE SUPPORT EMAIL (FOR CUSTOMER SERVICE / SUPPORT) ---
elif action == "Generate Support Email":
  st.subheader("📧 Support & Customer Service Email Generator")
  st.markdown(
      "Select a unit below to generate a clean email template for **Customer"
      " Service / Support**. It includes all unit details so Support can"
      " review, edit, forward, or reword it when reaching out to the"
      " customer."
  )

  if not df.empty:
    email_options = {}
    for index, row in df.iterrows():
      label_str = f"ID {row['id']} - Customer: {row['customer_name']} | RGA: {row['rga_number']} | WO: {row['wo_number']} | {row['model_description']} (SN: {row['serial_number']})"
      email_options[label_str] = row["id"]

    selected_email_label = st.selectbox(
        "Select Unit for Email Generation", list(email_options.keys())
    )
    selected_email_id = email_options[selected_email_label]
    e_row = df[df["id"] == selected_email_id].iloc[0]

    email_type = st.radio(
        "Select Email Scenario for Support",
        [
            (
                "🔴 Failed Calibration: Ask Customer if Unit should be Returned"
                " or Scrapped"
            ),
            (
                "🛠️ Parts Replacement Needed: Request Evaluation Report & PO"
                " Approval"
            ),
        ],
    )

    cust_name = (
        e_row["customer_name"]
        if pd.notna(e_row["customer_name"]) and e_row["customer_name"]
        else "[Customer Name]"
    )
    rga_val = (
        e_row["rga_number"]
        if pd.notna(e_row["rga_number"]) and e_row["rga_number"]
        else "N/A"
    )
    wo_val = (
        e_row["wo_number"]
        if pd.notna(e_row["wo_number"]) and e_row["wo_number"]
        else "N/A"
    )
    notif_val = (
        e_row["notification_number"]
        if pd.notna(e_row["notification_number"])
        and e_row["notification_number"]
        else "N/A"
    )
    model_val = (
        e_row["model_description"]
        if pd.notna(e_row["model_description"])
        and e_row["model_description"]
        else "N/A"
    )
    pn_val = (
        e_row["part_number"]
        if pd.notna(e_row["part_number"]) and e_row["part_number"]
        else "N/A"
    )
    sn_val = (
        e_row["serial_number"]
        if pd.notna(e_row["serial_number"]) and e_row["serial_number"]
        else "N/A"
    )
    notes_val = (
        e_row["notes"]
        if pd.notna(e_row["notes"]) and e_row["notes"]
        else "Unit evaluated in lab."
    )

    if "Failed Calibration" in email_type:
      email_subject = (
          f"HYDAC Lab Evaluation / Calibration Results - RGA #{rga_val}"
          f" / WO #{wo_val} (SN: {sn_val})"
      )
      email_body = f"""Hi Support / Customer Service Team,

Please use or adapt the draft below to reach out to the customer ({cust_name}) regarding their unit failing calibration testing.

---
**Customer Name:** {cust_name}
**RGA Number:** {rga_val}
**Work Order (WO) #:** {wo_val}
**Notification #:** {notif_val}
**Model Description:** {model_val}
**Part Number:** {pn_val}
**Serial Number:** {sn_val}
**Lab Findings / Notes:** {notes_val}
---

**Email Draft for Customer:**
"Dear {cust_name},

We have completed the evaluation and calibration testing for your unit in our lab. Unfortunately, the unit referenced above failed to meet calibration specifications or standard operational limits.

Please let us know how you would like to proceed:
1. **Return Unit As-Is / Unrepaired** (Shipping charges may apply)
2. **Scrap Unit Locally** (HYDAC will recycle/dispose of the unit here)

Please reply at your earliest convenience with your decision so we can process your shipment.

Best regards,
HYDAC Customer Service"
"""
    else:
      email_subject = (
          f"HYDAC Lab Evaluation Report & PO Request - RGA #{rga_val} / WO"
          f" #{wo_val} (SN: {sn_val})"
      )
      email_body = f"""Hi Support / Customer Service Team,

Please use or adapt the draft below to reach out to the customer ({cust_name}) to provide the evaluation report and request a Purchase Order (PO) for replacement parts.

---
**Customer Name:** {cust_name}
**RGA Number:** {rga_val}
**Work Order (WO) #:** {wo_val}
**Notification #:** {notif_val}
**Model Description:** {model_val}
**Part Number:** {pn_val}
**Serial Number:** {sn_val}
**Lab Findings & Repair Notes:** {notes_val}
---

**Email Draft for Customer:**
"Dear {cust_name},

Our technicians have evaluated your unit in the lab. Based on our diagnostics, replacement parts and repair work are required to restore the unit to full working order. 

Please find our evaluation report attached. **To proceed with the repairs, we kindly request that you review the evaluation and provide an official Purchase Order (PO).**

Please reply with your Purchase Order (PO) or let us know if you have any questions.

Best regards,
HYDAC Customer Service"
"""

    st.markdown("---")
    st.markdown("### 📋 Email Content & One-Click Copy")
    st.text_input("Subject Line", value=email_subject)

    st.markdown(
        "Click the **Copy icon (📋)** in the top right corner of the box below"
        " to instantly copy the entire email to your clipboard!"
    )
    st.code(email_body, language="markdown")
  else:
    st.info("No items available in queue.")

# --- SYNC EMAILS FROM RETURNS ---
elif action == "Sync Emails from Returns":
  st.subheader(
      "📥 Sync Outlook Emails from 'Returns' & Staged Review"
  )
  st.markdown(
      "Scan your Outlook inbox for emails from **Returns**, match them against"
      " active RGA or Notification numbers, and **review them in a staging table**"
      " before applying them to unit notes."
  )

  if "staged_returns_emails" not in st.session_state:
    st.session_state.staged_returns_emails = []

  col_sync1, col_sync2 = st.columns(2)
  with col_sync1:
    if st.button("🔍 1. Scan Outlook Inbox & Stage Matches"):
      try:
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace(
            "MAPI"
        )
        inbox = outlook.GetDefaultFolder(6)
        messages = inbox.Items
        messages.Sort("[ReceivedTime]", True)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, rga_number, notification_number, customer_name, notes"
            " FROM queue"
        )
        rows = cursor.fetchall()
        conn.close()

        staged_list = []
        scan_count = 0

        for message in messages:
          if scan_count > 150:
            break
          try:
            sender = getattr(message, "SenderName", "")
            subject = getattr(message, "Subject", "")
            body = getattr(message, "Body", "")
            received_time = str(getattr(message, "ReceivedTime", ""))

            if (
                "return" in sender.lower()
                or "return" in subject.lower()
                or "returns" in subject.lower()
            ):
              for db_id, rga, notif, cust, existing_notes in rows:
                rga_str = str(rga).strip()
                notif_str = str(notif).strip()

                if (
                    rga_str
                    and rga_str != "nan"
                    and rga_str != ""
                    and rga_str in subject
                ) or (
                    notif_str
                    and notif_str != "nan"
                    and notif_str != ""
                    and notif_str in subject
                ):
                  email_snippet = f"\n\n[Synced Email from Returns - {received_time}]\nSubject: {subject}\n{body[:1200]}"
                  if not any(
                      item["db_id"] == db_id
                      and item["subject"] == subject
                      for item in staged_list
                  ):
                    if email_snippet not in str(existing_notes or ""):
                      staged_list.append({
                          "db_id": db_id,
                          "customer": cust,
                          "rga": rga_str,
                          "notification": notif_str,
                          "sender": sender,
                          "subject": subject,
                          "received": received_time,
                          "body_snippet": email_snippet,
                      })
            scan_count += 1
          except Exception:
            continue

        st.session_state.staged_returns_emails = staged_list
        st.success(
            f"Scan complete! Found {len(staged_list)} matching email(s) ready"
            " for review below."
        )
        st.rerun()
      except Exception as e:
        st.error(
            "Could not connect to Outlook via win32com. Make sure pywin32 is"
            " installed (`pip install pywin32`) and Outlook is running."
            f" Error: {e}"
        )

  if st.session_state.staged_returns_emails:
    st.markdown("### 📋 Step 2: Review Pulled Emails Before Applying")
    st.markdown(
        "Review the matched emails below. Uncheck any you do not wish to"
        " apply, then click **Commit Approved Emails to Database Notes**."
    )

    with st.form("review_staged_form"):
      approved_indices = []
      for idx, item in enumerate(st.session_state.staged_returns_emails):
        st.markdown(
            f"**Match #{idx+1}** | Customer: **{item['customer']}** | RGA:"
            f" **{item['rga']}** | Notif: **{item['notification']}**"
        )
        st.text(f"Subject: {item['subject']} (Received: {item['received']})")
        st.text_area(
            f"Email Preview (ID {item['db_id']})",
            value=item["body_snippet"],
            height=120,
            key=f"preview_{idx}",
            disabled=True,
        )
        is_selected = st.checkbox(
            f"Approve and attach Match #{idx+1} to Database",
            value=True,
            key=f"chk_{idx}",
        )
        if is_selected:
          approved_indices.append(idx)
        st.markdown("---")

      commit_button = st.form_submit_button(
          "🚀 Commit Approved Emails to Database Notes"
      )

      if commit_button:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        applied_count = 0

        for idx in approved_indices:
          item = st.session_state.staged_returns_emails[idx]
          db_id = item["db_id"]
          snippet = item["body_snippet"]

          cursor.execute("SELECT notes FROM queue WHERE id = ?", (db_id,))
          res = cursor.fetchone()
          if res:
            current_notes = res[0] or ""
            if snippet not in current_notes:
              updated_notes = current_notes + snippet
              cursor.execute(
                  "UPDATE queue SET notes = ? WHERE id = ?",
                  (updated_notes, db_id),
              )
              conn.commit()
              applied_count += 1

        conn.close()
        st.session_state.staged_returns_emails = []
        st.success(
            f"Successfully applied {applied_count} approved email(s) to unit"
            " notes!"
        )
        st.rerun()
  else:
    st.info(
        "No emails staged yet. Click 'Scan Outlook Inbox & Stage Matches' above"
        " to check for new messages."
    )

# --- SYNC SENT ITEMS (OUTBOX & REPLIES) ---
elif action == "Sync Sent Items (Outbox & Replies)":
  st.subheader(
      "📤 Sync Outlook Sent Items (Outbox) & Staged Review"
  )
  st.markdown(
      "Scan your Outlook **Sent Items** folder for sent replies or messages"
      " matching active RGA or Notification numbers, and review them in a"
      " staging table before adding the green check reply confirmation to"
      " unit notes."
  )

  if "staged_sent_emails" not in st.session_state:
    st.session_state.staged_sent_emails = []

  col_sent1, col_sent2 = st.columns(2)
  with col_sent1:
    if st.button("🔍 1. Scan Outlook Sent Items & Stage Matches"):
      try:
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace(
            "MAPI"
        )
        sent_folder = outlook.GetDefaultFolder(
            5
        )  # 5 corresponds to Sent Items folder
        messages = sent_folder.Items
        messages.Sort("[SentOn]", True)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, rga_number, notification_number, customer_name, notes"
            " FROM queue"
        )
        rows = cursor.fetchall()
        conn.close()

        staged_list = []
        scan_count = 0

        for message in messages:
          if scan_count > 150:
            break
          try:
            subject = getattr(message, "Subject", "")
            body = getattr(message, "Body", "")
            sent_time = str(getattr(message, "SentOn", ""))
            to_recipient = getattr(message, "To", "")

            for db_id, rga, notif, cust, existing_notes in rows:
              rga_str = str(rga).strip()
              notif_str = str(notif).strip()

              if (
                  rga_str
                  and rga_str != "nan"
                  and rga_str != ""
                  and rga_str in subject
              ) or (
                  notif_str
                  and notif_str != "nan"
                  and notif_str != ""
                  and notif_str in subject
              ):
                email_snippet = f"\n\n[Synced Sent Reply - {sent_time}]\nTo: {to_recipient}\nSubject: {subject}\n{body[:1200]}"
                if not any(
                    item["db_id"] == db_id
                    and item["subject"] == subject
                    for item in staged_list
                ):
                  if "[Synced Sent Reply]" not in str(existing_notes or ""):
                    staged_list.append({
                        "db_id": db_id,
                        "customer": cust,
                        "rga": rga_str,
                        "notification": notif_str,
                        "to": to_recipient,
                        "subject": subject,
                        "sent": sent_time,
                        "body_snippet": email_snippet,
                    })
            scan_count += 1
          except Exception:
            continue

        st.session_state.staged_sent_emails = staged_list
        st.success(
            f"Scan complete! Found {len(staged_list)} matching sent reply(s)"
            " ready for review below."
        )
        st.rerun()
      except Exception as e:
        st.error(
            "Could not connect to Outlook via win32com. Make sure pywin32 is"
            " installed (`pip install pywin32`) and Outlook is running."
            f" Error: {e}"
        )

  if st.session_state.staged_sent_emails:
    st.markdown("### 📋 Step 2: Review Sent Replies Before Applying")
    st.markdown(
        "Review the matched sent messages below. Uncheck any you do not wish to"
        " apply, then click **Commit Approved Sent Replies to Database**."
    )

    with st.form("review_staged_sent_form"):
      approved_sent_indices = []
      for idx, item in enumerate(st.session_state.staged_sent_emails):
        st.markdown(
            f"**Match #{idx+1}** | Customer: **{item['customer']}** | RGA:"
            f" **{item['rga']}** | Notif: **{item['notification']}**"
        )
        st.text(
            f"To: {item['to']} | Subject: {item['subject']} (Sent:"
            f" {item['sent']})"
        )
        st.text_area(
            f"Sent Reply Preview (ID {item['db_id']})",
            value=item["body_snippet"],
            height=120,
            key=f"preview_sent_{idx}",
            disabled=True,
        )
        is_selected_sent = st.checkbox(
            f"Approve and attach sent reply Match #{idx+1} to Database",
            value=True,
            key=f"chk_sent_{idx}",
        )
        if is_selected_sent:
          approved_sent_indices.append(idx)
        st.markdown("---")

      commit_sent_button = st.form_submit_button(
          "🚀 Commit Approved Sent Replies to Database"
      )

      if commit_sent_button:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        applied_count = 0

        for idx in approved_sent_indices:
          item = st.session_state.staged_sent_emails[idx]
          db_id = item["db_id"]
          snippet = item["body_snippet"]

          cursor.execute("SELECT notes FROM queue WHERE id = ?", (db_id,))
          res = cursor.fetchone()
          if res:
            current_notes = res[0] or ""
            if "[Synced Sent Reply]" not in current_notes:
              updated_notes = current_notes + snippet
              cursor.execute(
                  "UPDATE queue SET notes = ? WHERE id = ?",
                  (updated_notes, db_id),
              )
              conn.commit()
              applied_count += 1

        conn.close()
        st.session_state.staged_sent_emails = []
        st.success(
            f"Successfully applied {applied_count} approved sent reply(s) to"
            " unit notes!"
        )
        st.rerun()
  else:
    st.info(
        "No sent items staged yet. Click 'Scan Outlook Sent Items & Stage"
        " Matches' above to check for sent replies."
    )

# --- SUPERVISOR URGENCY OVERRIDE ---
elif action == "Supervisor Urgency Override":
  st.subheader(
      "🚨 Supervisor Urgency Override (Instant Dashboard Flagging)"
  )

  if not df.empty:
    sup_options = {}
    for index, row in df.iterrows():
      label_str = f"ID {row['id']} - RGA: {row['rga_number']} | WO: {row['wo_number']} | {row['model_description']} (SN: {row['serial_number']}) [Current: {row['supervisor_urgency']}]"
      sup_options[label_str] = row["id"]

    selected_sup_label = st.selectbox(
        "Select Item for Emergency Urgency Bump", list(sup_options.keys())
    )
    selected_sup_id = sup_options[selected_sup_label]
    sup_current_row = df[df["id"] == selected_sup_id].iloc[0]

    with st.form("supervisor_urgency_form"):
      new_urgency = st.selectbox(
          "Set Supervisor Urgency Level",
          ["Normal", "🔴 CRITICAL / URGENT"],
          index=1
          if sup_current_row["supervisor_urgency"] == "🔴 CRITICAL / URGENT"
          else 0,
      )
      sup_notes_add = st.text_area(
          "Supervisor Call / Message Note",
          placeholder="e.g., Customer called supervisor directly requesting expedited turnaround...",
      )

      sup_submitted = st.form_submit_button(
          "🚨 Apply Emergency Urgency Override"
      )

      if sup_submitted:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        updated_notes = (
            str(sup_current_row["notes"])
            + f"\n[Supervisor Urgent Flag: {datetime.today().strftime('%m/%d/%Y')}] {sup_notes_add}"
        )
        cursor.execute(
            """
                    UPDATE queue 
                    SET supervisor_urgency = ?, notes = ?
                    WHERE id = ?
                """,
            (new_urgency, updated_notes, selected_sup_id),
        )
        conn.commit()
        conn.close()
        st.success("Urgency level successfully updated!")
        st.rerun()
  else:
    st.info("No items available in queue.")

# --- CREATE SERIAL CERT FOLDER ---
elif action == "Create Serial Cert Folder":
  st.subheader("📁 Create Local Certificate Folder & Pull from FORMS")
  st.markdown(
      "Select an item below to automatically create a folder named after its"
      " Serial Number (`SN`) under:"
      f" `{CERTS_BASE_DIR}` and copy the matching calibration report template"
      f" from `{FORMS_DIR}` renamed as **[SN]_CERT**."
  )

  if not df.empty:
    folder_options = {}
    for index, row in df.iterrows():
      label_str = f"ID {row['id']} - {row['model_description']} (SN: {row['serial_number']})"
      folder_options[label_str] = row["id"]

    selected_folder_label = st.selectbox(
        "Select Item to Create Cert Folder & Save SN_CERT",
        list(folder_options.keys()),
    )
    selected_folder_id = folder_options[selected_folder_label]
    folder_row = df[df["id"] == selected_folder_id].iloc[0]

    sn_value = str(folder_row["serial_number"]).strip()
    model_desc = str(folder_row["model_description"]).strip().upper()

    if st.button(
        "📁 Create Cert Folder & Pull Template from FORMS as SN_CERT"
    ):
      if not sn_value or sn_value.lower() == "nan" or sn_value == "":
        st.error(
            "This item does not have a valid Serial Number specified. Please"
            " update the unit's serial number first."
        )
      else:
        target_folder = os.path.join(CERTS_BASE_DIR, sn_value)
        try:
          if not os.path.exists(target_folder):
            os.makedirs(target_folder)

          template_filename = None
          if any(
              m in model_desc for m in ["CS12", "CS13", "CS15", "FCU1"]
          ):
            template_filename = (
                "F-0353 FCU & CS12_13_15xx CALIBRATION CERTIFICATE.docx"
            )
          elif any(m in model_desc for m in ["CS2", "FCU2"]):
            template_filename = "F-0354 FCU_CS2xxx CALIBRATION CERTIFICATE.docx"
          elif "HMG 4000" in model_desc:
            template_filename = (
                "F-0257 HMG 4000 CALIBRATION REPORT TEMPLATE.docm"
            )
          elif "HMG 3000" in model_desc:
            template_filename = "F-0242 HMG 30X0 CALIBRATION REPORT.docm"
          else:
            template_filename = (
                "F-0353 FCU & CS12_13_15xx CALIBRATION CERTIFICATE.docx"
            )

          src_template_path = os.path.join(FORMS_DIR, template_filename)
          copied_cert_path = ""
          ext = ".docx"

          if os.path.exists(src_template_path):
            ext = os.path.splitext(template_filename)[1]
            dest_filename = f"{sn_value}_CERT{ext}"
            copied_cert_path = os.path.join(target_folder, dest_filename)
            shutil.copy(src_template_path, copied_cert_path)
          else:
            st.warning(
                f"Template file '{template_filename}' not found in FORMS"
                f" directory ({FORMS_DIR}). Created empty cert folder."
            )

          conn = sqlite3.connect(DB_FILE)
          cursor = conn.cursor()
          cursor.execute(
              "UPDATE queue SET cert_folder_path = ? WHERE id = ?",
              (target_folder, selected_folder_id),
          )
          conn.commit()
          conn.close()

          st.success(
              f"Successfully created folder and saved cert as"
              f" '{sn_value}_CERT{ext}' at: {target_folder}"
          )
          st.rerun()
        except Exception as e:
          st.error(f"Failed to create directory or copy cert: {e}")
  else:
    st.info("No items available in queue.")

# --- DEMO & RESET CONTROLS ---
elif action == "Demo & Reset Controls":
  st.subheader("🎯 Boss Showcase Demo & Database Reset Controls")
  col_demo1, col_demo2 = st.columns(2)

  with col_demo1:
    if st.button("🚀 Preload 50 Showcase Demo Items"):
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute("DROP TABLE IF EXISTS queue")
      conn.commit()
      init_db()

      # Gather available demo photos from DEMO PHOTOS folder
      available_demo_photos = []
      if os.path.exists(DEMO_PHOTOS_DIR):
        valid_exts = (".png", ".jpg", ".jpeg")
        available_demo_photos = [
            os.path.join(DEMO_PHOTOS_DIR, f)
            for f in os.listdir(DEMO_PHOTOS_DIR)
            if f.lower().endswith(valid_exts)
        ]

      demo_items = []
      base_d = datetime(2026, 5, 1)
      model_list_demo = [
          "CS12xx",
          "CS13xx",
          "CS15xx",
          "FCU1xxx",
          "FCU2xxx",
          "HMG 3000",
          "HMG 4000",
          "SENSORS",
          "Pressure Transmitter",
          "Flow Sensor",
      ]
      customer_list_demo = [
          "Acme Industrial Corp",
          "Global Hydraulics",
          "Apex Dynamics",
          "Vanguard Fluid Power",
          "Summit Tech Systems",
          "Pioneer Automation",
      ]
      status_list_demo = [
          "Staging Area Outside Lab",
          "Shelf Waiting for Evaluation",
          "Shelf Waiting for Customer Response",
          "In Progress",
          "Closed",
      ]
      waiting_list_demo = [
          "None",
          "Awaiting Customer Response",
          "Issue Found with Unit",
          "Waiting on Replacement Parts/Third Party",
      ]

      for i in range(1, 51):
        d_in = base_d + timedelta(days=(i % 45))
        rga = f"6008{3000 + (i // 4)}"
        wo = f"WO-{9000 + i}"
        notif = f"200075{i:02d}"
        sn = f"000sS01831K{i:07d}"
        exp = "Yes" if i % 5 == 0 else "No"
        urg = "🔴 CRITICAL / URGENT" if i in [3, 14, 27, 42] else "Normal"
        status_val = status_list_demo[i % len(status_list_demo)]
        fin_date = (
            (d_in + timedelta(days=3)).strftime("%Y-%m-%d")
            if status_val == "Closed"
            else ""
        )
        chosen_model = model_list_demo[i % len(model_list_demo)]
        chosen_cust = customer_list_demo[i % len(customer_list_demo)]
        chosen_wait = waiting_list_demo[i % len(waiting_list_demo)]

        # Embed Returns Email and Sent Reply notes in some demo items
        sample_notes = f"Demo item {i} record note."
        if i % 4 == 0:
          sample_notes += f"\n\n[Synced Email from Returns - 10/18/2026 14:30]\nSubject: RGA #{rga} Status Inquiry from Customer\nPlease expedite evaluation."
        if i % 6 == 0:
          sample_notes += f"\n\n[Synced Sent Reply - 10/19/2026 09:15]\nTo: returns@hydac.com\nSubject: RE: RGA #{rga} / Notif #{notif}\nUnit evaluated and calibration report generated."

        cert_path = (
            os.path.join(CERTS_BASE_DIR, sn) if i % 3 == 0 else ""
        )

        # Randomly assign 1 to 3 photos from DEMO PHOTOS folder if available
        assigned_photo_paths = ""
        if available_demo_photos:
          num_photos_to_pick = random.randint(1, min(3, len(available_demo_photos)))
          picked_photos = random.sample(available_demo_photos, num_photos_to_pick)
          assigned_photo_paths = ";".join(picked_photos)

        demo_items.append((
            d_in.strftime("%Y-%m-%d"),
            chosen_cust,
            rga,
            wo,
            notif,
            chosen_model,
            f"PN-{200+i}",
            sn,
            f"SEN-{900+i}",
            "Power supply & cables" if i % 2 == 0 else "None",
            "Calibration" if i % 3 != 0 else "Repair",
            exp,
            urg,
            (d_in + timedelta(days=1)).strftime("%Y-%m-%d"),
            fin_date,
            status_val,
            chosen_wait,
            "Geo Hall" if i % 2 == 0 else "Unassigned",
            sample_notes,
            assigned_photo_paths,
            cert_path,
            d_in.strftime("%Y-%m-%d"),
        ))

      cursor.executemany(
          """
            INSERT INTO queue (
                date_in_lab, customer_name, rga_number, wo_number, notification_number, 
                model_description, part_number, serial_number, sensor_number, 
                accessories, service_requested, expedited_shipping, supervisor_urgency, 
                date_started, finished_date, status, waiting_on, assigned_to, notes, photo_path, cert_folder_path, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
          demo_items,
      )
      conn.commit()
      conn.close()
      st.success(
          "Successfully preloaded 50 rich showcase demo items with random"
          " DEMO PHOTOS, email badges, urgency flags, and cert folders!"
      )
      st.rerun()

  with col_demo2:
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
  st.subheader("Update Status, Enter Outcome, or Close Request")

  if not df.empty:
    item_options = {}
    for index, row in df.iterrows():
      label_str = f"ID {row['id']} - RGA: {row['rga_number']} | WO: {row['wo_number']} | {row['model_description']} (SN: {row['serial_number']})"
      item_options[label_str] = row["id"]

    selected_label = st.selectbox(
        "Select Item to Update", list(item_options.keys())
    )
    selected_id = item_options[selected_label]

    current_row = df[df["id"] == selected_id].iloc[0]

    with st.form("update_form"):
      col1, col2 = st.columns(2)
      with col1:
        new_wo = st.text_input(
            "WO # (Work Order Number)",
            value=str(current_row["wo_number"])
            if pd.notna(current_row["wo_number"])
            else "",
        )
        status_choices = [
            "Staging Area Outside Lab",
            "Shelf Waiting for Evaluation",
            "Shelf Waiting for Customer Response",
            "In Progress",
            "Closed",
        ]
        curr_status = (
            current_row["status"]
            if current_row["status"] in status_choices
            else "Staging Area Outside Lab"
        )
        new_status = st.selectbox(
            "Status / Physical Location",
            status_choices,
            index=status_choices.index(curr_status),
        )
        new_waiting_on = st.selectbox(
            "Waiting On / Hold Reason",
            [
                "None",
                "Awaiting Customer Response",
                "Issue Found with Unit",
                "Waiting on Replacement Parts/Third Party",
            ],
            index=[
                "None",
                "Awaiting Customer Response",
                "Issue Found with Unit",
                "Waiting on Replacement Parts/Third Party",
            ].index(current_row["waiting_on"])
            if current_row["waiting_on"]
            in [
                "None",
                "Awaiting Customer Response",
                "Issue Found with Unit",
                "Waiting on Replacement Parts/Third Party",
            ]
            else 0,
        )
        is_expedited_default = (
            True
            if pd.notna(current_row["expedited_shipping"])
            and current_row["expedited_shipping"] == "Yes"
            else False
        )
        new_expedited = st.checkbox(
            "🚀 Expedited Shipping Indicator", value=is_expedited_default
        )
        current_urgency_idx = (
            1
            if pd.notna(current_row["supervisor_urgency"])
            and current_row["supervisor_urgency"] == "🔴 CRITICAL / URGENT"
            else 0
        )
        new_supervisor_urgency = st.selectbox(
            "Supervisor Urgency",
            ["Normal", "🔴 CRITICAL / URGENT"],
            index=current_urgency_idx,
        )

      with col2:
        current_assignee = (
            current_row["assigned_to"]
            if pd.notna(current_row["assigned_to"])
            else "Geo Hall"
        )
        assignee_options = ["Geo Hall", "Unassigned", "Other Technician"]
        assignee_idx = (
            assignee_options.index(current_assignee)
            if current_assignee in assignee_options
            else 0
        )
        new_assigned_to = st.selectbox(
            "Assigned Technician", assignee_options, index=assignee_idx
        )

        try:
          default_started = datetime.strptime(
              str(current_row["date_started"]), "%Y-%m-%d"
          ).date()
        except Exception:
          default_started = datetime.today().date()

        new_date_started = st.date_input(
            "Date Started", value=default_started
        )

        current_fin_val = current_row["finished_date"]
        default_fin = None
        if pd.notna(current_fin_val) and str(current_fin_val).strip() != "":
          try:
            default_fin = datetime.strptime(
                str(current_fin_val), "%m/%d/%Y"
            ).date()
          except Exception:
            try:
              default_fin = datetime.strptime(
                  str(current_fin_val), "%Y-%m-%d"
              ).date()
            except Exception:
              pass

        new_finished_date_input = st.date_input(
            "Finished Date (Entering this closes the request)",
            value=default_fin,
        )

      new_photos = st.file_uploader(
          "Add Additional Photos",
          type=["png", "jpg", "jpeg"],
          accept_multiple_files=True,
      )
      new_notes = st.text_area(
          "Outcome & Repair Notes", value=str(current_row["notes"])
      )

      update_submitted = st.form_submit_button("Save Updates & Close")

      if update_submitted:
        existing_photos = str(current_row["photo_path"])
        saved_paths = (
            [p.strip() for p in existing_photos.split(";") if p.strip()]
            if existing_photos
            else []
        )

        if new_photos:
          for npic in new_photos:
            saved_p = os.path.join(
                PHOTO_DIR,
                f"unit_{datetime.today().strftime('%m%d%Y%H%M%S')}_{npic.name}",
            )
            with open(saved_p, "wb") as f:
              f.write(npic.getbuffer())
            saved_paths.append(saved_p)

        photo_path_str = ";".join(saved_paths) if saved_paths else ""
        exp_val = "Yes" if new_expedited else "No"
        fin_date_str = (
            new_finished_date_input.strftime("%Y-%m-%d")
            if new_finished_date_input
            else ""
        )
        update_item_status(
            selected_id,
            new_status,
            new_waiting_on,
            new_assigned_to,
            exp_val,
            new_supervisor_urgency,
            new_date_started.strftime("%Y-%m-%d"),
            fin_date_str,
            new_notes,
            photo_path_str,
            current_row["cert_folder_path"],
            new_wo,
        )
        st.success("Item updated successfully!")
        st.rerun()
  else:
    st.info("No items available to update.")

# --- MONTHLY VOLUME ANALYTICS ---
elif action == "Monthly Volume Analytics":
  st.subheader("Unit Volume Tracking & Analytics")

  if not df.empty:
    df["date_in_lab_dt"] = pd.to_datetime(df["date_in_lab"], errors="coerce")
    df["Month"] = df["date_in_lab_dt"].dt.to_period("M").astype(str)

    st.markdown("### 📊 Monthly Handled Units by Part Number")
    monthly_pivot = (
        df.pivot_table(
            index="part_number",
            columns="Month",
            values="id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
        .rename(columns={"part_number": "Part Number"})
    )

    monthly_pivot["Total Cumulative"] = df.groupby("part_number")[
        "id"
    ].count().values
    st.dataframe(monthly_pivot, use_container_width=True)

    st.markdown("### 📈 Breakdown by Service Requested")
    service_summary = (
        df.groupby(["Month", "service_requested"])["id"].count().reset_index()
    )
    service_summary.columns = ["Month", "Service", "Count"]
    st.dataframe(service_summary, use_container_width=True)
  else:
    st.info("No data available for volume tracking yet.")

# --- BACKUP & DATA EXPORT ---
elif action == "Backup & Data Export":
  st.subheader("💾 Database Backup & Export")
  if not df.empty:
    output_filename = (
        f"lab_queue_backup_{datetime.today().strftime('%m%d%Y')}.xlsx"
    )
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
      df.to_excel(writer, index=False, sheet_name="QueueBackup")
    buffer.seek(0)

    st.download_button(
        label="📥 Download Full Excel Backup",
        data=buffer,
        file_name=output_filename,
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
  else:
    st.info("No records available to back up yet.")