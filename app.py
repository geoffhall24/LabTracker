import io
import json
import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# =========================================================
# PAGE CONFIGURATION & ENTERPRISE DARK SLATE THEME
# =========================================================
st.set_page_config(
    page_title="HYDAC Electronic Lab Portal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_FILE = "lab_queue.db"
LOCAL_CERTS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Certs"
UPLOADS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Uploads"

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(LOCAL_CERTS_DIR, exist_ok=True)

# Custom Enterprise CSS
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0F172A !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        color: #F8FAFC !important;
    }

    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 98%;
    }

    h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #F8FAFC !important;
        font-weight: 800 !important;
        letter-spacing: -0.3px !important;
    }

    p, span, label, div {
        color: #CBD5E1 !important;
    }

    /* WIDGET LABELS */
    label[data-testid="stWidgetLabel"] p, .stWidgetLabel p {
        color: #94A3B8 !important;
        font-weight: 700 !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }

    /* INPUT FIELDS & DROPDOWNS */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #F8FAFC !important;
    }

    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
        color: #F8FAFC !important;
        font-weight: 500 !important;
    }

    /* KPI METRIC CARDS */
    div[data-testid="stMetric"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        padding: 16px 20px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important;
    }

    div[data-testid="stMetricValue"] div {
        color: #F8FAFC !important;
        font-size: 2.1rem !important;
        font-weight: 800 !important;
    }

    div[data-testid="stMetricLabel"] div {
        color: #94A3B8 !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
    }

    /* EXPANDER RGA CARDS */
    details[data-testid="stExpander"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        margin-bottom: 12px !important;
    }

    summary[data-testid="stExpanderSummary"] {
        background-color: #1E293B !important;
        border-radius: 10px !important;
        padding: 14px 18px !important;
    }

    summary[data-testid="stExpanderSummary"] p {
        color: #F8FAFC !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
    }

    /* LINE ITEM CARDS */
    .child-card {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }

    /* TIMEFRAME STATUS PILLS */
    .status-pill-green {
        background-color: rgba(22, 163, 74, 0.2);
        color: #4ADE80;
        border: 1px solid #16A34A;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
    }

    .status-pill-yellow {
        background-color: rgba(202, 138, 4, 0.2);
        color: #FACC15;
        border: 1px solid #CA8A04;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
    }

    .status-pill-red {
        background-color: rgba(220, 38, 38, 0.2);
        color: #F87171;
        border: 1px solid #DC2626;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
    }

    /* BUTTONS */
    div.stButton > button {
        background-color: #334155 !important;
        color: #F8FAFC !important;
        border: 1px solid #475569 !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
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
                    <h2 style="color:#F8FAFC; font-weight:900; margin-bottom:4px;">⚡ ELECTRONIC LAB PORTAL</h2>
                    <p style="color:#94A3B8; font-size:0.9rem; font-weight:600;">HYDAC Technology Corp Operations System</p>
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
# DATABASE INITIALIZATION & MIGRATION
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
    date_fresh = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    date_warn = (today - timedelta(days=35)).strftime("%Y-%m-%d")
    date_late = (today - timedelta(days=65)).strftime("%Y-%m-%d")

    demo_data = [
        ("60083000", "20007503", "Caterpillar Inc.", "Sarah Jenkins", "Calibration", "CS 1000 Contamination Sensor", "000SS01831K0000001", "CalRig", "Under Calibration", 9, "Geo H", "Case, Power Adapter", "Clean exterior", "F-0100", "{}", "High priority diode test bench 1.", "[]", "", date_fresh, ""),
        ("60083105", "20007510", "John Deere Corp.", "Mike Ross", "Repair", "FAM-10 Fluid Conditioning Unit", "FAM10-998231-A", "Waiting for Customer Response", "Pending Customer Approval", 6, "Adam K", "Inlet Hose, Outlet Hose", "Vacuum pump seal leak", "F-0101", "{}", "Quote sent to customer.", "[]", "", date_warn, date_warn),
        ("60082990", "20007480", "Komatsu Ltd.", "Rachel Zane", "Calibration", "FCU 1310 Portable Filtration", "FCU1310-88412-A", "Flow Bench", "Overdue - Urgent", 10, "New Guy", "Suction Hose", "Heavy oil accumulation", "F-0101", "{}", "Unit delayed over 8 weeks.", "[]", "", date_late, ""),
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
# INTERACTIVE MODAL DIALOGS
# =========================================================
@st.dialog("📷 Photos & Multi-Image Manager")
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
                cols[idx % 3].image(p, caption=f"Img #{idx+1}", use_container_width=True)
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
        st.toast("Photos updated successfully!", icon="📷")
        st.rerun()

@st.dialog("💬 Notes & Outlook Sync")
def modal_notes(unit_id, current_notes):
    st.markdown(f"### Unit #{unit_id} Diagnostic History")
    st.text_area("Log History:", value=current_notes or "No existing notes.", height=150, disabled=True)

    t1, t2 = st.tabs(["Add Lab Note", "Sync Outlook Email"])
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

@st.dialog("🖐️ Assign RGA Cascade")
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
# MAIN APP HEADER & MODULE NAVIGATION
# =========================================================
df = load_data()

col_logo, col_header, col_logout = st.columns([1, 6, 1.2])
with col_header:
    st.markdown(
        f"""
        <div style="background-color:#1E293B; border-left:6px solid #E30613; padding:18px 24px; border-radius:10px; margin-bottom:18px;">
            <div style="font-size:1.6rem; font-weight:800; color:#F8FAFC;">HYDAC ELECTRONIC LAB PORTAL</div>
            <div style="font-size:0.88rem; color:#94A3B8;">User: {st.session_state['user_name']} ({st.session_state['user_role']}) | Operations Command & Shelf Tracking</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔒 Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

nav = st.segmented_control(
    "Select Workflow Module:",
    [
        "🖥️ Operations Queue (TV Display)",
        "📥 Phase 1: Inbound Intake",
        "🔬 Phase 2: Evaluation & Testing",
        "⏱️ Customer Hold Tracker",
        "🛠️ System Admin & Tools",
    ],
    default="🖥️ Operations Queue (TV Display)",
)

# =========================================================
# MODULE 1: OPERATIONS QUEUE
# =========================================================
if nav == "🖥️ Operations Queue (TV Display)":
    if df.empty:
        st.info("Database empty. Use System Admin to populate demo data.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Inbound Drop-off", (df["location"] == "Inbound Material").sum())
        m2.metric("Ready for Eval", (df["location"] == "Ready for Evaluation").sum())
        m3.metric("Customer Hold", (df["location"] == "Waiting for Customer Response").sum())
        m4.metric("Active Bench / CalRig", df["location"].isin(["Flow Bench", "CalRig"]).sum())

        st.markdown("<br>", unsafe_allow_html=True)

        c_search, c_shelf, c_tf = st.columns([2.5, 1.2, 1.2])
        search = c_search.text_input("Search Queue:", placeholder="RGA, Serial, Customer...")
        shelf_f = c_shelf.selectbox("Shelf Filter:", ["All Shelves"] + list(df["location"].unique()))
        tf_f = c_tf.selectbox("Status Filter:", ["All Statuses", "🟢 On Time", "🟡 Warning", "🔴 Late"])

        filtered = df.copy()
        if shelf_f != "All Shelves":
            filtered = filtered[filtered["location"] == shelf_f]
        if tf_f == "🟢 On Time":
            filtered = filtered[filtered["timeframe_status"] == "GREEN"]
        elif tf_f == "🟡 Warning":
            filtered = filtered[filtered["timeframe_status"] == "YELLOW"]
        elif tf_f == "🔴 Late":
            filtered = filtered[filtered["timeframe_status"] == "RED"]

        if search:
            mask = filtered.astype(str).apply(lambda col: col.str.contains(search, case=False)).any(axis=1)
            filtered = filtered[mask]

        for rga, group in filtered.groupby("rga_number"):
            cust = group["customer_name"].iloc[0]
            owner = ", ".join(group["assigned_to"].unique())
            exp_header = f"RGA #{rga} — {cust} ({len(group)} Unit/s) | Owner: {owner}"

            with st.expander(exp_header, expanded=False):
                for _, item in group.iterrows():
                    st.markdown('<div class="child-card">', unsafe_allow_html=True)
                    col_info, col_shelf, col_act = st.columns([2.5, 1.5, 1])

                    status = item["timeframe_status"]
                    if status == "GREEN":
                        pill = '<span class="status-pill-green">🟢 On Schedule (&lt; 4 wks)</span>'
                    elif status == "YELLOW":
                        pill = '<span class="status-pill-yellow">🟡 Deadline Approaching (4-7 wks)</span>'
                    else:
                        pill = '<span class="status-pill-red">🔴 Late / Past SLA (&gt; 8 wks)</span>'

                    with col_info:
                        st.markdown(f"**Unit ID #{item['id']}** &nbsp; {pill}", unsafe_allow_html=True)
                        st.write(f"• **Model:** `{item.get('model_series', 'N/A')}`")
                        st.write(f"• **Serial:** `{item.get('serial_number', 'N/A')}`")
                        st.write(f"• **Notes:** {str(item.get('notes', 'None'))[:100]}...")

                    with col_shelf:
                        st.markdown("**Shelf Assignment:**")
                        new_s = st.selectbox(
                            "Move Shelf:",
                            ["Inbound Material", "Ready for Evaluation", "Flow Bench", "CalRig", "Waiting for Customer Response", "Completed / Ready for Shipping"],
                            index=["Inbound Material", "Ready for Evaluation", "Flow Bench", "CalRig", "Waiting for Customer Response", "Completed / Ready for Shipping"].index(item["location"]) if item["location"] in ["Inbound Material", "Ready for Evaluation", "Flow Bench", "CalRig", "Waiting for Customer Response", "Completed / Ready for Shipping"] else 1,
                            key=f"sh_{item['id']}"
                        )
                        if new_s != item["location"]:
                            if st.button("Apply Move", key=f"btn_sh_{item['id']}"):
                                update_location_and_status(item["id"], new_s)
                                st.rerun()

                    with col_act:
                        st.markdown("**Actions:**")
                        c_a1, c_a2, c_a3 = st.columns(3)
                        with c_a1:
                            if st.button("🖐️", key=f"cl_{item['id']}"):
                                modal_claim(item["rga_number"], item["id"], item.get("assigned_to", "Unassigned"))
                        with c_a2:
                            if st.button("📷", key=f"p_{item['id']}"):
                                modal_photos(item["id"], item.get("photo_path", ""))
                        with c_a3:
                            if st.button("💬", key=f"n_{item['id']}"):
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
# MODULE 5: SYSTEM ADMIN & EXCEL EXPORT
# =========================================================
else:
    st.subheader("🛠️ System Admin Tools")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🌱 Execute Database Reset & Demo Seed", type="primary"):
            reset_and_seed_db()
            st.toast("Database Reset Done!", icon="🌱")
            st.rerun()

    with c2:
        if not df.empty:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Lab Queue")
            st.download_button("📥 Export Excel Report (.xlsx)", data=output.getvalue(), file_name="lab_queue_export.xlsx")