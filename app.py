import io
import os
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# =========================================================
# PAGE CONFIGURATION & FUTURISTIC HYDAC OS THEME
# =========================================================
st.set_page_config(
    page_title="HYDAC Lab Operations Command OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",  # Collapsed for cleaner full-screen SPA feel
)

DB_FILE = "lab_queue.db"
LOCAL_CERTS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Certs"
UPLOADS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Uploads"

os.makedirs(UPLOADS_DIR, exist_ok=True)

# Injected Tailwind-Inspired Dark Slate / Crimson Styling & FontAwesome
st.markdown(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Montserrat:wght@600;700;800;900&display=swap" rel="stylesheet">

    <style>
    /* Dark Radial Grid Background */
    .stApp {
        background-color: #090D16 !important;
        background-image: radial-gradient(rgba(227, 6, 19, 0.2) 0.8px, transparent 0.8px), radial-gradient(rgba(255, 255, 255, 0.05) 0.8px, #090D16 0.8px) !important;
        background-size: 30px 30px !important;
        background-position: 0 0, 15px 15px !important;
        font-family: 'Inter', sans-serif;
        color: #F8FAFC !important;
    }

    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2.5rem;
        max-width: 95%;
    }

    h1, h2, h3, h4, .font-heading {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Command Banner Header */
    .hydac-banner {
        background: linear-gradient(135deg, #0B0F17 0%, #1E1B2E 50%, #151C2C 100%);
        border: 1px solid rgba(227, 6, 19, 0.4);
        border-left: 6px solid #E30613;
        border-radius: 20px;
        padding: 20px 28px;
        color: #FFFFFF;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(227, 6, 19, 0.2);
        margin-bottom: 20px;
    }
    .hydac-title {
        font-size: 2.1rem;
        font-weight: 900;
        color: #FFFFFF;
        letter-spacing: -0.5px;
        text-transform: uppercase;
    }

    /* Live Progress Gauge Card */
    .gauge-card {
        background: rgba(21, 28, 44, 0.85);
        border: 1px solid #2D3D58;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }
    .gauge-bar-bg {
        width: 100%;
        height: 14px;
        background-color: #0F172A;
        border-radius: 20px;
        border: 1px solid #2D3D58;
        overflow: hidden;
        padding: 2px;
    }
    .gauge-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #E30613 0%, #FF4D5A 100%);
        border-radius: 20px;
        box-shadow: 0 0 12px rgba(227, 6, 19, 0.8);
        transition: width 0.5s ease-in-out;
    }

    /* Status Badges */
    .badge-fresh {
        background: rgba(6, 95, 70, 0.35);
        color: #34D399;
        border: 1px solid #059669;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 800;
    }
    .badge-warn {
        background: rgba(133, 77, 14, 0.35);
        color: #FDE047;
        border: 1px solid #CA8A04;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 800;
    }
    .badge-critical {
        background: rgba(153, 27, 27, 0.45);
        color: #FF8888;
        border: 1px solid #E30613;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 800;
        box-shadow: 0 0 10px rgba(227, 6, 19, 0.4);
    }
    .badge-owner {
        background: rgba(30, 58, 138, 0.4);
        color: #93C5FD;
        border: 1px solid #2563EB;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 800;
    }
    .badge-unassigned {
        background: rgba(55, 65, 81, 0.5);
        color: #E5E7EB;
        border: 1px solid #6B7280;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 800;
    }

    /* Primary Action Buttons */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #E30613 0%, #99000B 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #FF3344 !important;
        font-weight: 800 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 16px rgba(227, 6, 19, 0.4) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #FF1A27 0%, #C4000C 100%) !important;
        box-shadow: 0 6px 20px rgba(227, 6, 19, 0.6) !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# DATABASE INIT & SCHEMA AUTO-REPAIR
# =========================================================
def init_db():
  """Ensures SQLite database schema exists with assignment and photo support."""
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
  """Loads queue data and calculates age metrics for color badges."""
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

    df["parsed_date"] = pd.to_datetime(df["date_logged"], errors="coerce")
    now = datetime.now()
    df["age_days"] = (now - df["parsed_date"]).dt.days.fillna(0).astype(int)
    df["age_weeks"] = (df["age_days"] / 7).round(1)

  return df


def reset_and_seed_db():
  """Resets database with realistic parent/child HYDAC RGA requests."""
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
      (
          "60083000",
          "20007503",
          "Caterpillar Inc.",
          "CS 1000 Contamination Sensor",
          "000SS01831K0000001",
          "Under Testing",
          9,
          "Geo Hall",
          "[Synced Email] High priority laser diode calibration for main line.",
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
          "Optical benchmarking on CalRig test bench 1.",
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
          "Intake complete. Awaiting technician assignment.",
          "",
          "2026-10-10",
      ),
      (
          "60083105",
          "20007510",
          "John Deere Corp.",
          "FAM-10 Fluid Conditioning Unit",
          "FAM10-998231-A",
          "Received in Lab",
          6,
          "Unassigned",
          "Unit intake over 8 weeks old. Needs warranty evaluation.",
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
          "Secondary vacuum pump module attached.",
          "",
          "2026-08-01",
      ),
      (
          "60083112",
          "20007522",
          "Komatsu Ltd.",
          "FCU 1310 Portable Filtration Unit",
          "FCU1310-88412-A",
          "Pending Customer Info",
          4,
          "Alex Rivera",
          "Waiting on plant manager response for operating hydraulic pressure.",
          "",
          "2026-09-15",
      ),
      (
          "60083145",
          "20007548",
          "Parker Hannifin",
          "AS 1000 AquaSensor",
          "AS1000-77621-C",
          "Received in Lab",
          7,
          "Unassigned",
          "Fresh field return intake today.",
          "",
          "2026-10-26",
      ),
      (
          "60083150",
          "20007555",
          "Eaton Hydraulics",
          "CS 2000 Particle Counter",
          "CS2000-55102-D",
          "Under Testing",
          10,
          "Unassigned",
          "CRITICAL / EXPEDITE: High priority warranty evaluation.",
          "",
          "2026-10-25",
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
  """Formats selection labels for edit forms."""
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
# INTERACTIVE MODAL DIALOG OVERLAYS (POPUP WINDOWS)
# =========================================================
@st.dialog("🖐️ Request Assignment & Claim Portal")
def modal_claim_unit(unit_id, current_owner, model_name, serial_num):
  st.markdown(f"### Assign Unit ID #{unit_id}")
  st.write(f"**Model:** `{model_name}` | **SN:** `{serial_num}`")
  st.write(f"Current Owner: **{current_owner}**")

  st.markdown("---")
  c1, c2 = st.columns(2)
  with c1:
    if st.button("🖐️ Self-Claim (Geo Hall)", type="primary", use_container_width=True):
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute(
          "UPDATE queue SET assigned_to='Geo Hall' WHERE id=?", (unit_id,)
      )
      conn.commit()
      conn.close()
      st.toast("✅ Claimed by Geo Hall!", icon="🖐️")
      st.rerun()

  with c2:
    target_assignee = st.selectbox(
        "Reassign Ownership:",
        ["Unassigned", "Geo Hall", "Alex Rivera", "Tech Lab Team B"],
    )
    if st.button("💾 Reassign Owner", use_container_width=True):
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute(
          "UPDATE queue SET assigned_to=? WHERE id=?",
          (target_assignee, unit_id),
      )
      conn.commit()
      conn.close()
      st.toast(f"✅ Reassigned to {target_assignee}!", icon="👤")
      st.rerun()


@st.dialog("📷 Inspection Photo & Attachment Hub")
def modal_manage_photo(unit_id, photo_path):
  st.markdown(f"### Inspection Photos — Unit ID #{unit_id}")

  if photo_path and os.path.exists(photo_path):
    st.image(
        photo_path,
        caption=f"Attached Inspection Image (Unit #{unit_id})",
        use_container_width=True,
    )
  else:
    st.info("No inspection photos currently attached to this record.")

  st.markdown("---")
  uploaded_img = st.file_uploader(
      "Upload New Defect / Test Photo:", type=["png", "jpg", "jpeg"]
  )
  if uploaded_img:
    img_filename = f"Unit_{unit_id}_{uploaded_img.name}"
    save_path = os.path.join(UPLOADS_DIR, img_filename)
    with open(save_path, "wb") as f:
      f.write(uploaded_img.getbuffer())

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE queue SET photo_path=? WHERE id=?", (save_path, unit_id)
    )
    conn.commit()
    conn.close()
    st.toast("✅ Photo uploaded successfully!", icon="📷")
    st.rerun()


@st.dialog("💬 Append Diagnostic Note & Test Log")
def modal_append_note(unit_id, current_notes):
  st.markdown(f"### Diagnostic Log — Unit ID #{unit_id}")
  st.text_area(
      "Existing Log History:",
      value=current_notes or "No log history.",
      height=150,
      disabled=True,
  )

  new_note = st.text_input(
      "New Outcome / Communication Note:",
      placeholder="Type test bench results...",
  )
  if st.button("💬 Save Log Note", type="primary", use_container_width=True):
    if new_note:
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      updated_notes = (
          str(current_notes or "")
          + f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')} - Geo Hall]: {new_note}"
      )
      cursor.execute(
          "UPDATE queue SET notes=? WHERE id=?", (updated_notes, unit_id)
      )
      conn.commit()
      conn.close()
      st.toast("✅ Note appended!", icon="💬")
      st.rerun()


# =========================================================
# TOP NAVIGATION HEADER & BANNER
# =========================================================
col_logo, col_header = st.columns([1, 7])
with col_logo:
  if os.path.exists("logo.png"):
    st.image("logo.png", width=110)
  else:
    st.markdown("### ⚡ **HYDAC**")

with col_header:
  st.markdown(
      """
    <div class="hydac-banner">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
            <span style="background:rgba(227,6,19,0.25); color:#FF8888; border:1px solid #E30613; padding:2px 10px; border-radius:12px; font-size:0.7rem; font-weight:800; text-transform:uppercase;">
                <i class="fa-solid fa-microchip"></i> HYDAC OS v2.6
            </span>
            <span style="background:rgba(255,255,255,0.1); color:#E2E8F0; padding:2px 10px; border-radius:12px; font-size:0.7rem; font-weight:700;">
                <i class="fa-solid fa-shield-halved"></i> Active User: Geo Hall (Lab Lead)
            </span>
        </div>
        <div class="hydac-title">Electronic Lab Operations Command OS</div>
        <div style="font-size:0.88rem; color:#94A3B8; margin-top:2px;">HYDAC Technology Corp — Quality Control, Interactive Request Tracking & Calibration Portal</div>
    </div>
    """,
      unsafe_allow_html=True,
  )

# Top Interactive Navigation Segmented Control
nav_choice = st.segmented_control(
    "Select Workflow Module:",
    [
        "📊 Live Command OS",
        "📥 Unit Intake Hub",
        "⚙️ Queue Operations",
        "✉️ Outlook Email Sync",
        "🛠️ System Admin & Tools",
    ],
    default="📊 Live Command OS",
)

df_queue = load_data()


# =========================================================
# MODULE 1: INTERACTIVE COMMAND OS DASHBOARD
# =========================================================
if nav_choice == "📊 Live Command OS":
  if df_queue.empty:
    st.warning(
        "No active unit records found in database. Go to **System Admin &"
        " Tools** to populate sample demo data!"
    )
  else:
    # Calculation for Live Progress Gauge Bar
    completed_units = (df_queue["status"] == "Completed").sum()
    total_units = len(df_queue)
    completion_rate = (
        int((completed_units / total_units) * 100) if total_units > 0 else 0
    )
    unassigned_count = (df_queue["assigned_to"] == "Unassigned").sum()
    overdue_count = (df_queue["age_weeks"] >= 8).sum()

    # Interactive Queue Workload Progress Gauge
    st.markdown(
        f"""
        <div class="gauge-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <div>
                    <span style="font-weight:900; font-size:1.1rem; color:#FFFFFF; font-family:'Montserrat', sans-serif;">
                        <i class="fa-solid fa-gauge-high" style="color:#E30613; margin-right:6px;"></i> Active Queue Workload & Throughput Gauge
                    </span>
                    <div style="font-size:0.8rem; color:#94A3B8;">Real-time completion index and unassigned request tracking.</div>
                </div>
                <div style="text-align:right;">
                    <span class="badge-critical"><i class="fa-solid fa-fire"></i> {overdue_count} OVERDUE REQUESTS</span>
                </div>
            </div>
            <div style="margin-top:12px;">
                <div style="display:flex; justify-content:space-between; font-size:0.78rem; font-weight:800; color:#E2E8F0; margin-bottom:4px;">
                    <span>Queue Resolution Progress: {completion_rate}% Completed ({completed_units} / {total_units} Units)</span>
                    <span>Unassigned Requests: {unassigned_count} Items</span>
                </div>
                <div class="gauge-bar-bg">
                    <div class="gauge-bar-fill" style="width: {max(completion_rate, 8)}%;"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Top Metric Bar
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Line Items", len(df_queue))
    m2.metric("Unassigned Requests", unassigned_count)
    m3.metric("Overdue (8+ Weeks)", overdue_count)
    m4.metric(
        "Assigned to Geo Hall", (df_queue["assigned_to"] == "Geo Hall").sum()
    )

    st.markdown("---")

    # Search & Filter Controls
    c_search, c_assignee = st.columns([3, 1])
    search_term = c_search.text_input(
        "🔍 Search Requests (RGA, Notification, Customer, Model, Serial Number):",
        placeholder="Type RGA, Serial Number, or Customer Name...",
    )
    assignee_filter = c_assignee.selectbox(
        "Filter Ownership",
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

    filtered_df = filtered_df.sort_values(by="parsed_date", ascending=True)

    st.markdown("### 📋 Interactive Pending Request Cards")

    # Parent RGA Grouping
    parent_groups = filtered_df.groupby("rga_number")

    for rga, group in parent_groups:
      max_weeks = group["age_weeks"].max()
      cust_name = group["customer_name"].iloc[0] or "N/A"
      notif_num = group["notification_number"].iloc[0] or "N/A"
      item_count = len(group)
      unassigned_in_group = (group["assigned_to"] == "Unassigned").sum()

      # Age Badges
      if max_weeks <= 4:
        age_badge = (
            f'<span class="badge-fresh"><i class="fa-solid'
            f' fa-circle-check"></i> FRESH ({max_weeks} Wks)</span>'
        )
      elif max_weeks <= 7:
        age_badge = (
            f'<span class="badge-warn"><i class="fa-solid fa-clock"></i>'
            f' ATTENTION ({max_weeks} Wks)</span>'
        )
      else:
        age_badge = (
            f'<span class="badge-critical"><i class="fa-solid'
            f' fa-triangle-exclamation"></i> OVERDUE ({max_weeks} Wks)</span>'
        )

      # Ownership Badges
      if unassigned_in_group == item_count:
        assign_pill = (
            '<span class="badge-unassigned"><i class="fa-solid'
            ' fa-user-slash"></i> UNASSIGNED</span>'
        )
      else:
        assignees = ", ".join(group["assigned_to"].unique())
        assign_pill = (
            f'<span class="badge-owner"><i class="fa-solid fa-user-check"></i>'
            f' {assignees}</span>'
        )

      expander_header = f"Parent RGA: {rga}  |  Customer: {cust_name}  |  {item_count} Child Item(s)  |  Notif: {notif_num}"

      with st.expander(expander_header, expanded=False):
        st.markdown(
            f"**Age Status:** {age_badge} &nbsp;&nbsp;&nbsp;&nbsp; **Ownership"
            f" Status:** {assign_pill}",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # Child Items Table Loop
        for _, child in group.iterrows():
          c_info, c_actions = st.columns([3, 2])

          with c_info:
            st.markdown(f"##### ⚙️ Child Item ID #{child['id']}")
            st.write(
                f"**Model Series:** `{child.get('model_series', 'N/A')}` |"
                f" **SN:** `{child.get('serial_number', 'N/A')}`\n\n"
                f"**Status:** `{child.get('status', 'Received in Lab')}` |"
                f" **Priority:** `{child.get('urgency', 5)}/10`\n\n"
                f"**Current Owner:** `{child.get('assigned_to', 'Unassigned')}`"
            )

            notes_val = str(child.get("notes", "") or "")
            if notes_val:
              st.caption(
                  f"Latest Log: {notes_val.splitlines()[-1] if notes_val else 'None'}"
              )

          with c_actions:
            st.markdown("##### ⚡ Quick Interactive Actions")
            btn1, btn2, btn3 = st.columns(3)

            with btn1:
              if st.button("🖐️ Assign", key=f"btn_claim_{child['id']}"):
                modal_claim_unit(
                    child["id"],
                    child.get("assigned_to", "Unassigned"),
                    child.get("model_series", "N/A"),
                    child.get("serial_number", "N/A"),
                )

            with btn2:
              if st.button("📷 Photos", key=f"btn_photo_{child['id']}"):
                modal_manage_photo(child["id"], child.get("photo_path", ""))

            with btn3:
              if st.button("💬 Log Note", key=f"btn_note_{child['id']}"):
                modal_append_note(child["id"], child.get("notes", ""))

          st.divider()

# =========================================================
# MODULE 2: INTAKE & UNIT LOGGING
# =========================================================
elif nav_choice == "📥 Unit Intake Hub":
  intake_sub = st.radio(
      "Intake Method:",
      [
          "Log Single Item",
          "Log Multiple Units (Batch per RGA)",
          "Bulk Import (Excel/CSV)",
      ],
      horizontal=True,
  )

  if intake_sub == "Log Single Item":
    st.subheader("📝 Log Single Unit into Queue")
    with st.form("new_unit_form"):
      c1, c2 = st.columns(2)
      f_rga = c1.text_input("Parent RGA Number*")
      f_notif = c2.text_input("Notification Number")

      c3, c4 = st.columns(2)
      f_cust = c3.text_input("Customer Name")
      f_model = c4.text_input("Model Series / Description*")

      c5, c6 = st.columns(2)
      f_sn = c5.text_input("Child Serial Number*")
      f_urgency = c6.slider("Priority Score", 1, 10, 5)

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

      if st.form_submit_button("➕ Log Unit into Queue", type="primary"):
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
          st.toast(f"✅ Unit RGA {f_rga} logged successfully!", icon="🚀")
        else:
          st.error("Please fill in required fields (RGA, Model, Serial Number).")

  elif intake_sub == "Log Multiple Units (Batch per RGA)":
    st.subheader("📦 Batch Log Child Serial Numbers under Parent RGA")
    c1, c2 = st.columns(2)
    batch_rga = c1.text_input("Parent RGA Number*:")
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
        st.toast(
            f"✅ Batch-logged {len(sn_list)} serial items under RGA"
            f" {batch_rga}!",
            icon="📦",
        )
      else:
        st.error("Enter RGA, Model, and at least one Serial Number.")

  else:
    st.subheader("📥 Bulk Data Import (Excel / CSV)")
    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file to stage:", type=["csv", "xlsx"]
    )
    if uploaded_file:
      try:
        import_df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        )
        st.dataframe(import_df.head(10), use_container_width=True)

        if st.button("💾 Append Previewed Data to Database", type="primary"):
          conn = sqlite3.connect(DB_FILE)
          import_df.to_sql("queue", conn, if_exists="append", index=False)
          conn.close()
          st.toast(
              f"✅ Appended {len(import_df)} records to database!", icon="💾"
          )
      except Exception as e:
        st.error(f"Error parsing file: {e}")

# =========================================================
# MODULE 3: QUEUE OPERATIONS & FOLDER TOOLS
# =========================================================
elif nav_choice == "⚙️ Queue Operations":
  ops_sub = st.radio(
      "Select Action:",
      [
          "Update Record",
          "Create Local Cert Folder",
          "Supervisor Urgency Override",
      ],
      horizontal=True,
  )

  if ops_sub == "Update Record":
    st.subheader("✏️ Edit Queue Record")
    if not df_queue.empty:
      unit_map = build_unit_dropdown_options(df_queue)
      sel_label = st.selectbox(
          "Select Unit to Edit:", options=list(unit_map.keys())
      )
      sel_id = unit_map[sel_label]
      sel_row = df_queue[df_queue["id"] == sel_id].iloc[0]

      with st.form("edit_form"):
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
            "Model Series", value=str(sel_row.get("model_series", ""))
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
          st.toast(f"✅ Record #{sel_id} updated!", icon="💾")

  elif ops_sub == "Create Local Cert Folder":
    st.subheader("📁 Create Local Serial Cert Folder")
    if not df_queue.empty:
      unit_map = build_unit_dropdown_options(df_queue)
      sel_label = st.selectbox(
          "Select Unit:",
          options=list(unit_map.keys()),
          key="cert_folder_select",
      )
      sel_id = unit_map[sel_label]
      sel_row = df_queue[df_queue["id"] == sel_id].iloc[0]

      if st.button("📁 Generate Cert Folder Directory", type="primary"):
        rga_clean = (
            str(sel_row.get("rga_number", "NO_RGA")).replace("nan", "").strip()
        )
        sn_clean = (
            str(sel_row.get("serial_number", "NO_SN")).replace("nan", "").strip()
        )
        target_dir = os.path.join(
            LOCAL_CERTS_DIR, f"RGA_{rga_clean}_SN_{sn_clean}"
        )

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
          st.toast(f"✅ Created folder: {target_dir}", icon="📁")
        except Exception as err:
          st.error(f"Directory creation error: {err}")

  else:
    st.subheader("⚡ Supervisor Urgency & Escalation Override")
    if not df_queue.empty:
      unit_map = build_unit_dropdown_options(df_queue)
      sel_label = st.selectbox(
          "Select Unit:", options=list(unit_map.keys()), key="sup_override_sel"
      )
      sel_id = unit_map[sel_label]
      sel_row = df_queue[df_queue["id"] == sel_id].iloc[0]

      new_urgency = st.slider(
          "Set Manager Priority Score (1-10)",
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
      override_reason = st.text_input("Manager Justification / Reason:")

      if st.button("⚡ Apply Escalation Override", type="primary"):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        updated_notes = (
            str(sel_row.get("notes", ""))
            + f"\n[Supervisor Override ({datetime.now().strftime('%Y-%m-%d %H:%M')}): Priority set to {new_urgency}/10, Assigned to {new_assignee}. Reason: {override_reason}]"
        )
        cursor.execute(
            "UPDATE queue SET urgency=?, assigned_to=?, status=?, notes=?"
            " WHERE id=?",
            (new_urgency, new_assignee, new_status, updated_notes, sel_id),
        )
        conn.commit()
        conn.close()
        st.toast(
            f"✅ Escalated Priority to {new_urgency}/10 for Unit #{sel_id}!",
            icon="⚡",
        )

# =========================================================
# MODULE 4: OUTLOOK EMAIL SYNC
# =========================================================
elif nav_choice == "✉️ Outlook Email Sync":
  email_sub = st.radio(
      "Sync Feature:",
      [
          "Generate Support Draft",
          "Synced Returns Inbox",
          "Synced Outbox & Replies",
      ],
      horizontal=True,
  )

  if email_sub == "Generate Support Draft":
    st.subheader("✉️ Generate Support Notification Email")
    if not df_queue.empty:
      unit_map = build_unit_dropdown_options(df_queue)
      sel_label = st.selectbox(
          "Select Target Unit:", options=list(unit_map.keys())
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
          "Pre-Populated Draft:", value=email_body, height=280
      )

  elif email_sub == "Synced Returns Inbox":
    st.subheader("📩 Synced Returns Email Inbox")
    email_units = df_queue[
        df_queue["notes"]
        .fillna("")
        .str.contains("\\[Synced Email from Returns", case=False)
    ]
    if email_units.empty:
      st.info("No synced Returns emails found in active records.")
    else:
      unit_map = build_unit_dropdown_options(email_units)
      sel_label = st.selectbox(
          "Select Unit with Email:", options=list(unit_map.keys())
      )
      sel_id = unit_map[sel_label]
      sel_row = email_units[email_units["id"] == sel_id].iloc[0]
      st.text_area(
          "Synced Email Content:",
          value=str(sel_row.get("notes", "")),
          height=280,
      )

  else:
    st.subheader("📤 Sync Outlook Sent Items")
    sent_units = df_queue[
        df_queue["notes"]
        .fillna("")
        .str.contains("\\[Synced Sent Reply", case=False)
    ]
    if sent_units.empty:
      st.info("No sent email replies tagged in database.")
    else:
      unit_map = build_unit_dropdown_options(sent_units)
      sel_label = st.selectbox(
          "Select Unit:", options=list(unit_map.keys())
      )
      sel_id = unit_map[sel_label]
      sel_row = sent_units[sent_units["id"] == sel_id].iloc[0]
      st.text_area(
          "Synced Reply Content:",
          value=str(sel_row.get("notes", "")),
          height=280,
      )

# =========================================================
# MODULE 5: SYSTEM ADMIN, DEMO RESET & EXPORTS
# =========================================================
else:
  admin_sub = st.radio(
      "Admin Tool:",
      ["Demo Reset & Seeding", "Monthly Analytics", "Backup & Data Export"],
      horizontal=True,
  )

  if admin_sub == "Demo Reset & Seeding":
    st.subheader("🛠️ Database Reset & Demo Seeding Engine")
    st.markdown(
        "Use this tool to wipe and re-seed `lab_queue.db` with realistic"
        " Parent/Child RGAs (Caterpillar, John Deere, Komatsu) and verify all"
        " features."
    )

    c_seed, c_clear = st.columns(2)
    with c_seed:
      with st.container(border=True):
        st.markdown("#### 🔄 Reset & Seed Demo Database")
        st.caption(
            "Clears current database and populates 8 realistic test bench"
            " records."
        )
        if st.button("🌱 Execute Reset & Seed", type="primary"):
          reset_and_seed_db()
          st.cache_data.clear()
          st.toast(
              "✅ Database reset complete! Populated 8 demo records.", icon="🌱"
          )
          st.rerun()

    with c_clear:
      with st.container(border=True):
        st.markdown("#### 🧹 Clear Session Cache")
        st.caption("Flushes Streamlit internal cache.")
        if st.button("🔄 Clear App Cache"):
          st.cache_data.clear()
          st.toast("App cache cleared.", icon="🧹")

  elif admin_sub == "Monthly Analytics":
    st.subheader("📈 Monthly Volume Analytics")
    if not df_queue.empty:
      c1, c2, c3 = st.columns(3)
      c1.metric("Total Line Items", len(df_queue))
      c2.metric(
          "Unassigned Items", (df_queue["assigned_to"] == "Unassigned").sum()
      )
      c3.metric("Critical Units (8-10)", (df_queue["urgency"] >= 8).sum())

      st.markdown("---")
      st.markdown("#### Status Breakdown")
      st.bar_chart(df_queue["status"].value_counts())

      st.markdown("#### Assignment Distribution")
      st.bar_chart(df_queue["assigned_to"].value_counts())

  else:
    st.subheader("📥 Backup & Data Export")
    if not df_queue.empty:
      st.markdown("Download snapshot of active records:")
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