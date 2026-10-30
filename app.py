import io
import json
import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# =========================================================
# PAGE CONFIGURATION & FLOATING LIGHT THEME STYLING
# =========================================================
st.set_page_config(
    page_title="HYDAC Electronic Lab Portal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "lab_queue.db"
LOCAL_CERTS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Certs"
UPLOADS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Uploads"

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(LOCAL_CERTS_DIR, exist_ok=True)

# High-Contrast Light Executive CSS
st.markdown(
    """
    <style>
    /* Light Canvas Base */
    .stApp {
        background-color: #F1F5F9 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        color: #0F172A !important;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 96%;
    }

    /* LEFT SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 2px solid #1E293B !important;
    }

    section[data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }

    section[data-testid="stSidebar"] .stRadio label {
        background-color: #1E293B !important;
        padding: 10px 14px !important;
        border-radius: 8px !important;
        margin-bottom: 6px !important;
        border: 1px solid #334155 !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
    }

    /* HEADERS & TYPOGRAPHY */
    h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #0F172A !important;
        font-weight: 800 !important;
        letter-spacing: -0.3px !important;
    }

    p, span, label, div {
        color: #1E293B !important;
    }

    /* FORM & FILTER WIDGET LABELS */
    label[data-testid="stWidgetLabel"] p, .stWidgetLabel p {
        color: #0284C7 !important;
        font-weight: 800 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }

    /* INPUT FIELDS & DROPDOWNS */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 2px solid #94A3B8 !important;
        border-radius: 8px !important;
        color: #0F172A !important;
    }

    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
        color: #0F172A !important;
        font-weight: 600 !important;
        font-size: 0.98rem !important;
    }

    /* KPI METRIC CARDS */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 2px solid #CBD5E1 !important;
        border-top: 4px solid #E30613 !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05) !important;
    }

    div[data-testid="stMetricValue"] div {
        color: #0F172A !important;
        font-size: 2.3rem !important;
        font-weight: 900 !important;
    }

    div[data-testid="stMetricLabel"] div {
        color: #475569 !important;
        font-size: 0.8rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
    }

    /* FLOATING EXPANDER CARDS (PARENT RGA) */
    details[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 2px solid #CBD5E1 !important;
        border-radius: 12px !important;
        margin-bottom: 18px !important;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06) !important;
        overflow: hidden !important;
    }

    summary[data-testid="stExpanderSummary"] {
        background-color: #F8FAFC !important;
        border-left: 8px solid #E30613 !important;
        padding: 16px 22px !important;
    }

    summary[data-testid="stExpanderSummary"] p, summary[data-testid="stExpanderSummary"] span {
        color: #0F172A !important;
        font-size: 1.15rem !important;
        font-weight: 900 !important;
    }

    /* LINE ITEM FLOATING CARDS */
    .child-card {
        background-color: #FFFFFF !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 18px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    }

    .child-card p, .child-card span, .child-card div, .child-card label {
        color: #0F172A !important;
    }

    .child-card strong {
        color: #0F172A !important;
        font-weight: 800 !important;
    }

    /* STATUS BADGES */
    .pill-green {
        background-color: #DCFCE7 !important;
        color: #15803D !important;
        border: 1.5px solid #16A34A !important;
        padding: 5px 14px !important;
        border-radius: 20px !important;
        font-weight: 800 !important;
        font-size: 0.82rem !important;
        display: inline-block !important;
    }

    .pill-yellow {
        background-color: #FEF9C3 !important;
        color: #A16207 !important;
        border: 1.5px solid #CA8A04 !important;
        padding: 5px 14px !important;
        border-radius: 20px !important;
        font-weight: 800 !important;
        font-size: 0.82rem !important;
        display: inline-block !important;
    }

    .pill-red {
        background-color: #FEE2E2 !important;
        color: #B91C1C !important;
        border: 1.5px solid #DC2626 !important;
        padding: 5px 14px !important;
        border-radius: 20px !important;
        font-weight: 800 !important;
        font-size: 0.82rem !important;
        display: inline-block !important;
    }

    /* BUTTONS */
    div.stButton > button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border: 1px solid #0F172A !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
    }

    div.stButton > button[kind="primary"] {
        background-color: #E30613 !important;
        color: #FFFFFF !important;
        border: 1px solid #B91C1C !important;
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
    "geo.h": {"password": "HYDAC2026", "name": "Geo H", "role": "Lab Technician"},
    "adam.k": {"password": "HYDAC2026", "name": "Adam K", "role": "Supervisor"},
    "new.guy": {"password": "HYDAC2026", "name": "New Guy", "role": "Lab Technician"},
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
            pass_input = st.text_input("Password:", type="password", key="auth_pass")

            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if st.button("🔓 Sign In", type="primary", use_container_width=True):
                    u_clean = user_input.strip().lower()
                    if u_clean in VALID_USERS and VALID_USERS[u_clean]["password"] == pass_input.strip():
                        st.session_state["authenticated"] = True
                        st.session_state["user_name"] = VALID_USERS[u_clean]["name"]
                        st.session_state["user_role"] = VALID_USERS[u_clean]["role"]
                        st.toast(f"Welcome back, {st.session_state['user_name']}!", icon="⚡")
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password.")

            with b_col2:
                if st.button("🚀 Quick Login (Geo H)", use_container_width=True):
                    st.session_state["authenticated"] = True
                    st.session_state["user_name"] = "Geo H"
                    st.session_state["user_role"] = "Lab Technician"
                    st.toast("Authenticated as Geo H (Lab Technician)", icon="🚀")
                    st.rerun()

            st.caption("Authorized Accounts:")
            st.caption("• Geo H (Lab Tech): `geo.h` / `HYDAC2026`")
            st.caption("• Adam K (Supervisor): `adam.k` / `HYDAC2026`")
            st.caption("• New Guy (Lab Tech): `new.guy` / `HYDAC2026`")
    st.stop()

# =========================================================
# DATABASE MIGRATIONS & PIPELINE
# =========================================================
def init_db():
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
    existing_cols = [col[1] for col in cursor.fetchall()]

    needed_cols = {
        "rga_number": "TEXT",
        "notification_number": "TEXT",
        "customer_name": "TEXT",
        "csr_name": "TEXT",
        "service_requested": "TEXT DEFAULT 'Calibration'",
        "model_series": "TEXT",
        "serial_number": "TEXT",
        "location": "TEXT DEFAULT 'Ready for Evaluation'",
        "status": "TEXT DEFAULT 'Received in Lab'",
        "urgency": "INTEGER DEFAULT 5",
        "assigned_to": "TEXT DEFAULT 'Unassigned'",
        "accessories": "TEXT",
        "visual_inspection": "TEXT",
        "eval_form_type": "TEXT",
        "eval_data": "TEXT",
        "notes": "TEXT",
        "photo_path": "TEXT",
        "cal_file_path": "TEXT",
        "date_logged": "TEXT",
        "customer_hold_date": "TEXT",
    }

    for col_name, col_type in needed_cols.items():
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE queue ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass

    conn.commit()
    conn.close()

def load_data():
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

        def calc_status(row):
            weeks = row["age_weeks"]
            if weeks < 4:
                return "GREEN"
            elif weeks <= 7:
                return "YELLOW"
            else:
                return "RED"

        df["timeframe_status"] = df.apply(calc_status, axis=1)

        def calc_hold_days(row):
            if row["location"] == "Waiting for Customer Response" and row.get("customer_hold_date") and str(row["customer_hold_date"]).strip() != "":
                try:
                    hold_start = datetime.strptime(str(row["customer_hold_date"]), "%Y-%m-%d")
                    days_waiting = (now - hold_start).days
                    return max(0, 30 - days_waiting)
                except Exception:
                    return 30
            return 30

        df["days_remaining_hold"] = df.apply(calc_hold_days, axis=1)

    return df

def assign_parent_rga_cascade(rga_number, new_assignee):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE queue SET assigned_to=? WHERE rga_number=?", (new_assignee, rga_number))
    conn.commit()
    conn.close()

def update_location_and_status(unit_id, new_location, new_status=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")

    if new_location == "Waiting for Customer Response":
        cursor.execute("UPDATE queue SET location=?, customer_hold_date=? WHERE id=?", (new_location, today_str, unit_id))
    else:
        cursor.execute("UPDATE queue SET location=? WHERE id=?", (new_location, unit_id))

    if new_status:
        cursor.execute("UPDATE queue SET status=? WHERE id=?", (new_status, unit_id))

    conn.commit()
    conn.close()

def reset_and_seed_db():
    """REBUILT SEEDER: Populates a comprehensive set of demo records utilizing all new schema fields."""
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

    today = datetime.now()
    d_fresh = (today - timedelta(days=6)).strftime("%Y-%m-%d")
    d_warn = (today - timedelta(days=32)).strftime("%Y-%m-%d")
    d_late = (today - timedelta(days=62)).strftime("%Y-%m-%d")

    demo_data = [
        # Parent RGA 60083000 (Caterpillar - Fresh)
        ("60083000", "20007503", "Caterpillar Inc.", "Sarah Jenkins", "Calibration", "CS 1000 Contamination Sensor", "000SS01831K0000001", "CalRig", "Under Calibration", 9, "Geo H", "Case, Power Adapter, Comm Cable", "Clean exterior, optical ports clear", "F-0100", "{\"diode\":\"Pass\",\"alignment\":\"In Spec\"}", "[2026-10-24 - Geo H]: Diode bench synced. Calibration underway.", "[]", "", d_fresh, ""),
        ("60083000", "20007503", "Caterpillar Inc.", "Sarah Jenkins", "Calibration", "CS 1000 Contamination Sensor", "000SS01831K0000002", "CalRig", "Under Calibration", 9, "Geo H", "Case, Power Adapter", "Diode port inspected", "F-0100", "{\"diode\":\"Pass\",\"alignment\":\"In Spec\"}", "[2026-10-24 - Geo H]: Zero offset verified.", "[]", "", d_fresh, ""),
        ("60083000", "20007503", "Caterpillar Inc.", "Sarah Jenkins", "Repair", "CS 1000 Contamination Sensor", "000SS01831K0000003", "Ready for Evaluation", "Received in Lab", 9, "Geo H", "Case", "Minor housing scuffing", "F-0100", "{}", "[2026-10-25 - Sarah Jenkins]: Customer requests fast turnaround.", "[]", "", d_fresh, ""),
        
        # Parent RGA 60083105 (John Deere - Approaching SLA)
        ("60083105", "20007510", "John Deere Corp.", "Mike Ross", "Repair", "FAM-10 Fluid Conditioning Unit", "FAM10-998231-A", "Waiting for Customer Response", "Pending Customer Approval", 6, "Adam K", "Inlet Hose, Outlet Hose, Manual", "Vacuum pump seal oil leakage noticed", "F-0101", "{\"pump\":\"Fail\"}", "[2026-10-02 - Adam K]: Quote sent to CSR Mike Ross for customer approval.\n\n[✉️ OUTLOOK SYNC - 2026-10-15 by Adam K]: Customer requested revised quote breakdown.", "[]", "", d_warn, d_warn),
        
        # Parent RGA 60082990 (Komatsu - Late)
        ("60082990", "20007480", "Komatsu Ltd.", "Rachel Zane", "Calibration", "FCU 1310 Portable Filtration", "FCU1310-88412-A", "Flow Bench", "Overdue - Urgent", 10, "New Guy", "Suction Hose, Power Adapter", "Heavy hydraulic oil accumulation inside casing", "F-0101", "{}", "[2026-08-28 - New Guy]: Unit delayed > 8 weeks awaiting bench adapter.\n\n[✉️ OUTLOOK SYNC - 2026-09-10 by Rachel Zane]: Customer inquired on delivery date.", "[]", "", d_late, ""),
        
        # Parent RGA 60083145 (Parker Hannifin - Inbound)
        ("60083145", "20007548", "Parker Hannifin", "Sarah Jenkins", "Calibration", "AS 1000 AquaSensor", "AS1000-77621-C", "Inbound Material", "Dropped Off", 5, "Unassigned", "Case, Comm Cable", "Original field return packaging intact", "F-0102", "{}", "[2026-10-28 - Geo H]: Package received at shipping dock shelf.", "[]", "", d_fresh, ""),
        
        # Parent RGA 60083200 (Volvo CE - Ready Shelf)
        ("60083200", "20007601", "Volvo Construction Equip.", "Mike Ross", "Warranty Evaluation", "AS 3000 AquaSensor", "AS3000-99120-B", "Ready for Evaluation", "Received in Lab", 7, "Unassigned", "Case, Manual", "Intact seal, moisture error reported", "F-0102", "{}", "[2026-10-22 - Mike Ross]: Warranty evaluation log opened.", "[]", "", d_fresh, ""),
        
        # Parent RGA 60083222 (Liebherr - Shipping Ready)
        ("60083222", "20007630", "Liebherr Mining", "Rachel Zane", "Calibration", "CS 2000 Contamination Sensor", "000SS02100K0000088", "Completed / Ready for Shipping", "Calibrated & Completed", 4, "Geo H", "Case, Power Adapter, Comm Cable", "Fully cleaned and re-sealed", "F-0100", "{\"diode\":\"Pass\",\"alignment\":\"In Spec\"}", "[2026-10-26 - Geo H]: Final calibration certificate generated. Ready for shipping dock.", "[]", "", d_fresh, ""),
    ]

    cursor.executemany("""
        INSERT INTO queue (
            rga_number, notification_number, customer_name, csr_name, service_requested,
            model_series, serial_number, location, status, urgency,
            assigned_to, accessories, visual_inspection, eval_form_type, eval_data,
            notes, photo_path, cal_file_path, date_logged, customer_hold_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, demo_data)

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

# =========================================================
# MODAL DIALOG OVERLAYS
# =========================================================
@st.dialog("📷 Inspection Photo Hub")
def modal_photos(unit_id, photo_json):
    st.markdown(f"### Unit #{unit_id} Photos")
    try:
        photos = json.loads(photo_json) if photo_json else []
    except Exception:
        photos = [photo_json] if photo_json else []

    if photos:
        cols = st.columns(3)
        for idx, p in enumerate(photos):
            if os.path.exists(p):
                cols[idx % 3].image(p, caption=f"Photo #{idx+1}", use_container_width=True)
    else:
        st.info("No attached photos found.")

    st.markdown("---")
    uploaded = st.file_uploader("Upload Inspection Photos:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    if uploaded:
        paths = []
        for file in uploaded:
            fpath = os.path.join(UPLOADS_DIR, f"Unit_{unit_id}_{file.name}")
            with open(fpath, "wb") as f:
                f.write(file.getbuffer())
            paths.append(fpath)
        
        all_photos = photos + paths
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE queue SET photo_path=? WHERE id=?", (json.dumps(all_photos), unit_id))
        conn.commit()
        conn.close()
        st.toast("Photos updated!", icon="📷")
        st.rerun()

@st.dialog("💬 Diagnostic Notes & Outlook Sync")
def modal_notes(unit_id, current_notes):
    st.markdown(f"### Unit #{unit_id} Diagnostic History")
    st.text_area("Log History:", value=current_notes or "No existing notes.", height=160, disabled=True)

    t1, t2 = st.tabs(["💬 Add Lab Note", "✉️ Sync Outlook Email"])
    with t1:
        note = st.text_input("New Note:")
        if st.button("Append Note", type="primary", use_container_width=True):
            if note:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                updated = f"{current_notes or ''}\n[{ts} - {st.session_state['user_name']}]: {note.strip()}"
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("UPDATE queue SET notes=? WHERE id=?", (updated, unit_id))
                conn.commit()
                conn.close()
                st.rerun()

    with t2:
        email_body = st.text_area("Paste Email Text:")
        if st.button("Sync Email Note", use_container_width=True):
            if email_body:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                updated = f"{current_notes or ''}\n\n[✉️ OUTLOOK SYNC - {ts} by {st.session_state['user_name']}]:\n{email_body.strip()}"
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("UPDATE queue SET notes=? WHERE id=?", (updated, unit_id))
                conn.commit()
                conn.close()
                st.rerun()

@st.dialog("🖐️ Parent RGA Cascading Assignment")
def modal_claim(rga_number, unit_id, current_owner):
    st.markdown(f"### Assign Parent RGA #{rga_number}")
    st.info(f"Assigning this item will update **ALL child units** under RGA **{rga_number}**.")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button(f"🖐️ Claim Self ({st.session_state['user_name']})", type="primary", use_container_width=True):
            assign_parent_rga_cascade(rga_number, st.session_state["user_name"])
            st.rerun()
    with c2:
        target = st.selectbox("Reassign To:", ["Unassigned", "Geo H", "Adam K", "New Guy"])
        if st.button("Reassign All", use_container_width=True):
            assign_parent_rga_cascade(rga_number, target)
            st.rerun()

# =========================================================
# LEFT-PANE SIDEBAR NAVIGATION & ROUTING
# =========================================================
df = load_data()

with st.sidebar:
    st.markdown("## ⚡ HYDAC PORTAL")
    st.caption(f"Logged in: **{st.session_state['user_name']}**\nRole: {st.session_state['user_role']}")
    st.divider()

    nav = st.radio(
        "WORKFLOW MODULES:",
        [
            "🖥️ Operations Queue",
            "📥 Phase 1: Inbound Intake",
            "🔬 Phase 2: Evaluation & Testing",
            "⏱️ Customer Hold Tracker",
            "🛠️ System Admin & Tools",
        ],
        index=0,
    )

    st.divider()
    if st.button("🔒 Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# =========================================================
# MODULE 1: OPERATIONS QUEUE (FLOATING CENTER LAYOUT)
# =========================================================
if nav == "🖥️ Operations Queue":
    # Floating Center Container Columns [1, 10, 1]
    col_pad_left, col_center, col_pad_right = st.columns([0.2, 10, 0.2])

    with col_center:
        st.markdown(
            """
            <div style="background-color:#FFFFFF; border-left:8px solid #E30613; border:2px solid #E2E8F0; padding:18px 24px; border-radius:12px; margin-bottom:20px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                <div style="font-size:1.6rem; font-weight:900; color:#0F172A; text-transform:uppercase;">OPERATIONS QUEUE & LAB COMMAND</div>
                <div style="font-size:0.9rem; color:#475569; font-weight:600;">HYDAC Technology Corp — Live Physical Shelf Queue & Order Tracking</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if df.empty:
            st.info("Database empty. Use System Admin in the left menu to populate demo data.")
        else:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Inbound Drop-off", (df["location"] == "Inbound Material").sum())
            m2.metric("Ready for Eval", (df["location"] == "Ready for Evaluation").sum())
            m3.metric("Customer Hold", (df["location"] == "Waiting for Customer Response").sum())
            m4.metric("Active Bench / CalRig", df["location"].isin(["Flow Bench", "CalRig"]).sum())

            st.markdown("<br>", unsafe_allow_html=True)

            c_search, c_shelf, c_tf = st.columns([2.5, 1.2, 1.2])
            search = c_search.text_input("SEARCH QUEUE:", placeholder="Type RGA, Serial Number, or Customer...")
            shelf_f = c_shelf.selectbox("SHELF FILTER:", ["All Shelves"] + list(df["location"].unique()))
            tf_f = c_tf.selectbox("STATUS FILTER:", ["All Statuses", "🟢 On Schedule", "🟡 Approaching SLA", "🔴 Late / Overdue"])

            filtered = df.copy()
            if shelf_f != "All Shelves":
                filtered = filtered[filtered["location"] == shelf_f]
            if tf_f == "🟢 On Schedule":
                filtered = filtered[filtered["timeframe_status"] == "GREEN"]
            elif tf_f == "🟡 Approaching SLA":
                filtered = filtered[filtered["timeframe_status"] == "YELLOW"]
            elif tf_f == "🔴 Late / Overdue":
                filtered = filtered[filtered["timeframe_status"] == "RED"]

            if search:
                mask = filtered.astype(str).apply(lambda col: col.str.contains(search, case=False)).any(axis=1)
                filtered = filtered[mask]

            st.markdown("### 📋 Active Request Queue")

            for rga, group in filtered.groupby("rga_number"):
                cust = group["customer_name"].iloc[0]
                csr = group.get("csr_name", pd.Series(["N/A"])).iloc[0] or "N/A"
                notif_num = group.get("notification_number", pd.Series(["N/A"])).iloc[0] or "N/A"
                owner = ", ".join(group["assigned_to"].unique())
                exp_header = f"RGA #{rga} — {cust} ({len(group)} Item/s) | Owner: {owner}"

                with st.expander(exp_header, expanded=False):
                    st.markdown(
                        f"**Parent RGA:** `{rga}` &nbsp;|&nbsp; **Customer:** `{cust}` &nbsp;|&nbsp; "
                        f"**CSR:** `{csr}` &nbsp;|&nbsp; **Notif #:** `{notif_num}` &nbsp;|&nbsp; "
                        f"**Assigned Owner:** `{owner}`"
                    )
                    st.markdown("---")

                    for _, item in group.iterrows():
                        st.markdown('<div class="child-card">', unsafe_allow_html=True)
                        col_info, col_shelf, col_act = st.columns([2.5, 1.6, 1.4])

                        status = item["timeframe_status"]
                        if status == "GREEN":
                            pill = '<span class="pill-green">🟢 On Schedule (&lt; 4 wks)</span>'
                        elif status == "YELLOW":
                            pill = '<span class="pill-yellow">🟡 Approaching SLA (4-7 wks)</span>'
                        else:
                            pill = '<span class="pill-red">🔴 Late / Overdue (&gt; 8 wks)</span>'

                        with col_info:
                            st.markdown(f"**Unit ID #{item['id']}** &nbsp;&nbsp; {pill}", unsafe_allow_html=True)
                            st.markdown(f"• **Model Series:** `{item.get('model_series') or 'None'}`")
                            st.markdown(f"• **Serial Number:** `{item.get('serial_number') or 'None'}`")
                            st.markdown(f"• **Accessories:** `{item.get('accessories') or 'None'}`")
                            st.markdown(f"• **Notes Log:** {str(item.get('notes', 'None'))}")

                        with col_shelf:
                            st.markdown("**Shelf Location:**")
                            st.write(f"Current Shelf: **{item['location']}**")
                            new_s = st.selectbox(
                                "Shift Shelf:",
                                ["Inbound Material", "Ready for Evaluation", "Flow Bench", "CalRig", "Waiting for Customer Response", "Completed / Ready for Shipping"],
                                index=["Inbound Material", "Ready for Evaluation", "Flow Bench", "CalRig", "Waiting for Customer Response", "Completed / Ready for Shipping"].index(item["location"]) if item["location"] in ["Inbound Material", "Ready for Evaluation", "Flow Bench", "CalRig", "Waiting for Customer Response", "Completed / Ready for Shipping"] else 1,
                                key=f"sh_{item['id']}"
                            )
                            if new_s != item["location"]:
                                if st.button("Apply Shift", key=f"btn_sh_{item['id']}"):
                                    update_location_and_status(item["id"], new_s)
                                    st.rerun()

                        with col_act:
                            st.markdown("**Actions:**")
                            c_a1, c_a2, c_a3 = st.columns(3)
                            with c_a1:
                                if st.button("🖐️ Assign", key=f"cl_{item['id']}"):
                                    modal_claim(item["rga_number"], item["id"], item.get("assigned_to", "Unassigned"))
                            with c_a2:
                                if st.button("📷 Photos", key=f"p_{item['id']}"):
                                    modal_photos(item["id"], item.get("photo_path", ""))
                            with c_a3:
                                if st.button("💬 Notes", key=f"n_{item['id']}"):
                                    modal_notes(item["id"], item.get("notes", ""))

                        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# MODULE 2: PHASE 1 INBOUND INTAKE
# =========================================================
elif nav == "📥 Phase 1: Inbound Intake":
    st.subheader("📥 Phase 1: Inbound Material Intake")
    intake_type = st.radio("Intake Type:", ["Single Unit Intake", "Batch Intake (Multiple Units under same RGA)"], horizontal=True)

    with st.form("phase1_form"):
        c1, c2, c3 = st.columns(3)
        rga = c1.text_input("RGA Number*:")
        notif = c2.text_input("Notification Number:")
        cust = c3.text_input("Customer Name*:")

        c4, c5 = st.columns(2)
        csr = c4.text_input("CSR Name:")
        service = c5.selectbox("Service Requested:", ["Calibration", "Repair", "Warranty Evaluation"])

        st.markdown("##### Accessories Checklist")
        acc_cols = st.columns(5)
        a_case = acc_cols[0].checkbox("Case")
        a_inlet = acc_cols[1].checkbox("Inlet Hose")
        a_outlet = acc_cols[2].checkbox("Outlet Hose")
        a_suction = acc_cols[3].checkbox("Suction Hose")
        a_comm = acc_cols[4].checkbox("Comm Cable")

        if intake_type == "Single Unit Intake":
            ca, cb = st.columns(2)
            model = ca.text_input("Model Series*:")
            sn = cb.text_input("Serial Number*:")
            vis = st.text_area("Visual Inspection Notes:")
            tech = st.selectbox("Assign Tech:", ["Unassigned", "Geo H", "Adam K", "New Guy"])

            if st.form_submit_button("🚀 Submit Intake", type="primary"):
                accs = []
                if a_case: accs.append("Case")
                if a_inlet: accs.append("Inlet Hose")
                if a_outlet: accs.append("Outlet Hose")
                if a_suction: accs.append("Suction Hose")
                if a_comm: accs.append("Comm Cable")

                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO queue (rga_number, notification_number, customer_name, csr_name, service_requested, model_series, serial_number, location, status, assigned_to, accessories, visual_inspection, date_logged)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Ready for Evaluation', 'Received in Lab', ?, ?, ?, ?)
                """, (rga, notif, cust, csr, service, model, sn, tech, ", ".join(accs), vis, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.toast("Intake logged!", icon="🚀")
                st.rerun()

# =========================================================
# MODULE 3: PHASE 2 EVALUATION & TESTING
# =========================================================
elif nav == "🔬 Phase 2: Evaluation & Testing":
    st.subheader("🔬 Phase 2: Bench Evaluation & Protocol Sheet")
    if df.empty:
        st.warning("No units available.")
    else:
        options = build_unit_dropdown_options(df)
        sel_label = st.selectbox("Select Unit to Evaluate:", list(options.keys()))
        sel_id = options[sel_label]
        sel_row = df[df["id"] == sel_id].iloc[0]

        st.markdown(f"**Evaluating Unit #{sel_id}** — RGA: `{sel_row['rga_number']}` | SN: `{sel_row['serial_number']}`")

        form_template = st.selectbox("Select Protocol Form:", ["F-0100: Contamination Sensors", "F-0101: Fluid Conditioning Units", "F-0102: AquaSensors", "F-0103: General Electronic Bench"])
        
        with st.form("eval_sheet_form"):
            c1, c2 = st.columns(2)
            diode = c1.selectbox("Laser Diode Check:", ["Pass", "Fail", "N/A"])
            align = c2.selectbox("Calibration Alignment:", ["In Spec", "Out of Spec", "Hardware Defect"])
            notes = st.text_area("Diagnostic Findings / Notes:", value=sel_row.get("notes", ""))
            
            target_shelf = st.radio("Route Shelf:", ["Keep on Bench", "Move to Customer Hold", "Complete & Ready for Shipping"])

            if st.form_submit_button("💾 Save Evaluation Protocol", type="primary"):
                route_loc = "Waiting for Customer Response" if "Customer Hold" in target_shelf else ("Completed / Ready for Shipping" if "Ready for Shipping" in target_shelf else sel_row["location"])
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE queue SET eval_form_type=?, notes=?, location=? WHERE id=?
                """, (form_template, notes, route_loc, sel_id))
                conn.commit()
                conn.close()
                st.toast("Saved evaluation!", icon="🔬")
                st.rerun()

# =========================================================
# MODULE 4: CUSTOMER HOLD TRACKER
# =========================================================
elif nav == "⏱️ Customer Hold Tracker":
    st.subheader("⏱️ Customer Response Tracker (30-Day Limit)")
    holds = df[df["location"] == "Waiting for Customer Response"]
    if holds.empty:
        st.success("No units on Customer Hold!")
    else:
        for _, row in holds.iterrows():
            with st.container(border=True):
                st.markdown(f"**Unit #{row['id']}** | RGA: `{row['rga_number']}` | Customer: `{row['customer_name']}`")
                st.write(f"Days Remaining: `{row.get('days_remaining_hold', 30)}`")
                if st.button("✅ Approval Received", key=f"hold_appr_{row['id']}"):
                    update_location_and_status(row["id"], "Flow Bench", "Approved")
                    st.rerun()

# =========================================================
# MODULE 5: SYSTEM ADMIN & DEMO RESET
# =========================================================
else:
    st.subheader("🛠️ System Admin Tools")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🌱 Execute Database Reset & Seed Demo Data", type="primary"):
            reset_and_seed_db()
            st.toast("Database Reset & Demo Data Loaded!", icon="🌱")
            st.rerun()

    with c2:
        if not df.empty:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Lab Queue")
            st.download_button("📥 Export Excel Report (.xlsx)", data=output.getvalue(), file_name="lab_queue_export.xlsx")