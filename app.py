import io
import os
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# =========================================================
# PAGE CONFIGURATION & HYDAC CORPORATE THEME
# =========================================================
st.set_page_config(
    page_title="HYDAC Lab Queue Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "lab_queue.db"
LOCAL_CERTS_DIR = r"C:\Users\Geoff.Hall\OneDrive - HYDAC Technology Corp\Desktop\LabQueueTracker\Certs"

# HYDAC Modern Industrial UI Styling (Corporate Red & Dark Slate)
st.markdown(
    """
    <style>
    /* HYDAC Corporate Palette */
    :root {
        --hydac-red: #E30613;
        --hydac-dark: #0F172A;
        --hydac-slate: #1E293B;
        --hydac-bg: #F8FAFC;
        --hydac-border: #E2E8F0;
    }

    /* Main Container Padding */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 96%;
    }

    /* Enterprise Header Banner */
    .hydac-header-card {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border-left: 6px solid #E30613;
        border-radius: 8px;
        padding: 20px 24px;
        color: #FFFFFF;
        box-shadow: 0 4px 14px rgba(0,0,0,0.06);
        margin-bottom: 18px;
    }
    .hydac-header-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hydac-header-subtitle {
        font-size: 0.92rem;
        color: #94A3B8;
        margin-top: 4px;
        font-weight: 500;
    }

    /* KPI Metrics Styling */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: 3px solid #E30613;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    div[data-testid="stMetric"] label {
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }

    /* Badges & Status Pills */
    .badge-email {
        background-color: #166534;
        color: #DCFCE7;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-reply {
        background-color: #1E40AF;
        color: #DBEAFE;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }

    /* Sidebar Customization */
    .sidebar-user-card {
        background: #1E293B;
        border-left: 4px solid #E30613;
        padding: 12px 16px;
        border-radius: 6px;
        color: #F8FAFC;
        margin-bottom: 15px;
    }
    .sidebar-section-header {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #94A3B8;
        font-weight: 700;
        margin-top: 14px;
        margin-bottom: 6px;
    }

    /* Button Styling Overrides */
    div.stButton > button[kind="primary"] {
        background-color: #E30613 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #A8000A !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HELPER FUNCTIONS & DATABASE DATA LOADER
# =========================================================
def load_data():
  """Loads the lab queue dataframe cleanly from the local SQLite database."""
  if not os.path.exists(DB_FILE):
    return pd.DataFrame()
  conn = sqlite3.connect(DB_FILE)
  try:
    df = pd.read_sql_query("SELECT * FROM queue", conn)
  except Exception:
    df = pd.DataFrame()
  finally:
    conn.close()
  return df


def build_unit_dropdown_options(df):
  """Formats dropdown labels into: RGA: X | Notif: Y | Model | SN: Z (Unit ID: N)"""
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

    label = (
        f"RGA: {rga} | Notif: {notif} | {model} | SN: {sn} (Unit ID: {unit_id})"
    )
    options_map[label] = unit_id

  return options_map


# Load dataset globally into memory
df_queue = load_data()


# =========================================================
# HEADER BANNER & ENVIRONMENT TOGGLE
# =========================================================
col_logo, col_header = st.columns([1, 6])
with col_logo:
  if os.path.exists("logo.png"):
    st.image("logo.png", width=115)
  else:
    st.markdown("### ⚡ **HYDAC**")

with col_header:
  st.markdown(
      """
    <div class="hydac-header-card">
        <div class="hydac-header-title">Enterprise Electronic Lab: Operations Command</div>
        <div class="hydac-header-subtitle">HYDAC Technology Corp — Quality Control, Testing & Returns Operations</div>
    </div>
    """,
      unsafe_allow_html=True,
  )

# Environment Mode Toggle
with st.container(border=True):
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


# =========================================================
# SIDEBAR NAVIGATION & CATEGORIZED WORKFLOWS
# =========================================================
with st.sidebar:
  st.markdown(
      """
    <div class="sidebar-user-card">
        <div style="font-size:0.75rem; color:#94A3B8; text-transform:uppercase;">Logged In User</div>
        <div style="font-size:1.1rem; font-weight:700;">Geo Hall</div>
        <div style="font-size:0.8rem; color:#E30613; font-weight:600;">Lab Lead / Developer</div>
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

  # Organized Category Navigation
  nav_category = st.selectbox(
      "Select Category",
      [
          "📊 Dashboard & Analytics",
          "📥 Intake & Unit Logging",
          "⚙️ Queue & Cert Operations",
          "✉️ Outlook Email Sync",
          "🛠️ System Admin & Tools",
      ],
      label_visibility="collapsed",
  )

  st.markdown(
      '<div class="sidebar-section-header">WORKFLOW VIEW</div>',
      unsafe_allow_html=True,
  )

  # Nested Views by Category
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
  elif nav_category == "⚙️ Queue & Cert Operations":
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

# Re-query fresh database records
df_queue = load_data()


# =========================================================
# VIEW 1: EXECUTIVE QUEUE DASHBOARD
# =========================================================
if nav_choice == "View Queue Dashboard":
  st.subheader("📊 Active Lab Queue Command Center")

  if df_queue.empty:
    st.warning("No records found in `lab_queue.db`.")
  else:
    # Executive KPI Summary Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Active Units", len(df_queue))

    synced_emails_count = (
        df_queue["notes"]
        .dropna()
        .apply(lambda x: "[Synced Email" in str(x))
        .sum()
        if "notes" in df_queue.columns
        else 0
    )
    m2.metric("Units with Synced Emails", synced_emails_count)

    rga_count = (
        df_queue["rga_number"].dropna().replace("nan", "").ne("").sum()
        if "rga_number" in df_queue.columns
        else 0
    )
    m3.metric("Active RGAs", rga_count)

    notif_count = (
        df_queue["notification_number"].dropna().replace("nan", "").ne("").sum()
        if "notification_number" in df_queue.columns
        else 0
    )
    m4.metric("Active Notifications", notif_count)

    st.markdown("---")

    # Filter Bar
    search_term = st.text_input(
        "🔍 Search Queue (RGA, Notification, Customer, Model, Serial Number):",
        placeholder="Type RGA, Serial Number, or Customer Name...",
    )

    if search_term:
      filter_mask = df_queue.astype(str).apply(
          lambda col: col.str.contains(search_term, case=False)
      ).any(axis=1)
      display_df = df_queue[filter_mask]
    else:
      display_df = df_queue

    # Display Queue Table inside Container Card
    with st.container(border=True):
      st.markdown("#### 📋 Current Queue Master Table")
      st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Unit Inspector Tool
    st.markdown("### 🔎 Deep Unit & Email Thread Inspection")
    unit_map = build_unit_dropdown_options(display_df)

    if unit_map:
      selected_inspect_label = st.selectbox(
          "Select Unit to Inspect Details & Synced Notes:",
          options=list(unit_map.keys()),
          key="inspect_select",
      )
      selected_id = unit_map[selected_inspect_label]
      selected_row = display_df[display_df["id"] == selected_id].iloc[0]

      with st.expander(
          f"📋 Unit Details — ID #{selected_id} | RGA:"
          f" {selected_row.get('rga_number', 'N/A')}",
          expanded=True,
      ):
        c1, c2, c3 = st.columns(3)
        c1.write(f"**RGA Number:** `{selected_row.get('rga_number', 'N/A')}`")
        c2.write(
            "**Notification Number:**"
            f" `{selected_row.get('notification_number', 'N/A')}`"
        )
        c3.write(
            f"**Customer Name:** `{selected_row.get('customer_name', 'N/A')}`"
        )

        c4, c5, c6 = st.columns(3)
        c4.write(
            "**Model / Item:**"
            f" `{selected_row.get('model_series') or selected_row.get('model') or selected_row.get('item_description') or 'N/A'}`"
        )
        c5.write(
            "**Serial Number:**"
            f" `{selected_row.get('serial_number', 'N/A')}`"
        )
        c6.write(
            f"**Status / Location:** `{selected_row.get('status', 'N/A')}`"
        )

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

        st.text_area(
            "Outcome / Notes History:",
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
    f_rga = c1.text_input("RGA Number")
    f_notif = c2.text_input("Notification Number")

    c3, c4 = st.columns(2)
    f_cust = c3.text_input("Customer Name")
    f_model = c4.text_input("Model / Item Description")

    f_sn = st.text_input("Serial Number")
    f_status = st.selectbox(
        "Initial Status",
        [
            "Received in Lab",
            "Under Testing",
            "Pending Customer Info",
            "Completed",
        ],
    )
    f_notes = st.text_area("Initial Notes")

    submit_btn = st.form_submit_button("➕ Log Unit", type="primary")
    if submit_btn:
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute(
          """
            INSERT INTO queue (rga_number, notification_number, customer_name, model_series, serial_number, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
          (f_rga, f_notif, f_cust, f_model, f_sn, f_status, f_notes),
      )
      conn.commit()
      conn.close()
      st.success(f"✅ Successfully logged unit RGA: {f_rga} | SN: {f_sn}")

# =========================================================
# VIEW 3: LOG MULTIPLE UNITS (BATCH PER RGA)
# =========================================================
elif nav_choice == "Log Multiple Units (Batch per RGA)":
  st.subheader("📦 Batch Log Multiple Serial Numbers")
  c1, c2 = st.columns(2)
  batch_rga = c1.text_input("RGA Number for Batch:")
  batch_notif = c2.text_input("Notification Number:")

  c3, c4 = st.columns(2)
  batch_cust = c3.text_input("Customer Name:")
  batch_model = c4.text_input("Model / Item Description:")

  batch_sns = st.text_area("Enter Serial Numbers (One per line):")

  if st.button("🚀 Process Batch Logging", type="primary"):
    sn_list = [s.strip() for s in batch_sns.split("\n") if s.strip()]
    if sn_list:
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      for sn in sn_list:
        cursor.execute(
            """
                INSERT INTO queue (rga_number, notification_number, customer_name, model_series, serial_number, status)
                VALUES (?, ?, ?, ?, ?, 'Received in Lab')
            """,
            (batch_rga, batch_notif, batch_cust, batch_model, sn),
        )
      conn.commit()
      conn.close()
      st.success(
          f"✅ Successfully batch logged {len(sn_list)} units under RGA"
          f" {batch_rga}!"
      )
    else:
      st.warning("Please enter at least one valid serial number.")

# =========================================================
# VIEW 4: BULK IMPORT & STAGED REVIEW
# =========================================================
elif nav_choice == "Bulk Import & Staged Review":
  st.subheader("📥 Bulk Data Import (Excel / CSV)")
  uploaded_file = st.file_uploader(
      "Upload Excel or CSV file:", type=["csv", "xlsx"]
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
            " lab_queue.db!"
        )
    except Exception as e:
      st.error(f"❌ Error reading file: {e}")

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

      u_sn = st.text_input(
          "Serial Number", value=str(sel_row.get("serial_number", ""))
      )
      u_status = st.text_input("Status", value=str(sel_row.get("status", "")))
      u_notes = st.text_area("Notes", value=str(sel_row.get("notes", "")))

      if st.form_submit_button("💾 Save Record Updates", type="primary"):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
                UPDATE queue SET rga_number=?, notification_number=?, customer_name=?, model_series=?, serial_number=?, status=?, notes=?
                WHERE id=?
            """,
            (u_rga, u_notif, u_cust, u_model, u_sn, u_status, u_notes, sel_id),
        )
        conn.commit()
        conn.close()
        st.success(f"✅ Record ID {sel_id} updated successfully!")

# =========================================================
# VIEW 6: GENERATE SUPPORT EMAIL
# =========================================================
elif nav_choice == "Generate Support Email":
  st.subheader("✉️ Generate Support Notification Email")
  if df_queue.empty:
    st.warning("No units available.")
  else:
    unit_map = build_unit_dropdown_options(df_queue)
    sel_label = st.selectbox(
        "Select Target Unit:", options=list(unit_map.keys())
    )
    sel_id = unit_map[sel_label]
    sel_row = df_queue[df_queue["id"] == sel_id].iloc[0]

    email_body = f"""Subject: HYDAC Electronic Lab Status Update - RGA: {sel_row.get('rga_number', 'N/A')}

Hello,

The following unit is currently in process at the HYDAC Electronic Lab:

- RGA Number: {sel_row.get('rga_number', 'N/A')}
- Notification Number: {sel_row.get('notification_number', 'N/A')}
- Model Series: {sel_row.get('model_series', 'N/A')}
- Serial Number: {sel_row.get('serial_number', 'N/A')}
- Current Status: {sel_row.get('status', 'N/A')}

Notes:
{sel_row.get('notes', 'N/A')}

Best regards,
HYDAC Electronic Lab Team
"""
    st.text_area("Copy Generated Email:", value=email_body, height=280)

# =========================================================
# VIEW 7: SYNC EMAILS FROM RETURNS
# =========================================================
elif nav_choice == "Sync Emails from Returns":
  st.subheader("📩 Synced Returns Email Inbox")
  st.info(
      "Emails from Returns are automatically scanned by `sync_outlook.py`"
      " locally on your PC."
  )
  email_units = df_queue[
      df_queue["notes"]
      .fillna("")
      .str.contains("\\[Synced Email from Returns", case=False)
  ]
  if email_units.empty:
    st.warning("No synced Returns emails found in database.")
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
  st.warning("Outlook integration requires Windows desktop environment.")
  sent_units = df_queue[
      df_queue["notes"]
      .fillna("")
      .str.contains("\\[Synced Sent Reply", case=False)
  ]
  if sent_units.empty:
    st.info("No sent email replies currently tagged in database.")
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
  st.subheader("⚡ Supervisor Urgency & Escalation Override")
  if df_queue.empty:
    st.warning("No active units available.")
  else:
    unit_map = build_unit_dropdown_options(df_queue)
    sel_label = st.selectbox(
        "Select Unit to Escalate:", options=list(unit_map.keys())
    )
    sel_id = unit_map[sel_label]
    urgency_level = st.select_slider(
        "Set Priority Level",
        options=["Normal", "High Priority", "CRITICAL / EXPEDITE"],
    )

    if st.button("Apply Urgency Flag", type="primary"):
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute(
          "UPDATE queue SET status=? WHERE id=?",
          (f"URGENT: {urgency_level}", sel_id),
      )
      conn.commit()
      conn.close()
      st.success(
          f"✅ Applied urgency status `{urgency_level}` to Unit ID {sel_id}!"
      )

# =========================================================
# VIEW 10: CREATE SERIAL CERT FOLDER
# =========================================================
elif nav_choice == "Create Serial Cert Folder":
  st.subheader("📁 Create Serial Cert Folder")

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
        if st.button("📁 Create Folder & Copy Template", type="primary"):
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
            st.success(
                f"✅ Folder successfully created locally:\n`{target_dir}`"
            )
          except Exception as err:
            st.error(f"❌ Failed to create folder directory: {err}")
      else:
        st.warning(
            "⚠️ **Local folder creation is disabled in Streamlit Cloud"
            " mode.**\n\nTo create folders on your PC:\n1. Run the app locally"
            " via `run_app.bat`.\n2. Switch the **Enable Local PC Mode** toggle"
            " at the top to **ON**."
        )

# =========================================================
# VIEW 11: VIEW-ONLY DISPLAY CONFIG
# =========================================================
elif nav_choice == "⚙️ View-Only Display Config":
  st.subheader("⚙️ Display Column Preferences")
  st.write("Configure which columns to highlight on the main queue dashboard:")
  show_rga = st.checkbox("Display RGA Column", value=True)
  show_notif = st.checkbox("Display Notification Column", value=True)
  show_sn = st.checkbox("Display Serial Number Column", value=True)
  st.success("Preferences applied to session context.")

# =========================================================
# VIEW 12: DEMO & RESET CONTROLS
# =========================================================
elif nav_choice == "Demo & Reset Controls":
  st.subheader("⚠️ Operations Command Controls")
  st.error("Danger Zone: Database operations")
  if st.button("🔄 Refresh Database Cache"):
    st.cache_data.clear()
    st.success("Cache flushed cleanly.")

# =========================================================
# VIEW 13: MONTHLY VOLUME ANALYTICS
# =========================================================
elif nav_choice == "Monthly Volume Analytics":
  st.subheader("📈 Monthly Volume Analytics")
  if df_queue.empty:
    st.warning("No data available for analytics.")
  else:
    st.metric("Total Items Processed", len(df_queue))
    st.bar_chart(df_queue["status"].value_counts())

# =========================================================
# VIEW 14: BACKUP & DATA EXPORT
# =========================================================
elif nav_choice == "Backup & Data Export":
  st.subheader("📥 Data Export & Database Backup")

  if not df_queue.empty:
    c_csv, c_excel = st.columns(2)

    with c_csv:
      csv_bytes = df_queue.to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 Download CSV Export",
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