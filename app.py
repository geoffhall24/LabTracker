import io
import os
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# =========================================================
# PAGE CONFIGURATION & HYDAC INDUSTRIAL UI THEME
# =========================================================
st.set_page_config(
    page_title="HYDAC Lab Operations Command",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "lab_queue.db"
LOCAL_CERTS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Certs"
UPLOADS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Uploads"

os.makedirs(UPLOADS_DIR, exist_ok=True)

# Modern High-Contrast Industrial UI (CSS)
st.markdown(
    """
    <style>
    :root {
        --hydac-red: #E30613;
        --hydac-dark: #0B0F17;
        --hydac-card: #151C2C;
        --hydac-slate: #1E293B;
        --hydac-border: #2D3D58;
    }

    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 96%;
    }

    /* Header Banner */
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

    /* Age & Status Color Badges */
    .badge-green {
        background-color: #065F46;
        color: #34D399;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #059669;
    }
    .badge-yellow {
        background-color: #854D0E;
        color: #FDE047;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #CA8A04;
    }
    .badge-red {
        background-color: #991B1B;
        color: #FCA5A5;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #DC2626;
        box-shadow: 0 0 8px rgba(220, 38, 38, 0.4);
    }
    .badge-assignee {
        background-color: #1E3A8A;
        color: #93C5FD;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #2563EB;
    }
    .badge-unassigned {
        background-color: #374151;
        color: #D1D5DB;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #4B5563;
    }

    /* Sidebar User Profile */
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

    /* Primary Action Buttons */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #E30613 0%, #A8000A 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 12px rgba(227, 6, 19, 0.3) !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# DATABASE INIT & SCHEMA REPAIR
# =========================================================
def init_db():
  """Ensures SQLite schema exists with assignment and photo support."""
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
            assigned_to TEXT DEFAULT 'Unassigned',
            notes TEXT,
            photo_path TEXT,
            date_logged TEXT
        )
    """)

  # Ensure schema columns exist
  cursor.execute("PRAGMA table_info(queue)")
  existing_cols = [col[1] for col in cursor.fetchall()]

  if "assigned_to" not in existing_cols:
    cursor.execute(
        "ALTER TABLE queue ADD COLUMN assigned_to TEXT DEFAULT 'Unassigned'"
    )
  if "photo_path" not in existing_cols:
    cursor.execute("ALTER TABLE queue ADD COLUMN photo_path TEXT")
  if "urgency" not in existing_cols:
    cursor.execute("ALTER TABLE queue ADD COLUMN urgency INTEGER DEFAULT 5")
  if "date_logged" not in existing_cols:
    cursor.execute("ALTER TABLE queue ADD COLUMN date_logged TEXT")

  conn.commit()
  conn.close()


def load_data():
  """Loads queue data and calculates age in weeks for color coding."""
  init_db()
  conn = sqlite3.connect(DB_FILE)
  try:
    df = pd.read_sql_query("SELECT * FROM queue", conn)
  except Exception:
    df = pd.DataFrame()
  finally:
    conn.close()

  if not df.empty:
    if "assigned_to" not in df.columns:
      df["assigned_to"] = "Unassigned"
    df["assigned_to"] = df["assigned_to"].fillna("Unassigned")

    if "date_logged" not in df.columns or df["date_logged"].isnull().all():
      df["date_logged"] = datetime.now().strftime("%Y-%m-%d")

    # Calculate age metrics
    df["parsed_date"] = pd.to_datetime(df["date_logged"], errors="coerce")
    now = datetime.now()
    df["age_days"] = (now - df["parsed_date"]).dt.days.fillna(0).astype(int)
    df["age_weeks"] = (df["age_days"] / 7).round(1)

  return df


def reset_and_seed_db():
  """Resets database with realistic parent/child RGA requests."""
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
            assigned_to TEXT DEFAULT 'Unassigned',
            notes TEXT,
            photo_path TEXT,
            date_logged TEXT
        )
    """)

  demo_data = [
      # Parent RGA 60083000 (Multiple Child Serial Numbers)
      (
          "60083000",
          "20007503",
          "Caterpillar Inc.",
          "CS 1000 Contamination Sensor",
          "000SS01831K0000001",
          "Under Testing",
          9,
          "Geo Hall",
          "[Synced Email] High priority calibration for line 1.",
          "",
          "2026-10-10",
      ),
      (
          "60083000",
          "20007503",
          "Caterpillar Inc.",
          "CS 1000 Contamination Sensor",
          "000SS01831K0000002",
          "Under Testing",
          9,
          "Geo Hall",
          "Optical sensor benchmarking in progress.",
          "",
          "2026-10-10",
      ),
      (
          "60083000",
          "20007503",
          "Caterpillar Inc.",
          "CS 1000 Contamination Sensor",
          "000SS01831K0000003",
          "Received in Lab",
          9,
          "Unassigned",
          "Awaiting physical inspection on CalRig 2.",
          "",
          "2026-10-10",
      ),
      # Parent RGA 60083105 (Overdue - 8+ Weeks)
      (
          "60083105",
          "20007510",
          "John Deere Corp.",
          "FAM-10 Fluid Conditioning Unit",
          "FAM10-998231-A",
          "Received in Lab",
          6,
          "Unassigned",
          "Unit intake over 8 weeks old. Needs technician evaluation.",
          "",
          "2026-08-01",
      ),
      (
          "60083105",
          "20007510",
          "John Deere Corp.",
          "FAM-10 Fluid Conditioning Unit",
          "FAM10-998231-B",
          "Received in Lab",
          6,
          "Unassigned",
          "Secondary pump module attached.",
          "",
          "2026-08-01",
      ),
      # Parent RGA 60083112 (5 to 7 Weeks)
      (
          "60083112",
          "20007522",
          "Komatsu Ltd.",
          "FCU 1310 Filtration Unit",
          "FCU1310-88412-A",
          "Pending Customer Info",
          4,
          "Alex Rivera",
          "Waiting on customer response for operating pressure limits.",
          "",
          "2026-09-15",
      ),
      # Parent RGA 60083145 (Fresh Intake)
      (
          "60083145",
          "20007548",
          "Parker Hannifin",
          "AS 1000 AquaSensor",
          "AS1000-77621-C",
          "Received in Lab",
          7,
          "Unassigned",
          "New field return intake today.",
          "",
          "2026-10-26",
      ),
  ]

  cursor.executemany(
      """
        INSERT INTO queue (rga_number, notification_number, customer_name, model_series, serial_number, status, urgency, assigned_to, notes, photo_path, date_logged)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
      demo_data,
  )

  conn.commit()
  conn.close()


def build_unit_dropdown_options(df):
  """Formats selection labels for forms."""
  options_map = {}
  if df is None or df.empty:
    return options_map

  for _, row in df.iterrows():
    unit_id = row.get("id", "")
    rga = str(row.get("rga_number", "")).replace("nan", "").strip() or "N/A"
    model = (
        row.get("model_series")
        or row.get("model")
        or row.get("item_description")
        or "N/A"
    )
    sn = str(row.get("serial_number", "")).replace("nan", "").strip() or "N/A"
    assigned = row.get("assigned_to", "Unassigned")

    label = f"RGA: {rga} | {model} | SN: {sn} [Assigned: {assigned}] (ID: {unit_id})"
    options_map[label] = unit_id

  return options_map


# Load state
df_queue = load_data()


# =========================================================
# HEADER BANNER & MODE TOGGLE
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
        <div class="hydac-subtitle">HYDAC Technology Corp — Interactive Request Tracking & Operations Hub</div>
    </div>
    """,
      unsafe_allow_html=True,
  )

with st.container(border=True):
  toggle_col, status_col = st.columns([2, 3])
  with toggle_col:
    is_local_mode = st.toggle(
        "🖥️ Enable Local PC Mode (Folder Creation)", value=False
    )

  with status_col:
    if is_local_mode:
      st.success(
          "Mode: **Local PC** — Direct local cert folder generation enabled"
          f" at:\n`{LOCAL_CERTS_DIR}`"
      )
    else:
      st.info(
          "Mode: **Streamlit Cloud** — Read-only web mode (Local file creation"
          " restricted)."
      )


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================
with st.sidebar:
  st.markdown(
      """
    <div class="sidebar-user-card">
        <div style="font-size:0.7rem; color:#94A3B8; text-transform:uppercase; font-weight:700;">Logged In User</div>
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
          "📊 Dashboard & Interactive Queue",
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

  if nav_category == "📊 Dashboard & Interactive Queue":
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

df_queue = load_data()


# =========================================================
# VIEW 1: INTERACTIVE COMMAND DASHBOARD (EXPANDABLE PARENT/CHILD)
# =========================================================
if nav_choice == "View Queue Dashboard":
  st.subheader("📊 Active Lab Queue Command Center")

  if df_queue.empty:
    st.warning(
        "No active unit records found in database. Go to **Demo & Reset"
        " Controls** in the sidebar to populate test data!"
    )
  else:
    # Top KPI Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Line Items", len(df_queue))

    unassigned_count = (df_queue["assigned_to"] == "Unassigned").sum()
    m2.metric("Unassigned Requests", unassigned_count)

    overdue_count = (df_queue["age_weeks"] >= 8).sum()
    m3.metric("Overdue (8+ Weeks)", overdue_count)

    my_assigned = (df_queue["assigned_to"] == "Geo Hall").sum()
    m4.metric("Assigned to Me", my_assigned)

    st.markdown("---")

    # Filters Bar
    c_search, c_assignee = st.columns([3, 1])
    search_term = c_search.text_input(
        "🔍 Search Requests (RGA, Notification, Customer, Model, Serial Number):",
        placeholder="Type RGA, Serial Number, or Customer Name...",
    )
    assignee_filter = c_assignee.selectbox(
        "Filter Assignment",
        ["All Requests", "Unassigned Only", "Assigned to Me (Geo Hall)"],
    )

    filtered_df = df_queue.copy()
    if assignee_filter == "Unassigned Only":
      filtered_df = filtered_df[filtered_df["assigned_to"] == "Unassigned"]
    elif assignee_filter == "Assigned to Me (Geo Hall)":
      filtered_df = filtered_df[filtered_df["assigned_to"] == "Geo Hall"]

    if search_term:
      filter_mask = filtered_df.astype(str).apply(
          lambda col: col.str.contains(search_term, case=False)
      ).any(axis=1)
      filtered_df = filtered_df[filter_mask]

    # Sort oldest to newest
    filtered_df = filtered_df.sort_values(by="parsed_date", ascending=True)

    st.markdown("### 📋 Interactive Pending Requests List")

    # Group by Parent RGA Number
    parent_groups = filtered_df.groupby("rga_number")

    for rga, group in parent_groups:
      max_weeks = group["age_weeks"].max()
      cust_name = group["customer_name"].iloc[0] or "N/A"
      notif_num = group["notification_number"].iloc[0] or "N/A"
      item_count = len(group)
      unassigned_in_group = (group["assigned_to"] == "Unassigned").sum()

      # Determine Age Color Coding
      if max_weeks <= 4:
        age_badge = (
            f'<span class="badge-green">🟢 0-4 WEEKS ({max_weeks} wks)</span>'
        )
      elif max_weeks <= 7:
        age_badge = (
            f'<span class="badge-yellow">🟡 5-7 WEEKS ({max_weeks} wks)</span>'
        )
      else:
        age_badge = (
            f'<span class="badge-red">🔴 OVERDUE ({max_weeks} wks)</span>'
        )

      # Assignee Pill
      if unassigned_in_group == item_count:
        assign_pill = (
            '<span class="badge-unassigned">👤 UNASSIGNED</span>'
        )
      else:
        assignees = ", ".join(group["assigned_to"].unique())
        assign_pill = f'<span class="badge-assignee">👤 {assignees}</span>'

      expander_header = f"Parent RGA: {rga} | Customer: {cust_name} | {item_count} Child Item(s) | Notif: {notif_num}"

      with st.expander(expander_header, expanded=False):
        st.markdown(
            f"**Age Status:** {age_badge} &nbsp;&nbsp;&nbsp; **Ownership:**"
            f" {assign_pill}",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # Child Items Table / Inspection Cards
        for _, child in group.iterrows():
          c_item, c_assign, c_media = st.columns([2, 1.2, 1.8])

          with c_item:
            st.markdown(f"##### Child Item ID #{child['id']}")
            st.write(
                f"**Model:** `{child.get('model_series', 'N/A')}`\n\n"
                f"**Serial Number:** `{child.get('serial_number', 'N/A')}`\n\n"
                f"**Current Status:** `{child.get('status', 'Received in Lab')}`\n\n"
                f"**Urgency Score:** `{child.get('urgency', 5)}/10`"
            )

          with c_assign:
            st.markdown("##### 👤 Assignment Control")
            current_owner = child.get("assigned_to", "Unassigned")
            st.write(f"Current Owner: **{current_owner}**")

            # Quick Claim Button
            if current_owner == "Unassigned":
              if st.button(
                  "🖐️ Claim Request",
                  key=f"claim_{child['id']}",
                  type="primary",
              ):
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE queue SET assigned_to='Geo Hall' WHERE id=?",
                    (child["id"],),
                )
                conn.commit()
                conn.close()
                st.success("Claimed by Geo Hall!")
                st.rerun()

            # Reassign Dropdown
            new_assignee = st.selectbox(
                "Assign To:",
                ["Unassigned", "Geo Hall", "Alex Rivera", "Tech Lab Team B"],
                index=[
                    "Unassigned",
                    "Geo Hall",
                    "Alex Rivera",
                    "Tech Lab Team B",
                ].index(current_owner)
                if current_owner
                in ["Unassigned", "Geo Hall", "Alex Rivera", "Tech Lab Team B"]
                else 0,
                key=f"assign_select_{child['id']}",
            )
            if new_assignee != current_owner:
              if st.button(
                  "💾 Update Assignment", key=f"save_assign_{child['id']}"
              ):
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE queue SET assigned_to=? WHERE id=?",
                    (new_assignee, child["id"]),
                )
                conn.commit()
                conn.close()
                st.success(f"Assigned to {new_assignee}!")
                st.rerun()

          with c_media:
            st.markdown("##### 📷 Media & Notes History")

            # Display uploaded photo if exists
            photo_file = child.get("photo_path", "")
            if photo_file and os.path.exists(photo_file):
              st.image(
                  photo_file,
                  caption=f"Attached Photo - Unit ID #{child['id']}",
                  width=220,
              )

            # Upload Photo Control
            uploaded_img = st.file_uploader(
                "Attach Photo / Inspection Image:",
                type=["png", "jpg", "jpeg"],
                key=f"photo_{child['id']}",
            )
            if uploaded_img:
              img_filename = f"Unit_{child['id']}_{uploaded_img.name}"
              save_path = os.path.join(UPLOADS_DIR, img_filename)
              with open(save_path, "wb") as f:
                f.write(uploaded_img.getbuffer())

              conn = sqlite3.connect(DB_FILE)
              cursor = conn.cursor()
              cursor.execute(
                  "UPDATE queue SET photo_path=? WHERE id=?",
                  (save_path, child["id"]),
              )
              conn.commit()
              conn.close()
              st.success("Photo attached successfully!")
              st.rerun()

          # Notes history & append note box
          st.text_area(
              "Notes / Communication History:",
              value=str(child.get("notes", "") or ""),
              height=100,
              disabled=True,
              key=f"notes_disp_{child['id']}",
          )

          with st.form(key=f"add_note_form_{child['id']}"):
            new_note_entry = st.text_input(
                "Append New Outcome / Test Note:",
                placeholder="Type inspection result...",
            )
            if st.form_submit_button("💬 Append Note"):
              if new_note_entry:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                updated_notes = (
                    str(child.get("notes", "") or "")
                    + f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')} - {st.session_state.get('user', 'Geo Hall')}]: {new_note_entry}"
                )
                cursor.execute(
                    "UPDATE queue SET notes=? WHERE id=?",
                    (updated_notes, child["id"]),
                )
                conn.commit()
                conn.close()
                st.success("Note appended!")
                st.rerun()

          st.divider()

# =========================================================
# VIEW 2: LOG NEW ITEM (SINGLE)
# =========================================================
elif nav_choice == "Log New Item (Single)":
  st.subheader("📝 Log New Unit into Lab Queue")
  with st.form("new_unit_form"):
    c1, c2 = st.columns(2)
    f_rga = c1.text_input("Parent RGA Number*")
    f_notif = c2.text_input("Notification Number")

    c3, c4 = st.columns(2)
    f_cust = c3.text_input("Customer Name")
    f_model = c4.text_input("Model Series / Description*")

    c5, c6 = st.columns(2)
    f_sn = c5.text_input("Child Serial Number*")
    f_urgency = c6.slider("Priority / Urgency Score", 1, 10, 5)

    f_assign = st.selectbox(
        "Initial Assignee",
        ["Unassigned", "Geo Hall", "Alex Rivera", "Tech Lab Team B"],
    )
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
                INSERT INTO queue (rga_number, notification_number, customer_name, model_series, serial_number, status, urgency, assigned_to, notes, date_logged)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f_rga,
                f_notif,
                f_cust,
                f_model,
                f_sn,
                f_status,
                f_urgency,
                f_assign,
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
  st.subheader("📦 Batch Log Multiple Serial Numbers under Parent RGA")
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
                INSERT INTO queue (rga_number, notification_number, customer_name, model_series, serial_number, status, urgency, assigned_to, date_logged)
                VALUES (?, ?, ?, ?, ?, 'Received in Lab', 5, 'Unassigned', ?)
            """,
            (batch_rga, batch_notif, batch_cust, batch_model, sn, today_str),
        )
      conn.commit()
      conn.close()
      st.success(
          f"✅ Successfully batch-logged {len(sn_list)} child serial number(s)"
          f" under Parent RGA `{batch_rga}`!"
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

      u_assign = st.selectbox(
          "Assignee",
          ["Unassigned", "Geo Hall", "Alex Rivera", "Tech Lab Team B"],
          index=["Unassigned", "Geo Hall", "Alex Rivera", "Tech Lab Team B"].index(
              sel_row.get("assigned_to", "Unassigned")
          )
          if sel_row.get("assigned_to", "Unassigned")
          in ["Unassigned", "Geo Hall", "Alex Rivera", "Tech Lab Team B"]
          else 0,
      )

      u_status = st.text_input("Status", value=str(sel_row.get("status", "")))
      u_notes = st.text_area("Notes", value=str(sel_row.get("notes", "")))

      if st.form_submit_button("💾 Save Record Updates", type="primary"):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
                UPDATE queue SET rga_number=?, notification_number=?, customer_name=?, model_series=?, serial_number=?, status=?, urgency=?, assigned_to=?, notes=?
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
                u_assign,
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

- Parent RGA Number: {sel_row.get('rga_number', 'N/A')}
- Notification Number: {sel_row.get('notification_number', 'N/A')}
- Model Series: {sel_row.get('model_series', 'N/A')}
- Serial Number: {sel_row.get('serial_number', 'N/A')}
- Assigned Technician: {sel_row.get('assigned_to', 'Unassigned')}
- Current Status: {sel_row.get('status', 'N/A')}

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
        f" **Assigned:** `{sel_row.get('assigned_to', 'Unassigned')}`"
    )

    new_urgency = st.slider(
        "Set Manager Urgency Score (1 = Low, 10 = Critical/Expedite)",
        1,
        10,
        int(sel_row.get("urgency", 5)),
    )
    new_assignee = st.selectbox(
        "Reassign Ownership",
        ["Unassigned", "Geo Hall", "Alex Rivera", "Tech Lab Team B"],
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

    if st.button("⚡ Apply Priority & Assignment Override", type="primary"):
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      updated_notes = (
          str(sel_row.get("notes", ""))
          + f"\n[Supervisor Override ({datetime.now().strftime('%Y-%m-%d %H:%M')}): Priority set to {new_urgency}/10, Assigned to {new_assignee}. Reason: {override_reason}]"
      )
      cursor.execute(
          "UPDATE queue SET urgency=?, assigned_to=?, status=?, notes=? WHERE"
          " id=?",
          (new_urgency, new_assignee, new_status, updated_notes, sel_id),
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
          "Wipes current queue database and inserts realistic HYDAC lab"
          " records grouped under parent RGAs (Caterpillar, John Deere,"
          " Komatsu)."
      )
      if st.button("🌱 Execute Database Reset & Seed", type="primary"):
        reset_and_seed_db()
        st.cache_data.clear()
        st.success("✅ Database reset complete! Sample records populated.")
        st.rerun()

  with c_clear:
    with st.container(border=True):
      st.markdown("#### 🧹 Flush App Cache")
      st.caption("Flushes Streamlit's internal memory cache.")
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
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Line Items", len(df_queue))
    c2.metric("Unassigned Items", (df_queue["assigned_to"] == "Unassigned").sum())
    c3.metric("Critical Priority Units", (df_queue["urgency"] >= 8).sum())

    st.markdown("---")
    st.markdown("#### Units Breakdown by Workflow Status")
    st.bar_chart(df_queue["status"].value_counts())

    st.markdown("#### Assignment Distribution")
    st.bar_chart(df_queue["assigned_to"].value_counts())

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