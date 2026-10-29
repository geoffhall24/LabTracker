import io
import os
import json
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# =========================================================
# PAGE CONFIGURATION & TV-OPTIMIZED HIGH-CONTRAST THEME
# =========================================================
st.set_page_config(
    page_title="Electronic Lab Portal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_FILE = "lab_queue.db"
LOCAL_CERTS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Certs"
UPLOADS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Uploads"

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(LOCAL_CERTS_DIR, exist_ok=True)

# High-Contrast TV & Executive Dashboard CSS Injection
st.markdown(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Montserrat:wght@700;800;900&display=swap" rel="stylesheet">

    <style>
    /* Executive Slate Canvas */
    .stApp {
        background-color: #E2E8F0 !important;
        font-family: 'Inter', sans-serif !important;
        color: #0F172A !important;
    }

    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2.5rem;
        max-width: 98%;
    }

    h1, h2, h3, h4, .font-heading {
        font-family: 'Montserrat', sans-serif !important;
        color: #0F172A !important;
        letter-spacing: -0.3px;
    }

    p, span, label, div, .stMarkdown {
        color: #0F172A !important;
    }

    /* WIDGET LABELS */
    label[data-testid="stWidgetLabel"], div[data-testid="stWidgetLabel"] p, .stWidgetLabel {
        color: #0F172A !important;
        font-weight: 800 !important;
        font-size: 0.88rem !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 6px !important;
    }

    /* TEXT INPUTS & TEXTAREAS */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        background-color: #FFFFFF !important;
        border: 2px solid #334155 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08) !important;
    }

    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        background-color: #FFFFFF !important;
    }

    div[data-baseweb="input"] input::placeholder, div[data-baseweb="textarea"] textarea::placeholder {
        color: #64748B !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="input"]:focus-within > div, div[data-baseweb="textarea"]:focus-within > div {
        border-color: #E30613 !important;
        box-shadow: 0 0 8px rgba(227, 6, 19, 0.35) !important;
    }

    /* SELECTBOXES & DROPDOWNS */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 2px solid #334155 !important;
        border-radius: 8px !important;
        color: #0F172A !important;
        font-weight: 800 !important;
    }

    /* SEGMENTED CONTROL / NAVIGATION TABS */
    div[data-testid="stSegmentedControl"] {
        background-color: #CBD5E1 !important;
        padding: 6px !important;
        border-radius: 12px !important;
        border: 1px solid #94A3B8 !important;
    }

    div[data-testid="stSegmentedControl"] button {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #64748B !important;
        font-weight: 800 !important;
        font-size: 0.88rem !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
    }

    div[data-testid="stSegmentedControl"] button:hover {
        background-color: #F1F5F9 !important;
        border-color: #E30613 !important;
        color: #E30613 !important;
    }

    div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
        background-color: #E30613 !important;
        color: #FFFFFF !important;
        border: 1px solid #B91C1C !important;
        box-shadow: 0 4px 12px rgba(227, 6, 19, 0.3) !important;
    }

    div[data-testid="stSegmentedControl"] button[aria-selected="true"] * {
        color: #FFFFFF !important;
    }

    /* EXPANDER CARDS */
    details[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #94A3B8 !important;
        border-radius: 12px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    }

    summary[data-testid="stExpanderSummary"] {
        background-color: #F1F5F9 !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        border-left: 6px solid #E30613 !important;
    }

    summary[data-testid="stExpanderSummary"] p, summary[data-testid="stExpanderSummary"] span {
        color: #0F172A !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
    }

    /* HEADER BANNER */
    .hydac-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border-left: 6px solid #E30613;
        border-radius: 14px;
        padding: 22px 28px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
        margin-bottom: 22px;
    }
    .hydac-banner * {
        color: #FFFFFF !important;
    }
    .hydac-title {
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: -0.5px;
        text-transform: uppercase;
        margin: 4px 0;
        font-family: 'Montserrat', sans-serif;
    }

    /* KPI METRIC CARDS */
    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #94A3B8 !important;
        border-top: 4px solid #E30613 !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #0F172A !important;
        font-size: 2.3rem !important;
        font-weight: 900 !important;
        font-family: 'Montserrat', sans-serif !important;
    }
    div[data-testid="stMetricLabel"] div {
        color: #334155 !important;
        font-weight: 800 !important;
        font-size: 0.82rem !important;
        text-transform: uppercase;
    }

    /* SHELF LOCATION BADGES */
    .badge-inbound { background-color: #E0F2FE; color: #0369A1; border: 1px solid #7DD3FC; padding: 4px 12px; border-radius: 20px; font-weight: 800; font-size: 0.78rem; display: inline-block; }
    .badge-ready { background-color: #FEF9C3; color: #A16207; border: 1px solid #FDE047; padding: 4px 12px; border-radius: 20px; font-weight: 800; font-size: 0.78rem; display: inline-block; }
    .badge-waiting { background-color: #FFEDD5; color: #C2410C; border: 1px solid #FDBA74; padding: 4px 12px; border-radius: 20px; font-weight: 800; font-size: 0.78rem; display: inline-block; }
    .badge-flow { background-color: #F3E8FF; color: #6B21A8; border: 1px solid #D8B4FE; padding: 4px 12px; border-radius: 20px; font-weight: 800; font-size: 0.78rem; display: inline-block; }
    .badge-calrig { background-color: #E0E7FF; color: #3730A3; border: 1px solid #A5B4FC; padding: 4px 12px; border-radius: 20px; font-weight: 800; font-size: 0.78rem; display: inline-block; }
    .badge-completed { background-color: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; padding: 4px 12px; border-radius: 20px; font-weight: 800; font-size: 0.78rem; display: inline-block; }

    .badge-critical { background-color: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; padding: 4px 12px; border-radius: 20px; font-weight: 800; font-size: 0.78rem; display: inline-block; }
    .badge-owner { background-color: #DBEAFE; color: #1D4ED8; border: 1px solid #93C5FD; padding: 4px 12px; border-radius: 20px; font-weight: 800; font-size: 0.78rem; display: inline-block; }

    /* BUTTONS */
    div.stButton > button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border: 1px solid #0F172A !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button * {
        color: #FFFFFF !important;
    }
    div.stButton > button:hover {
        background-color: #1E293B !important;
        border-color: #1E293B !important;
    }
    div.stButton > button[kind="primary"] {
        background-color: #E30613 !important;
        color: #FFFFFF !important;
        border: 1px solid #B91C1C !important;
        box-shadow: 0 4px 12px rgba(227, 6, 19, 0.3) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #C4000C !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# SESSION STATE & AUTHENTICATION GATE
# =========================================================
if "authenticated" not in st.session_state:
  st.session_state["authenticated"] = False
if "user_name" not in st.session_state:
  st.session_state["user_name"] = ""
if "user_role" not in st.session_state:
  st.session_state["user_role"] = ""

VALID_USERS = {
    "geo.h": {
        "password": "HYDAC2026",
        "name": "Geo H",
        "role": "Lab Technician",
    },
    "adam.k": {"password": "HYDAC2026", "name": "Adam K", "role": "Supervisor"},
    "new.guy": {
        "password": "HYDAC2026",
        "name": "New Guy",
        "role": "Lab Technician",
    },
}

if not st.session_state["authenticated"]:
  c_auth1, c_auth2, c_auth3 = st.columns([1, 2, 1])
  with c_auth2:
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.container(border=True):
      st.markdown(
          """
            <div style="text-align:center; padding:10px 0;">
                <h2 style="color:#0F172A; font-weight:900; margin-bottom:4px;">⚡ ELECTRONIC LAB PORTAL</h2>
                <p style="color:#475569; font-size:0.9rem; font-weight:600;">HYDAC Technology Corp Operations System</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
      st.markdown("---")

      user_input = st.text_input("Username:", key="auth_user")
      pass_input = st.text_input(
          "Password:", type="password", key="auth_pass"
      )

      b_col1, b_col2 = st.columns(2)
      with b_col1:
        if st.button("🔓 Sign In", type="primary", use_container_width=True):
          u_clean = user_input.strip().lower()
          if (
              u_clean in VALID_USERS
              and VALID_USERS[u_clean]["password"] == pass_input.strip()
          ):
            st.session_state["authenticated"] = True
            st.session_state["user_name"] = VALID_USERS[u_clean]["name"]
            st.session_state["user_role"] = VALID_USERS[u_clean]["role"]
            st.toast(
                f"Welcome back, {st.session_state['user_name']}!", icon="⚡"
            )
            st.rerun()
          else:
            st.error("Invalid Username or Password.")

      with b_col2:
        if st.button("🚀 Quick Login (Geo H)", use_container_width=True):
          st.session_state["authenticated"] = True
          st.session_state["user_name"] = "Geo H"
          st.session_state["user_role"] = "Lab Technician"
          st.toast("Authenticated as Geo H (Lab Tech)", icon="🚀")
          st.rerun()

      st.caption("Authorized Lab Personnel Accounts:")
      st.caption("• Geo H (Technician): `geo.h` / `HYDAC2026`")
      st.caption("• Adam K (Supervisor): `adam.k` / `HYDAC2026`")
      st.caption("• New Guy (Technician): `new.guy` / `HYDAC2026`")
  st.stop()


# =========================================================
# DATABASE INITIALIZATION & SCHEMA AUTO-REPAIR
# =========================================================
def init_db():
  """Ensures SQLite database schema exists with location, form, and accessory tracking."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rga_number TEXT,
            notification_number TEXT,
            customer_name TEXT,
            csr_name TEXT,
            service_requested TEXT DEFAULT 'Calibration',
            model_series TEXT,
            serial_number TEXT,
            location TEXT DEFAULT 'Ready for Evaluation',
            status TEXT DEFAULT 'Received in Lab',
            urgency INTEGER DEFAULT 5,
            assigned_to TEXT DEFAULT 'Unassigned',
            accessories TEXT,
            visual_inspection TEXT,
            eval_form_type TEXT,
            eval_data TEXT,
            notes TEXT,
            photo_path TEXT,
            cal_file_path TEXT,
            date_logged TEXT,
            customer_hold_date TEXT
        )
    """)

  cursor.execute("PRAGMA table_info(queue)")
  cols = [col[1] for col in cursor.fetchall()]

  needed_cols = {
      "csr_name": "TEXT",
      "service_requested": "TEXT DEFAULT 'Calibration'",
      "location": "TEXT DEFAULT 'Ready for Evaluation'",
      "accessories": "TEXT",
      "visual_inspection": "TEXT",
      "eval_form_type": "TEXT",
      "eval_data": "TEXT",
      "cal_file_path": "TEXT",
      "customer_hold_date": "TEXT",
  }

  for col_name, col_type in needed_cols.items():
    if col_name not in cols:
      cursor.execute(f"ALTER TABLE queue ADD COLUMN {col_name} {col_type}")

  conn.commit()
  conn.close()


def load_data():
  """Loads queue data and calculates age metrics & 30-day customer countdowns."""
  init_db()
  conn = sqlite3.connect(DB_FILE)
  try:
    df = pd.read_sql_query("SELECT * FROM queue", conn)
  except Exception:
    df = pd.DataFrame()
  finally:
    conn.close()

  if not df.empty:
    df["assigned_to"] = df["assigned_to"].fillna("Unassigned")
    df["location"] = df["location"].fillna("Ready for Evaluation")

    if "date_logged" not in df.columns or df["date_logged"].isnull().all():
      df["date_logged"] = datetime.now().strftime("%Y-%m-%d")

    df["parsed_date"] = pd.to_datetime(df["date_logged"], errors="coerce")
    now = datetime.now()
    df["age_days"] = (now - df["parsed_date"]).dt.days.fillna(0).astype(int)
    df["age_weeks"] = (df["age_days"] / 7).round(1)

    # Calculate 30-Day Customer Response Countdown
    def calc_hold_days(row):
      if (
          row["location"] == "Waiting for Customer Response"
          and row.get("customer_hold_date")
          and str(row["customer_hold_date"]).strip() != ""
      ):
        try:
          hold_start = datetime.strptime(
              str(row["customer_hold_date"]), "%Y-%m-%d"
          )
          days_waiting = (now - hold_start).days
          return max(0, 30 - days_waiting)
        except Exception:
          return 30
      return 30

    df["days_remaining_hold"] = df.apply(calc_hold_days, axis=1)

  return df


def assign_parent_rga_cascade(rga_number, new_assignee):
  """CASCADING ASSIGNMENT: When parent RGA is assigned, all children get assigned to same person."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE queue SET assigned_to=? WHERE rga_number=?",
      (new_assignee, rga_number),
  )
  conn.commit()
  conn.close()


def update_location_and_status(unit_id, new_location, new_status=None):
  """Updates unit shelf location and sets customer hold countdown date if applicable."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  today_str = datetime.now().strftime("%Y-%m-%d")

  if new_location == "Waiting for Customer Response":
    cursor.execute(
        "UPDATE queue SET location=?, customer_hold_date=? WHERE id=?",
        (new_location, today_str, unit_id),
    )
  else:
    cursor.execute(
        "UPDATE queue SET location=? WHERE id=?", (new_location, unit_id)
    )

  if new_status:
    cursor.execute(
        "UPDATE queue SET status=? WHERE id=?", (new_status, unit_id)
    )

  conn.commit()
  conn.close()


def reset_and_seed_db():
  """Resets database with realistic parent/child HYDAC test bench records."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("DROP TABLE IF EXISTS queue")
  cursor.execute("""
        CREATE TABLE queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rga_number TEXT,
            notification_number TEXT,
            customer_name TEXT,
            csr_name TEXT,
            service_requested TEXT,
            model_series TEXT,
            serial_number TEXT,
            location TEXT,
            status TEXT,
            urgency INTEGER DEFAULT 5,
            assigned_to TEXT DEFAULT 'Unassigned',
            accessories TEXT,
            visual_inspection TEXT,
            eval_form_type TEXT,
            eval_data TEXT,
            notes TEXT,
            photo_path TEXT,
            cal_file_path TEXT,
            date_logged TEXT,
            customer_hold_date TEXT
        )
    """)

  demo_data = [
      (
          "60083000",
          "20007503",
          "Caterpillar Inc.",
          "Sarah Jenkins",
          "Calibration",
          "CS 1000 Contamination Sensor",
          "000SS01831K0000001",
          "CalRig",
          "Under Calibration",
          9,
          "Geo H",
          "Case, Power Adapter, Communication Cable",
          "Clean exterior, optical port clear",
          "F-0100",
          "{}",
          "High priority diode test bench 1.",
          "",
          "",
          "2026-10-10",
          "",
      ),
      (
          "60083000",
          "20007503",
          "Caterpillar Inc.",
          "Sarah Jenkins",
          "Calibration",
          "CS 1000 Contamination Sensor",
          "000SS01831K0000002",
          "CalRig",
          "Under Calibration",
          9,
          "Geo H",
          "Case, Power Adapter",
          "Diode bench check",
          "F-0100",
          "{}",
          "Optical bench sync complete.",
          "",
          "",
          "2026-10-10",
          "",
      ),
      (
          "60083000",
          "20007503",
          "Caterpillar Inc.",
          "Sarah Jenkins",
          "Repair",
          "CS 1000 Contamination Sensor",
          "000SS01831K0000003",
          "Ready for Evaluation",
          "Received in Lab",
          9,
          "Unassigned",
          "Case",
          "Minor housing scuff",
          "F-0100",
          "{}",
          "Intake complete.",
          "",
          "",
          "2026-10-10",
          "",
      ),
      (
          "60083105",
          "20007510",
          "John Deere Corp.",
          "Mike Ross",
          "Repair",
          "FAM-10 Fluid Conditioning Unit",
          "FAM10-998231-A",
          "Waiting for Customer Response",
          "Pending Customer Approval",
          6,
          "Adam K",
          "Inlet Hose, Outlet Hose, Manual",
          "Vacuum pump seal leak identified",
          "F-0101",
          "{}",
          "Quote sent to customer for pump replacement.",
          "",
          "",
          "2026-10-01",
          "2026-10-10",
      ),
      (
          "60083112",
          "20007522",
          "Komatsu Ltd.",
          "Rachel Zane",
          "Calibration",
          "FCU 1310 Portable Filtration",
          "FCU1310-88412-A",
          "Flow Bench",
          "Draining Fluid",
          4,
          "New Guy",
          "Suction Hose, Power Adapter",
          "Residual hydraulic oil present",
          "F-0101",
          "{}",
          "Draining fluid on Flow Bench prior to sensor removal.",
          "",
          "",
          "2026-10-20",
          "",
      ),
      (
          "60083145",
          "20007548",
          "Parker Hannifin",
          "Sarah Jenkins",
          "Calibration",
          "AS 1000 AquaSensor",
          "AS1000-77621-C",
          "Inbound Material",
          "Dropped Off",
          7,
          "Unassigned",
          "Case, Communication Cable",
          "New field return drop off",
          "F-0102",
          "{}",
          "Awaiting SAP work order creation.",
          "",
          "",
          "2026-10-28",
          "",
      ),
  ]

  cursor.executemany(
      """
        INSERT INTO queue (rga_number, notification_number, customer_name, csr_name, service_requested, model_series, serial_number, location, status, urgency, assigned_to, accessories, visual_inspection, eval_form_type, eval_data, notes, photo_path, cal_file_path, date_logged, customer_hold_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
      demo_data,
  )

  conn.commit()
  conn.close()


def build_unit_dropdown_options(df):
  options_map = {}
  if df is None or df.empty:
    return options_map

  for _, row in df.iterrows():
    unit_id = row.get("id", "")
    rga = str(row.get("rga_number", "")).replace("nan", "").strip() or "N/A"
    model = row.get("model_series") or "N/A"
    sn = str(row.get("serial_number", "")).replace("nan", "").strip() or "N/A"
    loc = row.get("location", "Ready for Evaluation")
    assigned = row.get("assigned_to", "Unassigned")

    label = f"RGA: {rga} | {model} | SN: {sn} | Shelf: [{loc}] | Owner: [{assigned}] (ID: {unit_id})"
    options_map[label] = unit_id

  return options_map


# Load current data state
df_queue = load_data()


# =========================================================
# INTERACTIVE MODAL OVERLAYS
# =========================================================
@st.dialog("🖐️ Parent RGA Cascading Assignment")
def modal_claim_unit(rga_number, unit_id, current_owner, model_name, serial_num):
  st.markdown(f"### Assign Parent RGA #{rga_number}")
  st.info(
      f"⚠️ **CASCADING ASSIGNMENT**: Assigning this item will update **ALL child"
      f" units** under RGA **{rga_number}**."
  )
  st.write(
      f"Selected Unit ID #{unit_id} ({model_name} | SN: {serial_num}) | Current"
      f" Owner: **{current_owner}**"
  )

  st.markdown("---")
  c1, c2 = st.columns(2)
  with c1:
    if st.button(
        f"🖐️ Claim All Units ({st.session_state['user_name']})",
        key=f"claim_self_{unit_id}",
        type="primary",
        use_container_width=True,
    ):
      assign_parent_rga_cascade(rga_number, st.session_state["user_name"])
      st.toast(
          f"✅ All units for RGA {rga_number} assigned to"
          f" {st.session_state['user_name']}!",
          icon="🖐️",
      )
      st.rerun()

  with c2:
    target_assignee = st.selectbox(
        "Reassign All Children To:",
        ["Unassigned", "Geo H", "Adam K", "New Guy"],
        key=f"reassign_sel_{unit_id}",
    )
    if st.button(
        "💾 Reassign All Children",
        key=f"reassign_btn_{unit_id}",
        use_container_width=True,
    ):
      assign_parent_rga_cascade(rga_number, target_assignee)
      st.toast(
          f"✅ Reassigned all items under RGA {rga_number} to"
          f" {target_assignee}!",
          icon="👤",
      )
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
      "Upload Defect / Inspection Photo:",
      type=["png", "jpg", "jpeg"],
      key=f"upl_{unit_id}",
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


# =========================================================
# TOP NAVIGATION HEADER & BANNER
# =========================================================
col_logo, col_header, col_logout = st.columns([1, 6, 1.2])
with col_logo:
  if os.path.exists("logo.png"):
    st.image("logo.png", width=110)
  else:
    st.markdown("### ⚡ **HYDAC**")

with col_header:
  st.markdown(
      f"""
    <div class="hydac-banner">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
            <span style="background:rgba(227,6,19,0.35); color:#FFFFFF; border:1px solid #E30613; padding:4px 14px; border-radius:12px; font-size:0.75rem; font-weight:800; text-transform:uppercase;">
                <i class="fa-solid fa-microchip" style="color:#FF8888; margin-right:4px;"></i> HYDAC OS v3.0
            </span>
            <span style="background:rgba(255,255,255,0.18); color:#FFFFFF; padding:4px 14px; border-radius:12px; font-size:0.75rem; font-weight:800;">
                <i class="fa-solid fa-user-shield" style="color:#38BDF8; margin-right:4px;"></i> Active User: {st.session_state['user_name']} ({st.session_state['user_role']})
            </span>
        </div>
        <div class="hydac-title">ELECTRONIC LAB PORTAL</div>
        <div style="font-size:0.92rem; color:#E2E8F0; font-weight:600;">HYDAC Technology Corp — Operations Command, Shelf Tracking & Evaluation System</div>
    </div>
    """,
      unsafe_allow_html=True,
  )

with col_logout:
  st.markdown("<br>", unsafe_allow_html=True)
  if st.button("🔒 Sign Out", use_container_width=True):
    st.session_state["authenticated"] = False
    st.session_state["user_name"] = ""
    st.session_state["user_role"] = ""
    st.rerun()

# Top Navigation Tabs
nav_choice = st.segmented_control(
    "SELECT WORKFLOW MODULE:",
    [
        "🖥️ Operations Queue (TV Display)",
        "📥 Phase 1: Inbound Intake",
        "🔬 Phase 2: Evaluation & Testing",
        "⏱️ Waiting for Customer (30-Day Tracker)",
        "🛠️ System Admin & Tools",
    ],
    default="🖥️ Operations Queue (TV Display)",
)

df_queue = load_data()


# =========================================================
# MODULE 1: OPERATIONS QUEUE (DEFAULT TV DISPLAY)
# =========================================================
if nav_choice == "🖥️ Operations Queue (TV Display)":
  if df_queue.empty:
    st.warning(
        "No active unit records found in database. Go to **System Admin &"
        " Tools** to populate demo data!"
    )
  else:
    # Summary Metrics across shelves
    inbound_cnt = (df_queue["location"] == "Inbound Material").sum()
    ready_cnt = (df_queue["location"] == "Ready for Evaluation").sum()
    waiting_cnt = (
        df_queue["location"] == "Waiting for Customer Response"
    ).sum()
    bench_cnt = df_queue["location"].isin(["Flow Bench", "CalRig"]).sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Inbound Drop-off", inbound_cnt)
    m2.metric("Ready for Eval Shelf", ready_cnt)
    m3.metric("Waiting for Customer", waiting_cnt)
    m4.metric("Active Bench / CalRig", bench_cnt)

    st.markdown("---")

    # Search & Shelf Filter
    c_search, c_shelf = st.columns([3, 1])
    search_term = c_search.text_input(
        "🔍 SEARCH QUEUE (RGA, CUSTOMER, MODEL, S/N):",
        placeholder="Type RGA, Serial Number, or Customer Name...",
    )
    shelf_filter = c_shelf.selectbox(
        "FILTER BY SHELF LOCATION",
        [
            "All Shelves",
            "Inbound Material",
            "Ready for Evaluation",
            "Waiting for Customer Response",
            "Flow Bench",
            "CalRig",
            "Completed / Ready for Shipping",
        ],
    )

    filtered_df = df_queue.copy()
    if shelf_filter != "All Shelves":
      filtered_df = filtered_df[filtered_df["location"] == shelf_filter]

    if search_term:
      filter_mask = filtered_df.astype(str).apply(
          lambda col: col.str.contains(search_term, case=False)
      ).any(axis=1)
      filtered_df = filtered_df[filter_mask]

    st.markdown("### 📋 Active Requests & Shelf Overview")

    # Parent RGA Grouping
    parent_groups = filtered_df.groupby("rga_number")

    for rga, group in parent_groups:
      cust_name = group["customer_name"].iloc[0] or "N/A"
      csr_name = group.get("csr_name", pd.Series(["N/A"])).iloc[0] or "N/A"
      item_count = len(group)
      assignees = ", ".join(group["assigned_to"].unique())

      expander_header = f"Parent RGA: {rga}  |  Customer: {cust_name}  |  CSR: {csr_name}  |  {item_count} Child Unit(s)  |  Owner: [{assignees}]"

      with st.expander(expander_header, expanded=True):
        for _, child in group.iterrows():
          c_info, c_location, c_actions = st.columns([2.5, 1.8, 1.7])

          loc_str = child.get("location", "Ready for Evaluation")

          # Shelf Badges
          if loc_str == "Inbound Material":
            badge_html = (
                '<span class="badge-inbound"><i class="fa-solid'
                ' fa-truck-ramp-box"></i> Inbound Material</span>'
            )
          elif loc_str == "Ready for Evaluation":
            badge_html = (
                '<span class="badge-ready"><i class="fa-solid'
                ' fa-clipboard-check"></i> Ready for Evaluation</span>'
            )
          elif loc_str == "Waiting for Customer Response":
            days_left = child.get("days_remaining_hold", 30)
            badge_html = (
                f'<span class="badge-waiting"><i class="fa-solid fa-clock"></i>'
                f" Waiting Customer ({days_left} Days Left)</span>"
            )
          elif loc_str == "Flow Bench":
            badge_html = (
                '<span class="badge-flow"><i class="fa-solid'
                ' fa-faucet-drip"></i> Flow Bench</span>'
            )
          elif loc_str == "CalRig":
            badge_html = (
                '<span class="badge-calrig"><i class="fa-solid'
                ' fa-microchip"></i> CalRig</span>'
            )
          else:
            badge_html = (
                '<span class="badge-completed"><i class="fa-solid'
                ' fa-boxes-packing"></i> Ready for Shipping</span>'
            )

          with c_info:
            st.markdown(f"##### ⚙️ Unit ID #{child['id']}")
            st.write(
                f"**Model Series:** `{child.get('model_series', 'N/A')}`\n\n"
                f"**Serial Number:** `{child.get('serial_number', 'N/A')}`\n\n"
                f"**Requested Service:** `{child.get('service_requested', 'Calibration')}`"
                f" | **Owner:** `{child.get('assigned_to', 'Unassigned')}`"
            )

          with c_location:
            st.markdown("##### 📍 Location / Shelf")
            st.markdown(f"Current Shelf: {badge_html}", unsafe_allow_html=True)
            st.write(f"**Status:** `{child.get('status', 'Received')}`")

            # Quick Location Move Dropdown
            new_shelf = st.selectbox(
                "Move to Shelf:",
                [
                    "Inbound Material",
                    "Ready for Evaluation",
                    "Flow Bench",
                    "CalRig",
                    "Waiting for Customer Response",
                    "Completed / Ready for Shipping",
                ],
                index=[
                    "Inbound Material",
                    "Ready for Evaluation",
                    "Flow Bench",
                    "CalRig",
                    "Waiting for Customer Response",
                    "Completed / Ready for Shipping",
                ].index(loc_str)
                if loc_str in [
                    "Inbound Material",
                    "Ready for Evaluation",
                    "Flow Bench",
                    "CalRig",
                    "Waiting for Customer Response",
                    "Completed / Ready for Shipping",
                ]
                else 1,
                key=f"shelf_move_{child['id']}",
            )
            if new_shelf != loc_str:
              if st.button("Move Shelf", key=f"btn_move_{child['id']}"):
                update_location_and_status(child["id"], new_shelf)
                st.toast(
                    f"Moved Unit #{child['id']} to {new_shelf}", icon="📍"
                )
                st.rerun()

          with c_actions:
            st.markdown("##### ⚡ Quick Actions")
            btn1, btn2 = st.columns(2)

            with btn1:
              if st.button("🖐️ Assign RGA", key=f"btn_claim_{child['id']}"):
                modal_claim_unit(
                    child["rga_number"],
                    child["id"],
                    child.get("assigned_to", "Unassigned"),
                    child.get("model_series", "N/A"),
                    child.get("serial_number", "N/A"),
                )

            with btn2:
              if st.button("📷 Photos", key=f"btn_photo_{child['id']}"):
                modal_manage_photo(child["id"], child.get("photo_path", ""))

          st.divider()

# =========================================================
# MODULE 2: PHASE 1 INBOUND INTAKE
# =========================================================
elif nav_choice == "📥 Phase 1: Inbound Intake":
  st.subheader("📥 Phase 1: Inbound Material Intake (Shipping Drop-Off)")
  st.info(
      "Collect initial package details here upon arrival at the **Inbound"
      " Material** shelf prior to SAP processing."
  )

  intake_qty = st.radio(
      "Intake Type:",
      ["Single Unit Intake", "Multiple Units (Batch under same RGA)"],
      horizontal=True,
  )

  with st.form("phase1_intake_form"):
    c1, c2, c3 = st.columns(3)
    p1_rga = c1.text_input("Parent RGA Number*:")
    p1_notif = c2.text_input("Notification Number:")
    p1_cust = c3.text_input("Customer Name*:")

    c4, c5 = st.columns(2)
    p1_csr = c4.text_input("Customer Service Rep (CSR):")
    p1_service = c5.selectbox(
        "Requested Service*:", ["Calibration", "Repair", "Warranty Evaluation"]
    )

    st.markdown("##### 📦 Received Accessories Checklist")
    acc_cols = st.columns(5)
    acc_case = acc_cols[0].checkbox("Case")
    acc_inlet = acc_cols[1].checkbox("Inlet Hose")
    acc_outlet = acc_cols[2].checkbox("Outlet Hose")
    acc_suction = acc_cols[3].checkbox("Suction Hose")
    acc_comm = acc_cols[4].checkbox("Communication Cable")

    acc_cols2 = st.columns(5)
    acc_cd = acc_cols2[0].checkbox("CD / Floppy")
    acc_paper = acc_cols2[1].checkbox("Paper Roll")
    acc_ribbon = acc_cols2[2].checkbox("Ink Ribbon")
    acc_power = acc_cols2[3].checkbox("Power Adapter")
    acc_manual = acc_cols2[4].checkbox("Manual")

    st.markdown("---")

    if intake_qty == "Single Unit Intake":
      c6, c7 = st.columns(2)
      p1_model = c6.text_input("Model Series / Description*:")
      p1_sn = c7.text_input("Serial Number*:")
      p1_visual = st.text_area("External Visual Inspection Notes:")
      p1_assign = st.selectbox(
          "Initial Technician Assignment (Optional):",
          ["Unassigned", "Geo H", "Adam K", "New Guy"],
      )

      if st.form_submit_button(
          "🚀 Complete Intake & Move to Ready Shelf", type="primary"
      ):
        if p1_rga and p1_cust and p1_model and p1_sn:
          # Build accessories list
          accessories_list = []
          if acc_case:
            accessories_list.append("Case")
          if acc_inlet:
            accessories_list.append("Inlet Hose")
          if acc_outlet:
            accessories_list.append("Outlet Hose")
          if acc_suction:
            accessories_list.append("Suction Hose")
          if acc_comm:
            accessories_list.append("Communication Cable")
          if acc_cd:
            accessories_list.append("CD/Floppy")
          if acc_paper:
            accessories_list.append("Paper Roll")
          if acc_ribbon:
            accessories_list.append("Ink Ribbon")
          if acc_power:
            accessories_list.append("Power Adapter")
          if acc_manual:
            accessories_list.append("Manual")

          acc_str = ", ".join(accessories_list) if accessories_list else "None"

          conn = sqlite3.connect(DB_FILE)
          cursor = conn.cursor()
          cursor.execute(
              """
                        INSERT INTO queue (rga_number, notification_number, customer_name, csr_name, service_requested, model_series, serial_number, location, status, urgency, assigned_to, accessories, visual_inspection, date_logged)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'Ready for Evaluation', 'Received in Lab', 5, ?, ?, ?, ?)
                    """,
              (
                  p1_rga,
                  p1_notif,
                  p1_cust,
                  p1_csr,
                  p1_service,
                  p1_model,
                  p1_sn,
                  p1_assign,
                  acc_str,
                  p1_visual,
                  datetime.now().strftime("%Y-%m-%d"),
              ),
          )
          conn.commit()
          conn.close()
          st.toast(
              f"✅ Unit RGA {p1_rga} intake logged & moved to Ready for"
              " Evaluation shelf!",
              icon="🚀",
          )
        else:
          st.error(
              "Please fill in all required fields (RGA, Customer, Model, Serial"
              " Number)."
          )

    else:  # Batch intake
      p1_model = st.text_input("Model Series / Description*:")
      batch_sns = st.text_area(
          "Child Serial Numbers* (Enter one serial number per line):"
      )
      p1_visual = st.text_area("External Visual Inspection Notes:")
      p1_assign = st.selectbox(
          "Initial Technician Assignment (Optional):",
          ["Unassigned", "Geo H", "Adam K", "New Guy"],
      )

      if st.form_submit_button(
          "🚀 Process Batch Intake & Move to Ready Shelf", type="primary"
      ):
        sn_list = [s.strip() for s in batch_sns.split("\n") if s.strip()]
        if p1_rga and p1_cust and p1_model and sn_list:
          accessories_list = []
          if acc_case:
            accessories_list.append("Case")
          if acc_inlet:
            accessories_list.append("Inlet Hose")
          if acc_outlet:
            accessories_list.append("Outlet Hose")
          if acc_suction:
            accessories_list.append("Suction Hose")
          if acc_comm:
            accessories_list.append("Communication Cable")
          if acc_cd:
            accessories_list.append("CD/Floppy")
          if acc_paper:
            accessories_list.append("Paper Roll")
          if acc_ribbon:
            accessories_list.append("Ink Ribbon")
          if acc_power:
            accessories_list.append("Power Adapter")
          if acc_manual:
            accessories_list.append("Manual")

          acc_str = ", ".join(accessories_list) if accessories_list else "None"
          today_str = datetime.now().strftime("%Y-%m-%d")

          conn = sqlite3.connect(DB_FILE)
          cursor = conn.cursor()
          for sn in sn_list:
            cursor.execute(
                """
                            INSERT INTO queue (rga_number, notification_number, customer_name, csr_name, service_requested, model_series, serial_number, location, status, urgency, assigned_to, accessories, visual_inspection, date_logged)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 'Ready for Evaluation', 'Received in Lab', 5, ?, ?, ?, ?)
                        """,
                (
                    p1_rga,
                    p1_notif,
                    p1_cust,
                    p1_csr,
                    p1_service,
                    p1_model,
                    sn,
                    p1_assign,
                    acc_str,
                    p1_visual,
                    today_str,
                ),
            )
          conn.commit()
          conn.close()
          st.toast(
              f"✅ Batch logged {len(sn_list)} items under RGA {p1_rga}!",
              icon="📦",
          )
        else:
          st.error(
              "Please fill in RGA, Customer, Model, and at least one Serial"
              " Number."
          )

# =========================================================
# MODULE 3: PHASE 2 EVALUATION & TESTING (FORMS F-0100 - F-0103)
# =========================================================
elif nav_choice == "🔬 Phase 2: Evaluation & Testing":
  st.subheader("🔬 Phase 2: Evaluation & Bench Testing Sheet")
  st.info(
      "Pull a unit off the shelf (`Ready for Evaluation`, `Flow Bench`, or"
      " `CalRig`) to complete its evaluation sheet (F-0100 – F-0103), log test"
      " notes, and attach calibration data."
  )

  if df_queue.empty:
    st.warning("No units in database.")
  else:
    unit_map = build_unit_dropdown_options(df_queue)
    sel_label = st.selectbox(
        "Select Unit Off the Shelf to Evaluate:", options=list(unit_map.keys())
    )
    sel_id = unit_map[sel_label]
    sel_row = df_queue[df_queue["id"] == sel_id].iloc[0]

    st.markdown("---")
    st.markdown(
        f"#### ⚙️ Unit #{sel_row['id']} — RGA: {sel_row['rga_number']} | SN:"
        f" {sel_row['serial_number']}"
    )
    st.write(
        f"**Customer:** {sel_row['customer_name']} | **Model:**"
        f" {sel_row['model_series']} | **Current Shelf:**"
        f" `{sel_row['location']}` | **Accessories:** `{sel_row.get('accessories', 'None')}`"
    )

    form_type = st.selectbox(
        "Select Evaluation Form Template:",
        [
            "F-0100: Contamination Sensors (CS 1000 / CS 2000)",
            "F-0101: Fluid Conditioning Units (FAM / FCU)",
            "F-0102: AquaSensors (AS 1000 / AS 3000)",
            "F-0103: General Electronic Bench & Cal Sheet",
        ],
    )

    with st.form("eval_form_sheet"):
      st.markdown(f"### {form_type.split(':')[0]} Evaluation Protocol")

      col_e1, col_e2 = st.columns(2)
      diode_test = col_e1.selectbox(
          "Laser Diode / Sensor Bench Test:", ["Pass", "Fail", "N/A"]
      )
      calibration_status = col_e2.selectbox(
          "Calibration Alignment:",
          ["In Spec", "Out of Spec - Recalibrated", "Hardware Defect"],
      )

      col_e3, col_e4 = st.columns(2)
      fluid_check = col_e3.text_input(
          "Operating Pressure / Flow Rate:", value="100 bar / 1.5 L/min"
      )
      voltage_check = col_e4.text_input(
          "Supply Voltage Check:", value="24V DC Nominal"
      )

      eval_notes = st.text_area(
          "Diagnostic Findings / Tech Notes:",
          value=str(sel_row.get("notes", "") or ""),
      )

      st.markdown("##### 📁 Upload CalRig Calibration Data File")
      cal_file = st.file_uploader(
          "Attach CalRig XML / Data File:",
          type=["xml", "csv", "txt", "pdf"],
          key=f"cal_file_{sel_id}",
      )

      st.markdown("---")
      st.markdown("##### 🏁 Evaluation Outcome & Shelf Routing")
      outcome_choice = st.radio(
          "Select Next Action:",
          [
              "Keep on CalRig / Flow Bench",
              "Requires Customer Repair Approval (Move to Waiting Shelf)",
              "Calibration Complete (Move to Ready for Shipping)",
          ],
      )

      if st.form_submit_button(
          "💾 Save Evaluation & Route Unit", type="primary"
      ):
        # Save CalRig file if uploaded
        cal_path_saved = sel_row.get("cal_file_path", "")
        if cal_file:
          cal_filename = f"Cal_{sel_id}_{cal_file.name}"
          cal_path_saved = os.path.join(LOCAL_CERTS_DIR, cal_filename)
          with open(cal_path_saved, "wb") as f:
            f.write(cal_file.getbuffer())

        # Determine target shelf and status
        if "Waiting Shelf" in outcome_choice:
          target_shelf = "Waiting for Customer Response"
          target_status = "Pending Customer Approval"
        elif "Ready for Shipping" in outcome_choice:
          target_shelf = "Completed / Ready for Shipping"
          target_status = "Calibrated & Completed"
        else:
          target_shelf = sel_row["location"]
          target_status = "Under Testing"

        # Save eval details into database
        eval_dict = {
            "diode_test": diode_test,
            "calibration_status": calibration_status,
            "fluid_check": fluid_check,
            "voltage_check": voltage_check,
        }

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        today_str = datetime.now().strftime("%Y-%m-%d")
        if target_shelf == "Waiting for Customer Response":
          cursor.execute(
              """
                        UPDATE queue SET eval_form_type=?, eval_data=?, notes=?, cal_file_path=?, location=?, status=?, customer_hold_date=?
                        WHERE id=?
                    """,
              (
                  form_type.split(":")[0],
                  json.dumps(eval_dict),
                  eval_notes,
                  cal_path_saved,
                  target_shelf,
                  target_status,
                  today_str,
                  sel_id,
              ),
          )
        else:
          cursor.execute(
              """
                        UPDATE queue SET eval_form_type=?, eval_data=?, notes=?, cal_file_path=?, location=?, status=?
                        WHERE id=?
                    """,
              (
                  form_type.split(":")[0],
                  json.dumps(eval_dict),
                  eval_notes,
                  cal_path_saved,
                  target_shelf,
                  target_status,
                  sel_id,
              ),
          )

        conn.commit()
        conn.close()

        st.toast(
            f"✅ Saved evaluation for Unit #{sel_id}! Routed to"
            f" {target_shelf}.",
            icon="🔬",
        )
        st.rerun()

# =========================================================
# MODULE 4: WAITING FOR CUSTOMER (30-DAY COUNTDOWN TRACKER)
# =========================================================
elif nav_choice == "⏱️ Waiting for Customer (30-Day Tracker)":
  st.subheader("⏱️ Customer Response & Approval Tracker (30-Day Limit)")
  st.info(
      "Units sitting on the **Waiting for Customer Response** shelf undergo an"
      " automated **30-day countdown** to follow up on repair approvals."
  )

  waiting_df = df_queue[
      df_queue["location"] == "Waiting for Customer Response"
  ]

  if waiting_df.empty:
    st.success(
        "🎉 No units currently sitting on the Waiting for Customer Response"
        " shelf!"
    )
  else:
    for _, row in waiting_df.iterrows():
      days_remaining = row.get("days_remaining_hold", 30)

      if days_remaining <= 5:
        urgency_badge = (
            f'<span class="badge-critical"><i class="fa-solid'
            f' fa-triangle-exclamation"></i> OVERDUE / URGENT ({days_remaining}'
            " Days Remaining)</span>"
        )
      else:
        urgency_badge = (
            f'<span class="badge-waiting"><i class="fa-solid fa-clock"></i>'
            f" {days_remaining} Days Remaining</span>"
        )

      with st.container(border=True):
        c_w1, c_w2, c_w3 = st.columns([2.5, 1.5, 1])

        with c_w1:
          st.markdown(
              f"##### ⚙️ Unit #{row['id']} — RGA: {row['rga_number']} |"
              f" Customer: {row['customer_name']}"
          )
          st.write(
              f"**Model:** `{row['model_series']}` | **SN:**"
              f" `{row['serial_number']}`\n\n**Notes:** {row.get('notes', 'N/A')}"
          )

        with c_w2:
          st.markdown("##### ⏱️ Countdown Status")
          st.markdown(urgency_badge, unsafe_allow_html=True)
          st.caption(
              f"Hold Started: {row.get('customer_hold_date', 'Recent')}"
          )

        with c_w3:
          st.markdown("##### ⚡ Resolve Hold")
          if st.button("✅ Approval Received", key=f"appr_{row['id']}"):
            update_location_and_status(
                row["id"], "Flow Bench", "Approved - Under Repair"
            )
            st.toast("Customer approved! Moved to Flow Bench.", icon="✅")
            st.rerun()

          if st.button("📦 Return Unrepaired", key=f"ret_{row['id']}"):
            update_location_and_status(
                row["id"], "Completed / Ready for Shipping", "Returned As-Is"
            )
            st.toast("Moved to Ready for Shipping.", icon="📦")
            st.rerun()

# =========================================================
# MODULE 5: SYSTEM ADMIN & DEMO RESET
# =========================================================
else:
  st.subheader("🛠️ System Admin & Database Seeding Tools")

  c_seed, c_export = st.columns(2)
  with c_seed:
    with st.container(border=True):
      st.markdown("#### 🔄 Reset & Seed Demo Records")
      st.caption(
          "Wipes and populates realistic demo units across all physical shelves"
          " (Inbound, Ready, Flow Bench, CalRig, Waiting)."
      )
      if st.button("🌱 Execute Database Reset", type="primary"):
        reset_and_seed_db()
        st.cache_data.clear()
        st.toast("Database re-seeded with demo records!", icon="🌱")
        st.rerun()

  with c_export:
    with st.container(border=True):
      st.markdown("#### 📥 Backup & Excel Export")
      if not df_queue.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
          df_queue.to_excel(writer, index=False, sheet_name="Lab Queue")
        excel_bytes = output.getvalue()

        st.download_button(
            label="📥 Download Excel Report (.xlsx)",
            data=excel_bytes,
            file_name="lab_queue_export.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            use_container_width=True,
        )