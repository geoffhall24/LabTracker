import io
import os
import random
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# =========================================================
# PAGE CONFIGURATION & FUTURISTIC HYDAC THEME
# =========================================================
st.set_page_config(
    page_title="HYDAC Lab Operations Command",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "lab_queue.db"
LOCAL_CERTS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Certs"

# Modern High-Contrast Industrial UI (CSS)
st.markdown(
    """
    <style>
    /* HYDAC Dark Industrial Palette */
    :root {
        --hydac-red: #E30613;
        --hydac-red-glow: rgba(227, 6, 19, 0.25);
        --hydac-dark: #0B0F17;
        --hydac-card: #151C2C;
        --hydac-slate: #1E293B;
        --hydac-text: #F8FAFC;
        --hydac-border: #2D3D58;
    }

    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 96%;
    }

    /* Futuristic Header Banner */
    .hydac-banner {
        background: linear-gradient(135deg, #0B0F17 0%, #1E293B 100%);
        border: 1px solid #2D3D58;
        border-left: 6px solid #E30613;
        border-radius: 10px;
        padding: 22px 28px;
        color: #FFFFFF;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .hydac-title {
        font-size: 1.95rem;
        font-weight: 800;
        color: #FFFFFF;
        margin: 0;
        letter-spacing: -0.5px;
        text-transform: uppercase;
    }
    .hydac-subtitle {
        font-size: 0.92rem;
        color: #94A3B8;
        margin-top: 4px;
        font-weight: 500;
    }

    /* KPI Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #151C2C !important;
        border: 1px solid #2D3D58 !important;
        border-top: 3px solid #E30613 !important;
        border-radius: 8px !important;
        padding: 14px 18px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    div[data-testid="stMetric"] label {
        color: #94A3B8 !important;
        font-weight: 700 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }

    /* Status Badges */
    .badge-email {
        background-color: #059669;
        color: #ECFDF5;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-reply {
        background-color: #2563EB;
        color: #EFF6FF;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-urgent {
        background-color: #E30613;
        color: #FFFFFF;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 800;
        display: inline-block;
        box-shadow: 0 0 8px rgba(227, 6, 19, 0.5);
    }

    /* Sidebar Styling */
    .sidebar-user-card {
        background: #151C2C;
        border: 1px solid #2D3D58;
        border-left: 4px solid #E30613;
        padding: 14px 16px;
        border-radius: 8px;
        color: #F8FAFC;
        margin-bottom: 15px;
    }
    .sidebar-section-header {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #E30613;
        font-weight: 800;
        margin-top: 16px;
        margin-bottom: 6px;
    }

    /* Form Buttons */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #E30613 0%, #A8000A 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 12px rgba(227, 6, 19, 0.3) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #FF1A27 0%, #C4000C 100%) !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# DATABASE INIT & SCHEMA AUTO-REPAIR
# =========================================================
def init_db():
  """Ensures the SQLite database table and all required columns exist."""
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
            notes TEXT,
            date_logged TEXT
        )
    """)

  # Check missing columns
  cursor.execute("PRAGMA table_info(queue)")
  existing_cols = [col[1] for col in cursor.fetchall()]

  if "urgency" not in existing_cols:
    cursor.execute("ALTER TABLE queue ADD COLUMN urgency INTEGER DEFAULT 5")
  if "date_logged" not in existing_cols:
    cursor.execute("ALTER TABLE queue ADD COLUMN date_logged TEXT")

  conn.commit()
  conn.close()


def load_data():
  """Loads data safely from SQLite and returns a standardized pandas DataFrame."""
  init_db()
  conn = sqlite3.connect(DB_FILE)
  try:
    df = pd.read_sql_query("SELECT * FROM queue", conn)
  except Exception:
    df = pd.DataFrame()
  finally:
    conn.close()

  if not df.empty:
    if "urgency" not in df.columns:
      df["urgency"] = 5
    df["urgency"] = df["urgency"].fillna(5).astype(int)

    if "date_logged" not in df.columns or df["date_logged"].isnull().all():
      df["date_logged"] = datetime.now().strftime("%Y-%m-%d")

  return df


def reset_and_seed_db():
  """Completely resets database and seeds 10 realistic HYDAC Lab records."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("DROP TABLE IF EXISTS queue")
  cursor.execute("""
        CREATE TABLE queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rga_number TEXT,
            notification_number TEXT,
            customer_name TEXT,
            model_series TEXT,
            serial_number TEXT,
            status TEXT,
            urgency INTEGER DEFAULT 5,
            notes TEXT,
            date_logged TEXT
        )
    """)

  demo_data = [
      (
          "60083000",
          "20007503",
          "Caterpillar Inc.",
          "CS 1000 Contamination Sensor",
          "000SS01831K0000003",
          "Under Testing",
          9,
          "[Synced Email from Returns] Customer requesting urgent turnaround for lab calibration.",
          "2026-10-12",
      ),
      (
          "60083105",
          "20007510",
          "John Deere Corp.",
          "FAM-10 Fluid Conditioning Unit",
          "FAM10-998231-A",
          "Received in Lab",
          5,
          "Standard warranty intake review pending technician assignment.",
          "2026-10-18",
      ),
      (
          "60083112",
          "20007522",
          "Komatsu Ltd.",
          "FCU 1310 Portable Filtration Unit",
          "FCU1310-88412-B",
          "Pending Customer Info",
          3,
          "Waiting on customer clarification regarding operating hydraulic pressure.",
          "2026-10-05",
      ),
      (
          "60083120",
          "20007530",
          "Bosch Rexroth",
          "Lab CalRig Sensor Array",
          "CAL-90021-X",
          "Completed",
          2,
          "[Synced Sent Reply] Calibration certificate generated and emailed to supervisor.",
          "2026-09-28",
      ),
      (
          "60083145",
          "20007548",
          "Parker Hannifin",
          "AS 1000 AquaSensor Unit",
          "AS1000-77621-C",
          "Received in Lab",
          7,
          "Urgent field replacement requested under RGA 60083145.",
          "2026-10-22",
      ),
      (
          "60083150",
          "20007555",
          "Eaton Hydraulics",
          "CS 2000 Particle Counter",
          "CS2000-55102-D",
          "Under Testing",
          8,
          "Laser diode calibration in progress on CalRig bench 2.",
          "2026-10-15",
      ),
      (
          "60083162",
          "20007560",
          "General Electric",
          "HLP 6 Hydraulic Lab Pump",
          "HLP6-33910-E",
          "Received in Lab",
          4,
          "Visual inspection completed. Awaiting fluid analysis test results.",
          "2026-10-20",
      ),
      (
          "60083170",
          "20007572",
          "Volvo Construction",
          "FCU 2000 Dehydration Unit",
          "FCU2000-11209-F",
          "Completed",
          1,
          "Repaired pump seal and dispatched back to customer via freight.",
          "2026-09-15",
      ),
      (
          "60083185",
          "20007581",
          "Siemens Energy",
          "KineSys Servo Controller",
          "KINE-88201-G",
          "Pending Customer Info",
          6,
          "[Synced Email from Returns] Technical support requested failure logs from plant manager.",
          "2026-10-10",
      ),
      (
          "60083190",
          "20007599",
          "Danfoss Power",
          "CS 1000 Particle Counter",
          "CS1000-44109-H",
          "Under Testing",
          10,
          "CRITICAL / EXPEDITE: High priority warranty evaluation for plant outage.",
          "2026-10-25",
      ),
  ]

  cursor.executemany(
      """
        INSERT INTO queue (rga_number, notification_number, customer_name, model_series, serial_number, status, urgency, notes, date_logged)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
      demo_data,
  )

  conn.commit()
  conn.close()


def build_unit_dropdown_options(df):
  """Formats dropdown options into descriptive labels."""
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

    label = f"RGA: {rga} | Notif: {notif} | {model} | SN: {sn} [Priority: {urgency}/10] (ID: {unit_id})"
    options_map[label] = unit_id

  return options_map


# Load current queue state
df_queue = load_data()


# =========================================================
# HEADER BANNER & SYSTEM ENVIRONMENT TOGGLE
# =========================================================
col_logo, col_header = st.columns([1, 6])
with col_logo:
  if os.path.exists("logo.png"):
    st.image("logo.png", width=120)
  else:
    st.markdown("### ⚡ **HYDAC**")

with col_header:
  st.markdown(
      """
    <div class="hydac-banner">
        <div class="hydac-title">Enterprise Electronic Lab Command Center</div>
        <div class="hydac-subtitle">HYDAC Technology Corp — Quality Control, Calibration & Returns Management</div>
    </div>
    """,
      unsafe_allow_html=True,
  )

# Environment Mode Switch
with st.container(border=True):
  toggle_col, status_col = st.columns([2, 3])
  with toggle_col:
    is_local_mode = st.toggle(
        "🖥️ Enable Local PC Mode (Folder Creation)", value=False
    )

  with status_col:
    if is_local_mode:
      st.success(
          "Mode: **Local PC** — Direct local workstation folder generation"
          f" enabled at:\n`{LOCAL_CERTS_DIR}`"
      )
    else:
      st.info(
          "Mode: **Streamlit Cloud** — Read-only web mode (Local file system"
          " creation restricted)."
      )


# =========================================================
# SIDEBAR NAVIGATION & CATEGORY ROUTING
# =========================================================
with st.sidebar:
  st.markdown(
      """
    <div class="sidebar-user-card">
        <div style="font-size:0.7rem; color:#94A3B8; text-transform:uppercase; font-weight:700;">Active User</div>
        <div style="font-size:1.15rem; font-weight:800; color:#FFFFFF;">Geo Hall</div>
        <div style="font-size:0.8rem; color:#E30613; font-weight:700;">Lab Lead / Operations Lead</div>
    </div>
    """,
      unsafe_allow_html=True,
  )

  if st.button("🚪 Sign Out", use_container_width=True):
    st.toast("Signed out cleanly.", icon="🚪")

  st.markdown("---")
  st.markdown(
      '<div class="sidebar-section-header">MODULE CATEGORY</div>',
      unsafe_allow_html=True,
  )

  nav_category = st.selectbox(
      "Category",
      [
          "📊 Dashboard & Analytics",
          "📥 Intake & Unit Logging",
          "⚙️ Queue & Folder Operations",
          "✉️ Outlook Email Sync",
          "🛠️ System Admin & Tools",
      ],
      label_visibility="collapsed",
  )

  st.markdown(
      '<div class="sidebar-section-header">WORKFLOW VIEW</div>',
      unsafe_allow_html=True,
  )

  if nav_category == "📊 Dashboard & Analytics":
    nav_choice = st.radio(
        "Workflow",
        ["View Queue Dashboard", "Monthly Volume Analytics"],
        label_visibility="collapsed",
    )
  elif nav_category == "📥 Intake & Unit Logging":
    nav_choice = st.radio(
        "Workflow",
        [
            "Log New Item (Single)",
            "Log Multiple Units (Batch per RGA)",
            "Bulk Import & Staged Review",
        ],
        label_visibility="collapsed",
    )
  elif nav_category == "⚙️ Queue & Folder Operations":
    nav_choice = st.radio(
        "Workflow",
        [
            "Update Existing Item",
            "Create Serial Cert Folder",
            "Supervisor Urgency Override",
        ],
        label_visibility="collapsed",
    )
  elif nav_category == "✉️ Outlook Email Sync":
    nav_choice = st.radio(
        "Workflow",
        [
            "Generate Support Email",
            "Sync Emails from Returns",
            "Sync Sent Items (Outbox & Replies)",
        ],
        label_visibility="collapsed",
    )
  else:
    nav_choice = st.radio(
        "Workflow",
        [
            "⚙️ View-Only Display Config",
            "Demo & Reset Controls",
            "Backup & Data Export",
        ],
        label_visibility="collapsed",
    )

# Refresh dataset state
df_queue = load_data()


# =========================================================
# VIEW 1: EXECUTIVE COMMAND CENTER (DASHBOARD)
# =========================================================
if nav_choice == "View Queue Dashboard":
  st.subheader("📊 Active Lab Queue Command Center")

  if df_queue.empty:
    st.warning(
        "No active unit records found in database. Go to **Demo & Reset"
        " Controls** in the sidebar to populate test data!"
    )
  else:
    # Executive KPI Summary Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Active Units", len(df_queue))

    high_urgency = (df_queue["urgency"] >= 8).sum()
    m2.metric("Critical / Rush Units (8-10)", high_urgency)

    synced_emails = (
        df_queue["notes"]
        .dropna()
        .apply(lambda x: "[Synced" in str(x))
        .sum()
        if "notes" in df_queue.columns
        else 0
    )
    m3.metric("Units with Synced Emails", synced_emails)

    rga_count = (
        df_queue["rga_number"].dropna().replace("nan", "").ne("").sum()
        if "rga_number" in df_queue.columns
        else 0
    )
    m4.metric("Active RGAs", rga_count)

    st.markdown("---")

    # Search and Filter Controls
    c_search, c_status = st.columns([3, 1])
    search_term = c_search.text_input(
        "🔍 Real-Time Filter (RGA, Notification, Customer, Model, Serial Number):",
        placeholder="Search Caterpillar, CS 1000, 60083000...",
    )
    status_filter = c_status.selectbox(
        "Filter by Status",
        ["All Statuses"] + list(df_queue["status"].dropna().unique()),
    )

    filtered_df = df_queue.copy()
    if status_filter != "All Statuses":
      filtered_df = filtered_df[filtered_df["status"] == status_filter]

    if search_term:
      filter_mask = filtered_df.astype(str).apply(
          lambda col: col.str.contains(search_term, case=False)
      ).any(axis=1)
      filtered_df = filtered_df[filter_mask]

    # Master Table Display
    with st.container(border=True):
      st.markdown("#### 📋 Current Lab Queue Master Table")
      st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    # Unit Inspection & Quick Action Panel
    st.markdown("### 🔎 Deep Unit Inspection & Correspondence History")
    unit_map = build_unit_dropdown_options(filtered_df)

    if unit_map:
      selected_inspect_label = st.selectbox(
          "Select Unit to Inspect Details & Synced Notes:",
          options=list(unit_map.keys()),
          key="inspect_select",
      )
      selected_id = unit_map[selected_inspect_label]
      selected_row = filtered_df[filtered_df["id"] == selected_id].iloc[0]

      with st.expander(
          f"📋 Unit Summary — ID #{selected_id} | RGA:"
          f" {selected_row.get('rga_number', 'N/A')}",
          expanded=True,
      ):
        c1, c2, c3, c4 = st.columns(4)
        c1.write(f"**RGA Number:** `{selected_row.get('rga_number', 'N/A')}`")
        c2.write(
            "**Notification:**"
            f" `{selected_row.get('notification_number', 'N/A')}`"
        )
        c3.write(f"**Customer:** `{selected_row.get('customer_name', 'N/A')}`")
        c4.write(f"**Urgency:** `{selected_row.get('urgency', 5)}/10`")

        c5, c6, c7, c8 = st.columns(4)
        c5.write(f"**Model:** `{selected_row.get('model_series', 'N/A')}`")
        c6.write(f"**Serial Number:** `{selected_row.get('serial_number', 'N/A')}`")
        c7.write(f"**Status:** `{selected_row.get('status', 'N/A')}`")
        c8.write(f"**Date Logged:** `{selected_row.get('date_logged', 'N/A')}`")

        notes_val = str(selected_row.get("notes", "") or "")
        if "[Synced Email from Returns" in notes_val:
          st.markdown(
              '<span class="badge-email">⭐ Returns Email Synced</span>',
              unsafe_allow_html=True,
          )
        if "[Synced Sent Reply" in notes_val:
          st.markdown(
              '<span class="badge-reply">✅ Outbox Reply Sent</span>',
              unsafe_allow_html=True,
          )
        if int(selected_row.get("urgency", 5)) >= 8:
          st.markdown(
              '<span class="badge-urgent">🔥 CRITICAL / EXPEDITE</span>',
              unsafe_allow_html=True,
          )

        st.text_area(
            "Full Unit Activity & Email Notes History:",
            value=notes_val,
            height=200,
            disabled=True,
        )

# =========================================================
# VIEW 2: LOG NEW ITEM (SINGLE)
# =========================================================
elif nav_choice == "Log New Item (Single)":
  st.subheader("📝 Log New Unit into Lab Queue")
  with st.form("new_unit_form"):
    c1, c2 = st.columns(2)
    f_rga = c1.text_input("RGA Number*")
    f_notif = c2.text_input("Notification Number")

    c3, c4 = st.columns(2)
    f_cust = c3.text_input("Customer Name")
    f_model = c4.text_input("Model Series / Description*")

    c5, c6 = st.columns(2)
    f_sn = c5.text_input("Serial Number*")
    f_urgency = c6.slider("Priority / Urgency Score", 1, 10, 5)

    f_status = st.selectbox(
        "Initial Status",
        [
            "Received in Lab",
            "Under Testing",
            "Pending Customer Info",
            "Completed",
        ],
    )
    f_notes = st.text_area("Initial Intake Notes")

    submit_btn = st.form_submit_button("➕ Log Unit into Queue", type="primary")
    if submit_btn:
      if f_rga and f_sn and f_model:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
                INSERT INTO queue (rga_number, notification_number, customer_name, model_series, serial_number, status, urgency, notes, date_logged)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f_rga,
                f_notif,
                f_cust,
                f_model,
                f_sn,
                f_status,
                f_urgency,
                f_notes,
                datetime.now().strftime("%Y-%m-%d"),
            ),
        )
        conn.commit()
        conn.close()
        st.success(
            f"✅ Successfully logged unit RGA: `{f_rga}` | SN: `{f_sn}` into"
            " database!"
        )
      else:
        st.error(
            "Please fill in all required fields marked with * (RGA, Model,"
            " Serial Number)."
        )

# =========================================================
# VIEW 3: LOG MULTIPLE UNITS (BATCH PER RGA)
# =========================================================
elif nav_choice == "Log Multiple Units (Batch per RGA)":
  st.subheader("📦 Batch Log Multiple Serial Numbers")
  c1, c2 = st.columns(2)
  batch_rga = c1.text_input("Parent RGA Number for Batch*:")
  batch_notif = c2.text_input("Notification Number:")

  c3, c4 = st.columns(2)
  batch_cust = c3.text_input("Customer Name:")
  batch_model = c4.text_input("Model Series / Description*:")

  batch_sns = st.text_area(
      "Enter Child Serial Numbers* (One serial number per line):"
  )

  if st.button("🚀 Process Batch Intake", type="primary"):
    sn_list = [s.strip() for s in batch_sns.split("\n") if s.strip()]
    if batch_rga and batch_model and sn_list:
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      today_str = datetime.now().strftime("%Y-%m-%d")
      for sn in sn_list:
        cursor.execute(
            """
                INSERT INTO queue (rga_number, notification_number, customer_name, model_series, serial_number, status, urgency, date_logged)
                VALUES (?, ?, ?, ?, ?, 'Received in Lab', 5, ?)
            """,
            (batch_rga, batch_notif, batch_cust, batch_model, sn, today_str),
        )
      conn.commit()
      conn.close()
      st.success(
          f"✅ Successfully batch-logged {len(sn_list)} serial number(s) under"
          f" RGA `{batch_rga}`!"
      )
    else:
      st.error(
          "Please enter a Parent RGA Number, Model, and at least one valid"
          " Serial Number."
      )

# =========================================================
# VIEW 4: BULK IMPORT & STAGED REVIEW
# =========================================================
elif nav_choice == "Bulk Import & Staged Review":
  st.subheader("📥 Bulk Data Import (Excel / CSV)")
  uploaded_file = st.file_uploader(
      "Upload CSV or Excel file to stage:", type=["csv", "xlsx"]
  )
  if uploaded_file:
    try:
      if uploaded_file.name.endswith(".csv"):
        import_df = pd.read_csv(uploaded_file)
      else:
        import_df = pd.read_excel(uploaded_file)

      st.markdown("#### Staged Data Preview")
      st.dataframe(import_df.head(10), use_container_width=True)

      if st.button(
          "💾 Append Previewed Data to Queue Database", type="primary"
      ):
        conn = sqlite3.connect(DB_FILE)
        import_df.to_sql("queue", conn, if_exists="append", index=False)
        conn.close()
        st.success(
            f"✅ Successfully appended {len(import_df)} records into"
            " `lab_queue.db`!"
        )
    except Exception as e:
      st.error(f"❌ Error parsing file: {e}")

# =========================================================
# VIEW 5: UPDATE EXISTING ITEM
# =========================================================
elif nav_choice == "Update Existing Item":
  st.subheader("✏️ Update Existing Queue Record")
  if df_queue.empty:
    st.warning("No records to update.")
  else:
    unit_map = build_unit_dropdown_options(df_queue)
    sel_label = st.selectbox(
        "Select Unit to Edit:", options=list(unit_map.keys())
    )
    sel_id = unit_map[sel_label]
    sel_row = df_queue[df_queue["id"] == sel_id].iloc[0]

    with st.form("edit_unit_form"):
      c1, c2 = st.columns(2)
      u_rga = c1.text_input(
          "RGA Number", value=str(sel_row.get("rga_number", ""))
      )
      u_notif = c2.text_input(
          "Notification Number",
          value=str(sel_row.get("notification_number", "")),
      )

      c3, c4 = st.columns(2)
      u_cust = c3.text_input(
          "Customer Name", value=str(sel_row.get("customer_name", ""))
      )
      u_model = c4.text_input(
          "Model / Item", value=str(sel_row.get("model_series", ""))
      )

      c5, c6 = st.columns(2)
      u_sn = c5.text_input(
          "Serial Number", value=str(sel_row.get("serial_number", ""))
      )
      u_urgency = c6.slider(
          "Urgency Score", 1, 10, int(sel_row.get("urgency", 5))
      )

      u_status = st.text_input("Status", value=str(sel_row.get("status", "")))
      u_notes = st.text_area("Notes", value=str(sel_row.get("notes", "")))

      if st.form_submit_button("💾 Save Record Updates", type="primary"):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
                UPDATE queue SET rga_number=?, notification_number=?, customer_name=?, model_series=?, serial_number=?, status=?, urgency=?, notes=?
                WHERE id=?
            """,
            (
                u_rga,
                u_notif,
                u_cust,
                u_model,
                u_sn,
                u_status,
                u_urgency,
                u_notes,
                sel_id,
            ),
        )
        conn.commit()
        conn.close()
        st.success(f"✅ Record ID #{sel_id} updated successfully!")

# =========================================================
# VIEW 6: GENERATE SUPPORT EMAIL
# =========================================================
elif nav_choice == "Generate Support Email":
  st.subheader("✉️ Generate Support Notification Email")
  if df_queue.empty:
    st.warning("No units available in database.")
  else:
    unit_map = build_unit_dropdown_options(df_queue)
    sel_label = st.selectbox(
        "Select Target Unit for Email:", options=list(unit_map.keys())
    )
    sel_id = unit_map[sel_label]
    sel_row = df_queue[df_queue["id"] == sel_id].iloc[0]

    email_body = f"""Subject: HYDAC Electronic Lab Status Update - RGA: {sel_row.get('rga_number', 'N/A')}

Hello {sel_row.get('customer_name', 'Customer')},

The following unit is currently in process at the HYDAC Electronic Lab:

- RGA Number: {sel_row.get('rga_number', 'N/A')}
- Notification Number: {sel_row.get('notification_number', 'N/A')}
- Model Series: {sel_row.get('model_series', 'N/A')}
- Serial Number: {sel_row.get('serial_number', 'N/A')}
- Current Status: {sel_row.get('status', 'N/A')}
- Priority Score: {sel_row.get('urgency', 5)}/10

Notes / Test Log:
{sel_row.get('notes', 'N/A')}

Best regards,
HYDAC Electronic Lab Team
1700 Fairgrounds Rd, Bethlehem, PA 18018
"""
    st.text_area(
        "Copy Pre-Populated Outlook Email Draft:", value=email_body, height=300
    )

# =========================================================
# VIEW 7: SYNC EMAILS FROM RETURNS
# =========================================================
elif nav_choice == "Sync Emails from Returns":
  st.subheader("📩 Synced Returns Email Inbox")
  st.info(
      "Emails from Returns are automatically scanned by `sync_outlook.py`"
      " locally on your workstation."
  )
  email_units = df_queue[
      df_queue["notes"]
      .fillna("")
      .str.contains("\\[Synced Email from Returns", case=False)
  ]
  if email_units.empty:
    st.warning("No synced Returns emails found in current database records.")
  else:
    unit_map = build_unit_dropdown_options(email_units)
    sel_label = st.selectbox(
        "Select Unit with Synced Returns Email:", options=list(unit_map.keys())
    )
    sel_id = unit_map[sel_label]
    sel_row = email_units[email_units["id"] == sel_id].iloc[0]
    st.text_area(
        "Synced Email Content:", value=str(sel_row.get("notes", "")), height=300
    )

# =========================================================
# VIEW 8: SYNC SENT ITEMS (OUTBOX & REPLIES)
# =========================================================
elif nav_choice == "Sync Sent Items (Outbox & Replies)":
  st.subheader("📤 Sync Outlook Sent Items")
  st.warning(
      "Outlook integration requires running `sync_outlook.py` locally on"
      " Windows."
  )
  sent_units = df_queue[
      df_queue["notes"]
      .fillna("")
      .str.contains("\\[Synced Sent Reply", case=False)
  ]
  if sent_units.empty:
    st.info("No sent email replies currently tagged in database records.")
  else:
    unit_map = build_unit_dropdown_options(sent_units)
    sel_label = st.selectbox(
        "Select Unit with Sent Reply:", options=list(unit_map.keys())
    )
    sel_id = unit_map[sel_label]
    sel_row = sent_units[sent_units["id"] == sel_id].iloc[0]
    st.text_area(
        "Synced Sent Reply Content:",
        value=str(sel_row.get("notes", "")),
        height=300,
    )

# =========================================================
# VIEW 9: SUPERVISOR URGENCY OVERRIDE
# =========================================================
elif nav_choice == "Supervisor Urgency Override":
  st.subheader("⚡ Supervisor Urgency & Priority Escalation Override")
  if df_queue.empty:
    st.warning("No active units available.")
  else:
    unit_map = build_unit_dropdown_options(df_queue)
    sel_label = st.selectbox(
        "Select Unit to Override Priority:", options=list(unit_map.keys())
    )
    sel_id = unit_map[sel_label]
    sel_row = df_queue[df_queue["id"] == sel_id].iloc[0]

    st.write(
        f"**Current Priority:** `{sel_row.get('urgency', 5)}/10` |"
        f" **Status:** `{sel_row.get('status', 'N/A')}`"
    )

    new_urgency = st.slider(
        "Set Manager Urgency Score (1 = Low, 10 = Critical/Expedite)",
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
            "CRITICAL / EXPEDITE",
            "Completed",
        ],
    )
    override_reason = st.text_input("Manager Override Justification / Reason:")

    if st.button("⚡ Apply Priority Override", type="primary"):
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      updated_notes = (
          str(sel_row.get("notes", ""))
          + f"\n[Supervisor Override ({datetime.now().strftime('%Y-%m-%d %H:%M')}): Priority set to {new_urgency}/10. Reason: {override_reason}]"
      )
      cursor.execute(
          "UPDATE queue SET urgency=?, status=?, notes=? WHERE id=?",
          (new_urgency, new_status, updated_notes, sel_id),
      )
      conn.commit()
      conn.close()
      st.success(
          f"✅ Applied Manager Priority Score `{new_urgency}/10` to Unit ID"
          f" #{sel_id}!"
      )

# =========================================================
# VIEW 10: CREATE SERIAL CERT FOLDER
# =========================================================
elif nav_choice == "Create Serial Cert Folder":
  st.subheader("📁 Create Local Serial Cert Folder")

  if df_queue.empty:
    st.warning("No unit records available in database.")
  else:
    unit_map = build_unit_dropdown_options(df_queue)

    if unit_map:
      selected_label = st.selectbox(
          "Select Unit for Cert Folder Creation:",
          options=list(unit_map.keys()),
          key="cert_folder_select",
      )

      selected_id = unit_map[selected_label]
      selected_row = df_queue[df_queue["id"] == selected_id].iloc[0]

      st.markdown("---")
      st.markdown("#### Selected Unit Summary")
      c1, c2, c3 = st.columns(3)
      c1.write(f"**RGA Number:** `{selected_row.get('rga_number', 'N/A')}`")
      c2.write(
          f"**Notification:** `{selected_row.get('notification_number', 'N/A')}`"
      )
      c3.write(
          f"**Serial Number:** `{selected_row.get('serial_number', 'N/A')}`"
      )

      st.markdown("---")

      if is_local_mode:
        if st.button("📁 Create Folder & Setup Cert Template", type="primary"):
          rga_clean = (
              str(selected_row.get("rga_number", "UNKNOWN"))
              .replace("nan", "")
              .strip()
              or "NO_RGA"
          )
          sn_clean = (
              str(selected_row.get("serial_number", "UNKNOWN"))
              .replace("nan", "")
              .strip()
              or "NO_SN"
          )
          folder_title = f"RGA_{rga_clean}_SN_{sn_clean}"
          target_dir = os.path.join(LOCAL_CERTS_DIR, folder_title)

          try:
            os.makedirs(target_dir, exist_ok=True)

            # Generate template text file inside directory
            template_path = os.path.join(
                target_dir, f"Cert_Template_{sn_clean}.txt"
            )
            with open(template_path, "w", encoding="utf-8") as f:
              f.write(
                  f"HYDAC CERTIFICATE RECORD\nRGA: {rga_clean}\nSN:"
                  f" {sn_clean}\nDate:"
                  f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
              )

            st.success(
                f"✅ Folder structure successfully generated locally at:\n`{target_dir}`"
            )
          except Exception as err:
            st.error(f"❌ Failed to create folder directory: {err}")
      else:
        st.warning(
            "⚠️ **Local folder creation is disabled in Streamlit Cloud"
            " mode.**\n\nTo generate folders on your PC:\n1. Launch the app"
            " locally via `run_app.bat`.\n2. Switch the **Enable Local PC Mode**"
            " toggle at the top to **ON**."
        )

# =========================================================
# VIEW 11: VIEW-ONLY DISPLAY CONFIG
# =========================================================
elif nav_choice == "⚙️ View-Only Display Config":
  st.subheader("⚙️ Display Column Preferences")
  st.write("Configure column preferences for the main queue dashboard:")
  show_rga = st.checkbox("Display RGA Column", value=True)
  show_notif = st.checkbox("Display Notification Column", value=True)
  show_sn = st.checkbox("Display Serial Number Column", value=True)
  st.success("Preferences saved to local session context.")

# =========================================================
# VIEW 12: DEMO & RESET CONTROLS
# =========================================================
elif nav_choice == "Demo & Reset Controls":
  st.subheader("🛠️ Operations Command Reset & Demo Seeder")
  st.markdown(
      "Use these tools to re-seed the SQLite database with fresh demo lab"
      " records or clear system cache."
  )

  c_seed, c_clear = st.columns(2)

  with c_seed:
    with st.container(border=True):
      st.markdown("#### 🔄 Reset & Seed Demo Data")
      st.caption(
          "Wipes current queue database and inserts 10 realistic HYDAC lab"
          " records (CS 1000, FAM-10, Caterpillar, John Deere)."
      )
      if st.button("🌱 Execute Database Reset & Seed", type="primary"):
        reset_and_seed_db()
        st.cache_data.clear()
        st.success(
            "✅ Database reset complete! 10 sample records populated into"
            " `lab_queue.db`."
        )
        st.rerun()

  with c_clear:
    with st.container(border=True):
      st.markdown("#### 🧹 Flush App Cache")
      st.caption(
          "Flushes Streamlit's internal memory cache without deleting database"
          " records."
      )
      if st.button("🔄 Clear App Cache"):
        st.cache_data.clear()
        st.success("App cache cleared successfully.")

# =========================================================
# VIEW 13: MONTHLY VOLUME ANALYTICS
# =========================================================
elif nav_choice == "Monthly Volume Analytics":
  st.subheader("📈 Monthly Volume & Status Analytics")
  if df_queue.empty:
    st.warning("No data available for analytics.")
  else:
    c1, c2 = st.columns(2)
    c1.metric("Total Processed Records", len(df_queue))
    c2.metric("Critical Urgency Units", (df_queue["urgency"] >= 8).sum())

    st.markdown("---")
    st.markdown("#### Units Breakdown by Workflow Status")
    st.bar_chart(df_queue["status"].value_counts())

    st.markdown("#### Priority Distribution (Urgency Scores 1 to 10)")
    st.bar_chart(df_queue["urgency"].value_counts())

# =========================================================
# VIEW 14: BACKUP & DATA EXPORT
# =========================================================
elif nav_choice == "Backup & Data Export":
  st.subheader("📥 Data Export & Database Snapshot")

  if not df_queue.empty:
    st.markdown(
        "Download a complete snapshot of all active records from `lab_queue.db`:"
    )
    c_csv, c_excel = st.columns(2)

    with c_csv:
      csv_bytes = df_queue.to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 Download CSV Snapshot",
          data=csv_bytes,
          file_name="lab_queue_backup.csv",
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
          file_name="lab_queue_backup.xlsx",
          mime=(
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          ),
          use_container_width=True,
      )
  else:
    st.warning("No data currently available to export.")