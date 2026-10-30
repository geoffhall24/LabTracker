import io
import json
import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# =========================================================
# PAGE CONFIGURATION & HIGH-CONTRAST LIGHT THEME
# =========================================================
st.set_page_config(
    page_title="HYDAC Electronic Lab Portal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "lab_queue.db"
FORMS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\FORMS"
LOCAL_CERTS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Certs"
UPLOADS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Uploads"

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(LOCAL_CERTS_DIR, exist_ok=True)
os.makedirs(FORMS_DIR, exist_ok=True)

# CSS for Ultra-High Contrast & Legibility
st.markdown(
    """
    <style>
    /* Clean Light Base */
    .stApp {
        background-color: #F8FAFC !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        color: #0F172A !important;
    }

    .main .block-container {
        padding-top: 1.2rem;
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

    /* CODE BLOCKS & MONOSPACE READABILITY FIX */
    code, .stMarkdown code {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        border: 1px solid #CBD5E1 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 0.95rem !important;
    }

    /* WIDGET LABELS */
    label[data-testid="stWidgetLabel"] p, .stWidgetLabel p {
        color: #0284C7 !important;
        font-weight: 800 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }

    /* INPUT FIELDS & DROPDOWNS */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 2px solid #64748B !important;
        border-radius: 8px !important;
        color: #0F172A !important;
    }

    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
        color: #0F172A !important;
        font-weight: 700 !important;
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
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05) !important;
        overflow: hidden !important;
    }

    summary[data-testid="stExpanderSummary"] {
        background-color: #F1F5F9 !important;
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
        border: 2px solid #CBD5E1 !important;
        border-radius: 10px !important;
        padding: 20px !important;
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
        border: 2px solid #16A34A !important;
        padding: 6px 14px !important;
        border-radius: 20px !important;
        font-weight: 800 !important;
        font-size: 0.85rem !important;
        display: inline-block !important;
    }

    .pill-yellow {
        background-color: #FEF9C3 !important;
        color: #A16207 !important;
        border: 2px solid #CA8A04 !important;
        padding: 6px 14px !important;
        border-radius: 20px !important;
        font-weight: 800 !important;
        font-size: 0.85rem !important;
        display: inline-block !important;
    }

    .pill-red {
        background-color: #FEE2E2 !important;
        color: #B91C1C !important;
        border: 2px solid #DC2626 !important;
        padding: 6px 14px !important;
        border-radius: 20px !important;
        font-weight: 800 !important;
        font-size: 0.85rem !important;
        display: inline-block !important;
    }

    /* ICON INDICATOR BADGES */
    .indicator-badge {
        background-color: #E2E8F0;
        color: #0F172A;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.82rem;
        margin-right: 6px;
        display: inline-block;
        border: 1px solid #94A3B8;
    }

    /* HIGH CONTRAST BUTTON FIX FOR SHOP FLOOR READABILITY */
    div.stButton > button {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border: 1px solid #0F172A !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
        box-shadow: 0 3px 8px rgba(0,0,0,0.15) !important;
    }

    div.stButton > button:hover {
        background-color: #334155 !important;
        color: #FFFFFF !important;
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
# DATABASE INITIALIZATION & MIGRATION PIPELINE
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
            last_phase_change TEXT,
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
        "last_phase_change": "TEXT",
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

        def calc_flags(row):
            photos = row.get("photo_path")
            has_photos = False
            if photos and photos != "[]" and photos != "None":
                try:
                    p_list = json.loads(photos)
                    has_photos = len(p_list) > 0
                except Exception:
                    has_photos = True

            notes_str = str(row.get("notes") or "")
            has_notes = len(notes_str.strip()) > 0 and notes_str != "None"
            has_outlook = "OUTLOOK SYNC" in notes_str or "✉️" in notes_str

            last_change = row.get("last_phase_change")
            recent_phase = False
            if last_change and last_change != "None":
                try:
                    c_date = datetime.strptime(str(last_change)[:10], "%Y-%m-%d")
                    recent_phase = (now - c_date).days <= 2
                except Exception:
                    recent_phase = False

            return pd.Series([has_photos, has_notes, has_outlook, recent_phase])

        df[["has_photos", "has_notes", "has_outlook", "recent_phase"]] = df.apply(calc_flags, axis=1)

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
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    if new_location == "Waiting for Customer Response":
        cursor.execute("UPDATE queue SET location=?, customer_hold_date=?, last_phase_change=? WHERE id=?", (new_location, today_str[:10], today_str, unit_id))
    else:
        cursor.execute("UPDATE queue SET location=?, last_phase_change=? WHERE id=?", (new_location, today_str, unit_id))

    if new_status:
        cursor.execute("UPDATE queue SET status=? WHERE id=?", (new_status, unit_id))

    conn.commit()
    conn.close()

def get_pdf_form_list():
    """Reads PDF files from FORMS_DIR."""
    if os.path.exists(FORMS_DIR):
        files = [f for f in os.listdir(FORMS_DIR) if f.lower().endswith(".pdf")]
        if files:
            return sorted(files)
    return ["F-0100_Contamination_Sensors.pdf", "F-0101_Fluid_Conditioning_Units.pdf", "F-0102_AquaSensors.pdf", "F-0103_General_Bench.pdf"]

def reset_and_seed_db():
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
            last_phase_change TEXT,
            customer_hold_date TEXT
        )
    """)

    today = datetime.now()
    d_fresh = (today - timedelta(days=6)).strftime("%Y-%m-%d")
    d_warn = (today - timedelta(days=32)).strftime("%Y-%m-%d")
    d_late = (today - timedelta(days=62)).strftime("%Y-%m-%d")
    ts_fresh = datetime.now().strftime("%Y-%m-%d %H:%M")

    demo_data = [
        ("60083000", "20007503", "Caterpillar Inc.", "Sarah Jenkins", "Calibration", "CS 1000 Contamination Sensor", "000SS01831K0000001", "CalRig", "Under Calibration", 9, "Geo H", "Case, Power Adapter, Comm Cable", "Clean exterior, optical ports clear", "F-0100_Contamination_Sensors.pdf", "{\"diode\":\"Pass\",\"alignment\":\"In Spec\"}", "[2026-10-24 - Geo H]: Diode bench synced. Calibration underway.", "[]", "", d_fresh, ts_fresh, ""),
        ("60083000", "20007503", "Caterpillar Inc.", "Sarah Jenkins", "Calibration", "CS 1000 Contamination Sensor", "000SS01831K0000002", "CalRig", "Under Calibration", 9, "Geo H", "Case, Power Adapter", "Diode port inspected", "F-0100_Contamination_Sensors.pdf", "{\"diode\":\"Pass\",\"alignment\":\"In Spec\"}", "[2026-10-24 - Geo H]: Zero offset verified.", "[]", "", d_fresh, ts_fresh, ""),
        ("60083105", "20007510", "John Deere Corp.", "Mike Ross", "Repair", "FAM-10 Fluid Conditioning Unit", "FAM10-998231-A", "Waiting for Customer Response", "Pending Customer Approval", 6, "Adam K", "Inlet Hose, Outlet Hose, Manual", "Vacuum pump seal oil leakage noticed", "F-0101_Fluid_Conditioning_Units.pdf", "{\"pump\":\"Fail\"}", "[2026-10-02 - Adam K]: Quote sent to CSR Mike Ross for customer approval.\n\n[✉️ OUTLOOK SYNC - 2026-10-15 by Adam K]: Customer requested revised quote breakdown.", "[]", "", d_warn, ts_fresh, d_warn),
        ("60082990", "20007480", "Komatsu Ltd.", "Rachel Zane", "Calibration", "FCU 1310 Portable Filtration", "FCU1310-88412-A", "Flow Bench", "Overdue - Urgent", 10, "New Guy", "Suction Hose, Power Adapter", "Heavy hydraulic oil accumulation inside casing", "F-0101_Fluid_Conditioning_Units.pdf", "{}", "[2026-08-28 - New Guy]: Unit delayed > 8 weeks awaiting bench adapter.\n\n[✉️ OUTLOOK SYNC - 2026-09-10 by Rachel Zane]: Customer inquired on delivery date.", "[]", "", d_late, ts_fresh, ""),
        ("60083145", "20007548", "Parker Hannifin", "Sarah Jenkins", "Calibration", "AS 1000 AquaSensor", "AS1000-77621-C", "Inbound Material", "Dropped Off", 5, "Unassigned", "Case, Comm Cable", "Original field return packaging intact", "F-0102_AquaSensors.pdf", "{}", "[2026-10-28 - Geo H]: Package received at shipping dock shelf.", "[]", "", d_fresh, ts_fresh, ""),
    ]

    cursor.executemany("""
        INSERT INTO queue (
            rga_number, notification_number, customer_name, csr_name, service_requested,
            model_series, serial_number, location, status, urgency,
            assigned_to, accessories, visual_inspection, eval_form_type, eval_data,
            notes, photo_path, cal_file_path, date_logged, last_phase_change, customer_hold_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
# INTERACTIVE MODAL OVERLAYS
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
# SIDEBAR NAVIGATION
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
# MODULE 1: OPERATIONS QUEUE
# =========================================================
if nav == "🖥️ Operations Queue":
    col_pad_left, col_center, col_pad_right = st.columns([0.1, 10, 0.1])

    with col_center:
        st.markdown(
            """
            <div style="background-color:#FFFFFF; border-left:8px solid #E30613; border:2px solid #CBD5E1; padding:18px 24px; border-radius:12px; margin-bottom:20px;">
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
                owner = ", ".join(group["assigned_to"].unique())

                rga_has_photos = group["has_photos"].any()
                rga_has_notes = group["has_notes"].any()
                rga_has_outlook = group["has_outlook"].any()
                rga_recent_phase = group["recent_phase"].any()

                icon_str = ""
                if rga_has_photos: icon_str += " 📷"
                if rga_has_notes: icon_str += " 💬"
                if rga_has_outlook: icon_str += " ✉️"
                if rga_recent_phase: icon_str += " 🔄"

                exp_header = f"RGA #{rga} — {cust} ({len(group)} Item/s) {icon_str} | Owner: {owner}"

                with st.expander(exp_header, expanded=False):
                    st.markdown(
                        f"**Parent RGA:** `{rga}` &nbsp;|&nbsp; **Customer:** `{cust}` &nbsp;|&nbsp; **Assigned Owner:** `{owner}`"
                    )
                    st.markdown("---")

                    for _, item in group.iterrows():
                        st.markdown('<div class="child-card">', unsafe_allow_html=True)
                        col_info, col_shelf, col_act = st.columns([2.5, 1.6, 1.4])

                        status = item["timeframe_status"]
                        if status == "GREEN":
                            pill = '<span class="pill-green">🟢 On Schedule</span>'
                        elif status == "YELLOW":
                            pill = '<span class="pill-yellow">🟡 Approaching SLA</span>'
                        else:
                            pill = '<span class="pill-red">🔴 Late / Overdue</span>'

                        item_icons = ""
                        if item["has_photos"]: item_icons += '<span class="indicator-badge">📷 Photos</span>'
                        if item["has_notes"]: item_icons += '<span class="indicator-badge">💬 Notes</span>'
                        if item["has_outlook"]: item_icons += '<span class="indicator-badge">✉️ Outlook</span>'
                        if item["recent_phase"]: item_icons += '<span class="indicator-badge">🔄 Shifted</span>'

                        with col_info:
                            st.markdown(f"**Unit ID #{item['id']}** &nbsp;&nbsp; {pill} &nbsp;&nbsp; {item_icons}", unsafe_allow_html=True)
                            st.markdown(f"• **Part Number / Model:** `{item.get('model_series') or 'None'}`")
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
# MODULE 2: PHASE 1 INBOUND INTAKE (DYNAMIC MIXED BATCH ENTRY)
# =========================================================
elif nav == "📥 Phase 1: Inbound Intake":
    st.subheader("📥 Phase 1: Inbound Material Intake")
    intake_type = st.radio("Intake Mode:", ["Single Unit Entry", "Multi-Item Mixed Batch Entry (Different Part Numbers & Serials)"], horizontal=True)

    with st.form("phase1_form"):
        c1, c2, c3 = st.columns(3)
        rga = c1.text_input("RGA Number*:")
        notif = c2.text_input("Notification Number:")
        cust = c3.text_input("Customer Name*:")

        c4, c5 = st.columns(2)
        csr = c4.text_input("CSR Name:")
        service = c5.selectbox("Service Requested:", ["Calibration", "Repair", "Warranty Evaluation"])

        st.markdown("##### Received Accessories Checklist")
        acc_cols = st.columns(5)
        a_case = acc_cols[0].checkbox("Case")
        a_inlet = acc_cols[1].checkbox("Inlet Hose")
        a_outlet = acc_cols[2].checkbox("Outlet Hose")
        a_suction = acc_cols[3].checkbox("Suction Hose")
        a_comm = acc_cols[4].checkbox("Comm Cable")

        acc_cols2 = st.columns(5)
        a_power = acc_cols2[0].checkbox("Power Adapter")
        a_manual = acc_cols2[1].checkbox("Manual")
        a_cd = acc_cols2[2].checkbox("CD/Floppy")
        a_paper = acc_cols2[3].checkbox("Paper Roll")
        a_ribbon = acc_cols2[4].checkbox("Ink Ribbon")

        if intake_type == "Single Unit Entry":
            ca, cb = st.columns(2)
            model = ca.text_input("Part Number / Model Series*:")
            sn = cb.text_input("Serial Number*:")
            vis = st.text_area("Visual Inspection Notes:")
            tech = st.selectbox("Assign Tech:", ["Unassigned", "Geo H", "Adam K", "New Guy"])

            if st.form_submit_button("🚀 Submit Single Intake", type="primary"):
                if rga and cust and model and sn:
                    accs = [label for check, label in [(a_case, "Case"), (a_inlet, "Inlet Hose"), (a_outlet, "Outlet Hose"), (a_suction, "Suction Hose"), (a_comm, "Comm Cable"), (a_power, "Power Adapter"), (a_manual, "Manual"), (a_cd, "CD/Floppy"), (a_paper, "Paper Roll"), (a_ribbon, "Ink Ribbon")] if check]

                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO queue (rga_number, notification_number, customer_name, csr_name, service_requested, model_series, serial_number, location, status, assigned_to, accessories, visual_inspection, date_logged, last_phase_change)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'Ready for Evaluation', 'Received in Lab', ?, ?, ?, ?, ?)
                    """, (rga, notif, cust, csr, service, model, sn, tech, ", ".join(accs) if accs else "None", vis, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    conn.close()
                    st.toast("Unit intake logged!", icon="🚀")
                    st.rerun()
                else:
                    st.error("Please fill in RGA, Customer, Model, and Serial Number.")

        else:
            st.markdown("##### 📦 Multi-Item Batch Grid (Enter mixed Part Numbers & Serials)")
            st.caption("Edit the table below to enter different Part Numbers and Serial Numbers under this single RGA:")

            initial_batch_df = pd.DataFrame([
                {"Part_Number": "CS 1000 Contamination Sensor", "Serial_Number": ""},
                {"Part_Number": "FAM-10 Fluid Conditioning Unit", "Serial_Number": ""},
                {"Part_Number": "AS 1000 AquaSensor", "Serial_Number": ""},
            ])

            batch_grid = st.data_editor(
                initial_batch_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Part_Number": st.column_config.TextColumn("Part Number / Model Series", required=True),
                    "Serial_Number": st.column_config.TextColumn("Serial Number", required=True),
                },
                key="batch_grid_editor"
            )

            vis = st.text_area("Visual Inspection Notes:")
            tech = st.selectbox("Assign Tech:", ["Unassigned", "Geo H", "Adam K", "New Guy"])

            if st.form_submit_button("🚀 Submit Multi-Item Batch Intake", type="primary"):
                valid_items = batch_grid.dropna(subset=["Part_Number", "Serial_Number"])
                valid_items = valid_items[(valid_items["Part_Number"].str.strip() != "") & (valid_items["Serial_Number"].str.strip() != "")]

                if rga and cust and not valid_items.empty:
                    accs = [label for check, label in [(a_case, "Case"), (a_inlet, "Inlet Hose"), (a_outlet, "Outlet Hose"), (a_suction, "Suction Hose"), (a_comm, "Comm Cable"), (a_power, "Power Adapter"), (a_manual, "Manual"), (a_cd, "CD/Floppy"), (a_paper, "Paper Roll"), (a_ribbon, "Ink Ribbon")] if check]
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    ts_str = datetime.now().strftime("%Y-%m-%d %H:%M")

                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()

                    for _, row in valid_items.iterrows():
                        cursor.execute("""
                            INSERT INTO queue (rga_number, notification_number, customer_name, csr_name, service_requested, model_series, serial_number, location, status, assigned_to, accessories, visual_inspection, date_logged, last_phase_change)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 'Ready for Evaluation', 'Received in Lab', ?, ?, ?, ?, ?)
                        """, (rga, notif, cust, csr, service, row["Part_Number"].strip(), row["Serial_Number"].strip(), tech, ", ".join(accs) if accs else "None", vis, today_str, ts_str))

                    conn.commit()
                    conn.close()
                    st.toast(f"Logged {len(valid_items)} mixed batch items under RGA {rga}!", icon="📦")
                    st.rerun()
                else:
                    st.error("Please provide RGA, Customer Name, and at least one row with Part Number and Serial Number.")

# =========================================================
# MODULE 3: PHASE 2 EVALUATION & TESTING (PDF INTEGRATED)
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

        st.markdown(f"**Evaluating Unit #{sel_id}** — RGA: `{sel_row['rga_number']}` | Part: `{sel_row['model_series']}` | SN: `{sel_row['serial_number']}`")

        pdf_forms = get_pdf_form_list()
        selected_pdf = st.selectbox("📁 Select Evaluation Form Template (Loaded from FORMS directory):", pdf_forms)

        st.info(f"Loaded PDF Form Schema: `{selected_pdf}`")

        with st.form("eval_sheet_form"):
            st.markdown(f"#### Protocol Questions for `{selected_pdf}`")

            if "F-0100" in selected_pdf or "Contamination" in selected_pdf:
                c1, c2 = st.columns(2)
                diode = c1.selectbox("Laser Diode Alignment Check:", ["Pass", "Fail", "N/A"])
                optics = c2.selectbox("Cell Optics Cleanliness:", ["Pass", "Requires Cleaning", "Fail"])
                p_channel = st.text_input("4um / 6um / 14um Channel Baseline Check:", value="Clean - In Spec")

            elif "F-0101" in selected_pdf or "Conditioning" in selected_pdf:
                c1, c2 = st.columns(2)
                vacuum = c1.selectbox("Vacuum Pump Seal Leak Check:", ["Pass", "Fail - Leaking", "N/A"])
                flow_rate = c2.text_input("Measured Flow Rate (L/min):", value="1.5 L/min")
                p_channel = st.text_input("Dehydration Efficiency Test:", value="Optimal")

            elif "F-0102" in selected_pdf or "Aqua" in selected_pdf:
                c1, c2 = st.columns(2)
                sat = c1.selectbox("Water Saturation Sensor Calibration:", ["Pass", "Out of Spec", "N/A"])
                temp = c2.text_input("Temperature Sensor Accuracy (°C):", value="25.0 °C")
                p_channel = st.text_input("Capacitive Element Voltage:", value="1.2V DC")

            else:
                c1, c2 = st.columns(2)
                diode = c1.selectbox("General Voltage Alignment:", ["Pass", "Fail"])
                optics = c2.selectbox("Housing Seal Check:", ["Pass", "Fail"])
                p_channel = st.text_input("General Bench Inspection Notes:", value="Passed standard check")

            notes = st.text_area("Diagnostic Findings / Tech Notes Log:", value=sel_row.get("notes", ""))
            target_shelf = st.radio("Route Shelf:", ["Keep on Bench", "Move to Customer Hold", "Complete & Ready for Shipping"])

            if st.form_submit_button("💾 Save Evaluation Protocol", type="primary"):
                route_loc = "Waiting for Customer Response" if "Customer Hold" in target_shelf else ("Completed / Ready for Shipping" if "Ready for Shipping" in target_shelf else sel_row["location"])
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE queue SET eval_form_type=?, notes=?, location=?, last_phase_change=? WHERE id=?
                """, (selected_pdf, notes, route_loc, datetime.now().strftime("%Y-%m-%d %H:%M"), sel_id))
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