import os
import tempfile
import base64
import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
import altair as alt
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from risk_assessment.extract_pdf import extract_clauses
from risk_assessment.analyze_clauses import analyze_all_batches
from risk_assessment.notification_alert import send_compliance_alert

from config import ModelManager

# Load environment variables
#load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS — Modern SaaS Dashboard Style
# ─────────────────────────────────────────────────────────────────────────────
def add_custom_style():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%) !important;
        min-height: 100vh;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%) !important;
        border-right: 1px solid rgba(99, 102, 241, 0.2) !important;
        padding-top: 1.5rem;
    }
    [data-testid="stSidebar"] .block-container { padding: 0 1rem; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stRadio label { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stRadio > div { gap: 0.4rem; }
    [data-testid="stSidebar"] .stRadio [data-baseweb="radio"] label {
        background: rgba(99, 102, 241, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 10px;
        padding: 0.55rem 1rem;
        transition: all 0.2s ease;
        color: #cbd5e1 !important;
        font-size: 0.9rem;
        width: 100%;
    }
    [data-testid="stSidebar"] .stRadio [data-baseweb="radio"] label:hover {
        background: rgba(99, 102, 241, 0.2);
        border-color: rgba(99, 102, 241, 0.4);
        color: #fff !important;
    }
    [data-testid="stSidebar"] .stRadio [aria-checked="true"] ~ label,
    [data-testid="stSidebar"] .stRadio [data-baseweb="radio"]:has(input:checked) label {
        background: linear-gradient(135deg, rgba(99,102,241,0.35), rgba(139,92,246,0.35)) !important;
        border-color: rgba(99, 102, 241, 0.6) !important;
        color: #fff !important;
        font-weight: 600;
    }
    [data-testid="stSidebar"] .stInfo {
        background: rgba(99, 102, 241, 0.1) !important;
        border: 1px solid rgba(99, 102, 241, 0.25) !important;
        border-radius: 10px;
        color: #94a3b8 !important;
        font-size: 0.85rem;
    }

    .block-container {
        padding: 1.5rem 2rem 3rem 2rem !important;
        max-width: 1200px;
    }

    .dashboard-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 20px 60px rgba(99, 102, 241, 0.35);
        position: relative;
        overflow: hidden;
    }
    .dashboard-header::before {
        content: '';
        position: absolute;
        top: -50%; right: -10%;
        width: 400px; height: 400px;
        background: rgba(255,255,255,0.05);
        border-radius: 50%;
    }
    .dashboard-header h1 {
        color: #ffffff !important;
        font-size: 1.9rem !important;
        font-weight: 800 !important;
        margin: 0 0 0.5rem 0 !important;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    .dashboard-header p {
        color: rgba(255,255,255,0.85) !important;
        font-size: 1rem !important;
        margin: 0 !important;
        line-height: 1.6;
        max-width: 650px;
    }

    h2, h3 { color: #e2e8f0 !important; font-weight: 700 !important; letter-spacing: -0.3px; }

    [data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.9) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 16px !important;
        padding: 1.2rem 1.4rem !important;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 32px rgba(99,102,241,0.25) !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricLabel"] {
        color: #94a3b8 !important; font-size: 0.8rem !important;
        font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.5px;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #f1f5f9 !important; font-size: 2rem !important; font-weight: 800 !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricDelta"] {
        color: #64748b !important; font-size: 0.78rem !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: #ffffff !important; border: none !important;
        border-radius: 12px !important; padding: 0.65rem 1.4rem !important;
        font-size: 0.92rem !important; font-weight: 600 !important;
        letter-spacing: 0.2px;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.55) !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 10px rgba(99, 102, 241, 0.4) !important;
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, #0ea5e9, #06b6d4) !important;
        color: #ffffff !important; border: none !important;
        border-radius: 12px !important; padding: 0.6rem 1.2rem !important;
        font-size: 0.88rem !important; font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(6, 182, 212, 0.35) !important;
        transition: all 0.25s ease !important;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #0284c7, #0891b2) !important;
        box-shadow: 0 8px 25px rgba(6, 182, 212, 0.5) !important;
        transform: translateY(-2px) !important;
    }

    [data-testid="stFileUploader"] {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 2px dashed rgba(99, 102, 241, 0.4) !important;
        border-radius: 16px !important; padding: 1.5rem !important;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(99, 102, 241, 0.8) !important;
        background: rgba(99, 102, 241, 0.08) !important;
    }
    [data-testid="stFileUploader"] label { color: #94a3b8 !important; font-size: 0.9rem; }

    [data-testid="stDataFrame"] {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 16px !important; overflow: hidden;
    }
    iframe[title="st_aggrid"] { border-radius: 16px !important; }

    [data-testid="stSelectbox"] > div > div {
        background: rgba(30, 41, 59, 0.9) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 10px !important; color: #e2e8f0 !important;
    }
    [data-testid="stSelectbox"] label {
        color: #94a3b8 !important; font-size: 0.85rem !important; font-weight: 600;
    }

    [data-testid="stTextInput"] input {
        background: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 10px !important; color: #e2e8f0 !important;
        padding: 0.65rem 1rem !important; font-size: 0.92rem;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: rgba(99, 102, 241, 0.7) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    }
    [data-testid="stTextInput"] label {
        color: #94a3b8 !important; font-size: 0.85rem !important; font-weight: 600;
    }

    .stAlert { border-radius: 12px !important; border: none !important; font-size: 0.92rem !important; }
    [data-testid="stInfo"] {
        background: rgba(6, 182, 212, 0.1) !important;
        border-left: 4px solid #06b6d4 !important;
        color: #7dd3fc !important; border-radius: 12px !important;
    }
    [data-testid="stSuccess"] {
        background: rgba(34, 197, 94, 0.1) !important;
        border-left: 4px solid #22c55e !important;
        color: #86efac !important; border-radius: 12px !important;
    }
    [data-testid="stError"] {
        background: rgba(239, 68, 68, 0.1) !important;
        border-left: 4px solid #ef4444 !important;
        color: #fca5a5 !important; border-radius: 12px !important;
    }
    [data-testid="stWarning"] {
        background: rgba(234, 179, 8, 0.1) !important;
        border-left: 4px solid #eab308 !important;
        color: #fde047 !important; border-radius: 12px !important;
    }

    [data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
        border-radius: 100px !important;
    }
    [data-testid="stProgress"] > div {
        background: rgba(99, 102, 241, 0.15) !important;
        border-radius: 100px !important; height: 6px !important;
    }

    [data-testid="stSpinner"] { color: #6366f1 !important; }

    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 14px !important; overflow: hidden;
    }
    [data-testid="stExpander"] summary {
        color: #e2e8f0 !important; font-weight: 600 !important;
        font-size: 0.95rem !important; padding: 1rem 1.2rem !important;
    }
    [data-testid="stExpander"] summary:hover { background: rgba(99, 102, 241, 0.08) !important; }
    [data-testid="stExpander"] > div > div { padding: 0 1.2rem 1.2rem 1.2rem !important; }

    [data-testid="stForm"] {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 16px !important; padding: 1.5rem !important;
    }

    hr { border-color: rgba(99, 102, 241, 0.2) !important; margin: 1.5rem 0 !important; }

    .stCaption, caption, small { color: #64748b !important; font-size: 0.82rem !important; }

    .section-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 18px;
        padding: 1.5rem 1.5rem 1rem 1.5rem;
        margin-bottom: 1.2rem;
        backdrop-filter: blur(10px);
    }
    .section-card h3 {
        margin-top: 0 !important; font-size: 1.05rem !important;
        color: #e2e8f0 !important; font-weight: 700 !important;
    }

    .badge-high {
        display: inline-block; background: rgba(239,68,68,0.15); color: #fca5a5;
        border: 1px solid rgba(239,68,68,0.35); border-radius: 100px;
        padding: 2px 12px; font-size: 0.78rem; font-weight: 600;
    }
    .badge-medium {
        display: inline-block; background: rgba(234,179,8,0.15); color: #fde047;
        border: 1px solid rgba(234,179,8,0.35); border-radius: 100px;
        padding: 2px 12px; font-size: 0.78rem; font-weight: 600;
    }
    .badge-low {
        display: inline-block; background: rgba(34,197,94,0.15); color: #86efac;
        border: 1px solid rgba(34,197,94,0.35); border-radius: 100px;
        padding: 2px 12px; font-size: 0.78rem; font-weight: 600;
    }

    .gsheet-btn a button { transition: all 0.25s ease !important; }
    .gsheet-btn a button:hover { opacity: 0.88; transform: translateY(-2px); }

    .sidebar-logo {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        border-radius: 12px; padding: 0.85rem 1rem;
        margin-bottom: 1.2rem; text-align: center;
    }
    .sidebar-logo span { color: #fff; font-size: 1rem; font-weight: 700; letter-spacing: 0.3px; }

    .upload-label { color: #e2e8f0; font-size: 0.95rem; font-weight: 500; margin-bottom: 0.5rem; }

    .loader-overlay {
        position: fixed; top: 0; left: 0;
        width: 100%; height: 100%;
        background: linear-gradient(135deg, #0f172a, #1e293b);
        display: flex; flex-direction: column;
        justify-content: center; align-items: center; z-index: 9999;
    }
    .loader-overlay .loader-title { color: #e2e8f0; font-size: 1.8rem; font-weight: 700; margin-top: 1.5rem; }
    .loader-overlay .loader-sub { color: #64748b; font-size: 1rem; margin-top: 0.5rem; }

    .vega-embed { background: transparent !important; }

    .stSubheader, [data-testid="stSubheader"] {
        color: #e2e8f0 !important; font-size: 1.1rem !important; font-weight: 700 !important;
        border-bottom: 2px solid rgba(99,102,241,0.3);
        padding-bottom: 0.4rem; margin-bottom: 0.8rem;
    }

    </style>
    """, unsafe_allow_html=True)


def add_background_image():
    image_path = "images/bgimg.png"
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
        """, unsafe_allow_html=True)


add_custom_style()
add_background_image()

# ─────────────────────────────────────────────────────────────────────────────
# Google Sheets
# ─────────────────────────────────────────────────────────────────────────────
GOOGLE_AUTH_FILE = "services.json"
GSHEET_ID = st.secrets["GSHEET_ID"]
SHEET_NAME = "Sheet1"

import json

google_creds = json.loads(st.secrets["GOOGLE_CREDENTIALS"])

creds = Credentials.from_service_account_info(
    google_creds,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gs_client = gspread.Client(auth=creds)          # ✅ fixed: was gspread.authorize()
spreadsheet = gs_client.open_by_key(GSHEET_ID)

if "sheet_cleared" not in st.session_state:
    for ws in spreadsheet.worksheets():
        if ws.title != "Sheet1":
            ws.clear()
    st.session_state.sheet_cleared = True

# ─────────────────────────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "upload"
if "clauses" not in st.session_state:
    st.session_state.clauses = None
if "results" not in st.session_state:
    st.session_state.results = None
if "df" not in st.session_state:
    st.session_state.df = None
if "contracts" not in st.session_state:
    st.session_state.contracts = {}
if "current_contract" not in st.session_state:
    st.session_state.current_contract = None

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
def show_sidebar():
    st.sidebar.markdown("""
    <div class="sidebar-logo">
        <span>📑 Compliance Checker</span>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(
        "<p style='color:#64748b;font-size:0.75rem;font-weight:600;text-transform:uppercase;"
        "letter-spacing:1px;margin-bottom:0.6rem;padding-left:0.2rem;'>Previous Contracts</p>",
        unsafe_allow_html=True
    )

    if st.session_state.contracts:
        contract_names = list(st.session_state.contracts.keys())
        options_with_icons = [f"📄 {name}" for name in contract_names]

        selected_with_icon = st.sidebar.radio(
            "Select a contract:",
            options=options_with_icons,
            index=contract_names.index(st.session_state.current_contract)
            if st.session_state.current_contract in contract_names else 0,
            label_visibility="collapsed"
        )

        selected = selected_with_icon[2:]

        if selected != st.session_state.current_contract:
            contract = st.session_state.contracts[selected]
            st.session_state.current_contract = selected
            st.session_state.df = contract["df"]
            st.session_state.clauses = contract["clauses"]
            st.session_state.results = contract["results"]
            st.session_state.page = "results"
            st.session_state.email_status = None
            st.session_state.email_status_type = None
            st.session_state.show_rewrites = False
            st.rerun()
    else:
        st.sidebar.info("No previous contracts yet.")

    st.sidebar.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(
        "<p style='color:#334155;font-size:0.75rem;text-align:center;'>AI Compliance Checker v1.0</p>",
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────────────────────────────────────
# Header (Upload Page)
# ─────────────────────────────────────────────────────────────────────────────
def show_header():
    st.markdown("""
    <div class="dashboard-header">
        <h1>📑 AI Powered Regulatory Compliance Checker</h1>
        <p>
            Upload a contract in PDF format to automatically extract clauses,
            assess regulatory risks, and receive AI-powered compliance recommendations for improvement.
        </p>
    </div>
    """, unsafe_allow_html=True)

    image_path = "images/headimg.png"
    if os.path.exists(image_path):
        st.markdown(
            f"""
            <div style="text-align:center; margin: 1.5rem 0;">
                <img src="data:image/png;base64,{base64.b64encode(open(image_path, 'rb').read()).decode()}"
                     style="width:580px; max-width:92%; border-radius:16px;
                            box-shadow: 0 20px 60px rgba(0,0,0,0.5);" />
            </div>
            """,
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────────────────────────────────────
# PDF Export Helper
# ─────────────────────────────────────────────────────────────────────────────
def generate_rewritten_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>AI-Rewritten Contract Clauses Report</b>", styles["Title"]))
    story.append(Spacer(1, 20))

    for _, row in df.iterrows():
        clause_id = row["Clause ID"]
        original = row["Contract Clause"]
        risk_level = row.get("Risk Level", "Unknown")
        modified = row.get("AI-Modified Clause", "⚠️ Not available")
        modified_risk = row.get("AI-Modified Risk Level", "Unknown")

        story.append(Paragraph(f"<b>Clause ID:</b> {clause_id}", styles["Heading2"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Original Risk Level:</b> {risk_level}", styles["Normal"]))
        story.append(Paragraph(f"<b>Original Clause:</b> {original}", styles["Normal"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>AI-Modified Clause:</b> {modified}", styles["Normal"]))
        story.append(Paragraph(f"<b>AI-Modified Risk Level:</b> {modified_risk}", styles["Normal"]))
        story.append(Spacer(1, 15))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Email Modal
# ─────────────────────────────────────────────────────────────────────────────
def email_modal(high, medium, low, gsheet_url):
    if "recipient_email" not in st.session_state:
        st.session_state.recipient_email = ""
    if "reset_email_field" not in st.session_state:
        st.session_state.reset_email_field = False

    if st.session_state.reset_email_field:
        st.session_state.recipient_email = ""
        st.session_state.reset_email_field = False

    with st.form("email_form", clear_on_submit=True):
        st.markdown("### ✉️ Send Compliance Alert")
        st.caption("Enter recipient email or leave blank to use default compliance analyst.")

        recipient_email = st.text_input(
            "Recipient Email (optional)",
            key="recipient_email",
            placeholder="example@company.com"
        )

        col1, col2 = st.columns([1, 1])
        send_btn = col1.form_submit_button("📧 Send")
        cancel_btn = col2.form_submit_button("❌ Cancel")

        if send_btn:
            pdf_path = "ai_modified_clauses.pdf"
            pdf_data = generate_rewritten_pdf(st.session_state.df)
            with open(pdf_path, "wb") as f:
                f.write(pdf_data)

            success, msg = send_compliance_alert(
                subject="Compliance Risk Report",
                high_risk_count=high,
                medium_risk_count=medium,
                low_risk_count=low,
                gsheet_link=gsheet_url,
                recipient=recipient_email if recipient_email else None,
                contract_name=st.session_state.current_contract,
                contract_description=generate_contract_summary(st.session_state.df, st.session_state.current_contract),
                total_clauses=len(st.session_state.df),
                ai_modified_filepaths=[pdf_path] if os.path.exists(pdf_path) else []
            )

            if success:
                st.success(f"✅ Email sent to {recipient_email if recipient_email else 'default compliance analyst'}.")
                st.session_state.show_email_modal = False
                st.session_state.reset_email_field = True
                st.rerun()
            else:
                st.error(f"⚠️ Failed to send: {msg}")

        elif cancel_btn:
            st.session_state.show_email_modal = False
            st.session_state.reset_email_field = True
            st.info("❌ Email sending cancelled.")
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Upload Page
# ─────────────────────────────────────────────────────────────────────────────
def upload_page():
    show_sidebar()
    show_header()

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<p class='upload-label'>📁 Upload your contract document</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload PDF contract", type=["pdf"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    batch_size = 5

    if uploaded_file:
        st.session_state.clauses = None
        st.session_state.results = None
        st.session_state.df = None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        st.info("📂 Extracting clauses from your contract...")
        st.session_state.clauses = extract_clauses(tmp_path)

        with st.spinner("Analyzing clauses with AI..."):
            progress = st.progress(0)
            results = []
            for i in range(0, len(st.session_state.clauses), batch_size):
                batch = st.session_state.clauses[i:i + batch_size]
                batch_results = analyze_all_batches(batch, start_id=i + 1, batch_size=batch_size)
                results.extend(batch_results)
                progress.progress(min((i + batch_size) / len(st.session_state.clauses), 1.0))
            progress.empty()
            st.success("✅ Analysis completed successfully!")
            st.session_state.results = results

        df = pd.DataFrame(st.session_state.results)
        df["Risk Score"] = df.get("Risk Score", "0%").fillna("0%")
        st.session_state.df = df

        # Save contract to session state FIRST (GSheets failure won't block navigation)
        new_name = f"Contract {len(st.session_state.contracts) + 1}"
        st.session_state.contracts[new_name] = {
            "df": st.session_state.df.copy(),
            "clauses": st.session_state.clauses.copy(),
            "results": st.session_state.results.copy()
        }
        st.session_state.current_contract = new_name

        # Try to sync to Google Sheets (non-fatal)
        try:
            rows = [st.session_state.df.columns.tolist()] + st.session_state.df.astype(str).values.tolist()

            try:
                ws = gs_client.open_by_key(GSHEET_ID).worksheet(new_name)
                ws.clear()
            except gspread.exceptions.WorksheetNotFound:
                ws = gs_client.open_by_key(GSHEET_ID).add_worksheet(title=new_name, rows="1000", cols="20")

            ws.update(rows, "A1")          # ✅ fixed: was ws.update("A1", rows)

        except Exception as e:
            st.warning(f"⚠ Google Sheets sync failed (results still saved locally): {e}")

        st.markdown("""
        <div class="loader-overlay">
            <div style="font-size:3rem;">⏳</div>
            <div class="loader-title">Loading Results...</div>
            <div class="loader-sub">Preparing your compliance report</div>
        </div>
        """, unsafe_allow_html=True)

        st.session_state.page = "results"
        st.rerun()

    if st.session_state.df is not None and not st.session_state.df.empty:
        col1, col2, col3 = st.columns([6, 2, 1])
        with col3:
            if st.button("➡ Go to Results", key="go_to_results"):
                st.session_state.page = "results"
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Results Page
# ─────────────────────────────────────────────────────────────────────────────
def results_page():
    show_sidebar()

    df = st.session_state.df
    if df is None or df.empty:
        st.error("No data available.")
        return

    st.markdown("""
    <div class="dashboard-header">
        <h1>📊 Compliance Risk Analysis Results</h1>
        <p>
            Your contract has been analyzed clause-by-clause. Review the compliance risks,
            distribution overview, and AI-generated recommendations below.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='margin-bottom:0.4rem;'>
        <span style='color:#94a3b8;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;'>
        Key Metrics
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.caption("These metrics summarize the overall compliance profile of your contract.")

    high = df[df["Risk Level"] == "High"].shape[0]
    medium = df[df["Risk Level"] == "Medium"].shape[0]
    low = df[df["Risk Level"] == "Low"].shape[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📄 Total Clauses", len(df))
    col2.metric("🔴 High Risk", high, "Clauses with high compliance risk")
    col3.metric("🟡 Medium Risk", medium, "Clauses with moderate compliance risk")
    col4.metric("🟢 Low Risk", low, "Clauses with low compliance risk")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Charts ──
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("""
    <p style='color:#94a3b8;font-size:0.75rem;font-weight:600;text-transform:uppercase;
    letter-spacing:1px;margin-bottom:0.2rem;'>Risk Level Distribution</p>
    """, unsafe_allow_html=True)
    st.caption("Overview of how clauses are distributed across High, Medium, and Low risk levels.")

    risk_counts = df["Risk Level"].value_counts().reindex(["High", "Medium", "Low"], fill_value=0).reset_index()
    risk_counts.columns = ["Risk Level", "Count"]

    color_scale = alt.Scale(domain=["High", "Medium", "Low"], range=["#ef4444", "#eab308", "#22c55e"])

    bar_chart = (
        alt.Chart(risk_counts)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("Risk Level:N", sort=["High", "Medium", "Low"],
                    axis=alt.Axis(labelColor="#94a3b8", titleColor="#94a3b8", grid=False)),
            y=alt.Y("Count:Q",
                    axis=alt.Axis(labelColor="#94a3b8", titleColor="#94a3b8", grid=True,
                                  gridColor="rgba(99,102,241,0.1)")),
            color=alt.Color("Risk Level:N", scale=color_scale, legend=None),
            tooltip=["Risk Level", "Count"]
        )
        .properties(width=350, height=320)
        .configure_view(fill="transparent", stroke="transparent")
        .configure_axis(labelFontSize=12, titleFontSize=12)
    )

    pie_chart = (
        alt.Chart(risk_counts)
        .mark_arc(innerRadius=55, outerRadius=130)
        .encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color("Risk Level:N", scale=color_scale,
                            legend=alt.Legend(labelColor="#94a3b8", titleColor="#94a3b8")),
            tooltip=["Risk Level", "Count"]
        )
        .properties(width=350, height=320)
        .configure_view(fill="transparent", stroke="transparent")
    )

    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(bar_chart, use_container_width=True)
    with col2:
        st.altair_chart(pie_chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Clause Analysis ──
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("""
    <p style='color:#94a3b8;font-size:0.75rem;font-weight:600;text-transform:uppercase;
    letter-spacing:1px;margin-bottom:0.2rem;'>Clause Analysis</p>
    """, unsafe_allow_html=True)

    desc_col, filter_col = st.columns([7, 2])
    with desc_col:
        st.caption(
            "Breakdown of each extracted clause with its assessed risk level. "
            "Use the filter to focus on a specific risk category."
        )
    with filter_col:
        filter_option = st.selectbox(
            "Filter Risk Level",
            options=["All", "High", "Medium", "Low"],
            index=0,
            label_visibility="collapsed"
        )

    if filter_option != "All":
        filtered_df = df[df["Risk Level"] == filter_option]
    else:
        filtered_df = df

    analysis_df = filtered_df.drop(columns=["AI-Modified Clause", "AI-Modified Risk Level"], errors="ignore")
    st.dataframe(analysis_df, use_container_width=True, height=420)

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download Filtered Clause Analysis CSV",
        data=csv,
        file_name="clause_analysis.csv",
        mime="text/csv"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── AI-Modified Clauses ──
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("""
    <p style='color:#94a3b8;font-size:0.75rem;font-weight:600;text-transform:uppercase;
    letter-spacing:1px;margin-bottom:0.2rem;'>⚡ AI-Modified Clauses</p>
    """, unsafe_allow_html=True)
    st.caption("High-risk clauses can be minimized by reviewing AI suggestions below.")

    if "show_rewrites" not in st.session_state:
        st.session_state.show_rewrites = False

    if not st.session_state.show_rewrites:
        st.markdown(
            "<div style='color:#94a3b8;margin-bottom:0.8rem;font-size:0.9rem;'>"
            "Do you want AI suggestions to minimize high-risk clauses? Click the button below.</div>",
            unsafe_allow_html=True
        )
        if st.button("⚡ Give AI-Modified Clauses"):
            st.session_state.show_rewrites = True
            st.rerun()

    if st.session_state.show_rewrites:
        high_risk_df = df[df["Risk Level"] == "High"].copy()

        if not high_risk_df.empty:
            if "AI-Modified Clause" not in high_risk_df.columns:
                high_risk_df["AI-Modified Clause"] = "⚠️ No rewritten version available"
            if "Clause Feedback & Fix" not in high_risk_df.columns:
                high_risk_df["Clause Feedback & Fix"] = "No feedback available"
            if "AI-Modified Risk Level" not in high_risk_df.columns:
                high_risk_df["AI-Modified Risk Level"] = "Unknown"

            keep_cols = ["Clause ID", "Contract Clause", "Risk Level", "AI-Modified Clause", "AI-Modified Risk Level"]
            sugg_df = high_risk_df[[c for c in keep_cols if c in high_risk_df.columns]]

            with st.expander("⚡ AI-Modified Clauses (click to expand)"):
                st.dataframe(sugg_df, use_container_width=True, height=400)

                sugg_csv = sugg_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇ Download AI-Modified Clauses CSV",
                    data=sugg_csv,
                    file_name="ai_modified_clauses.csv",
                    mime="text/csv"
                )

                pdf_data = generate_rewritten_pdf(sugg_df)
                st.download_button(
                    "📄 Download AI-Modified Clauses PDF",
                    data=pdf_data,
                    file_name="ai_Modified_clauses.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("✅ No high-risk clauses to rewrite.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Google Sheets Button ──
    current_name = st.session_state.current_contract

    try:
        ws = gs_client.open_by_key(GSHEET_ID).worksheet(current_name)
        gsheet_url = f"https://docs.google.com/spreadsheets/d/{GSHEET_ID}/edit#gid={ws.id}"
    except gspread.exceptions.WorksheetNotFound:
        gsheet_url = f"https://docs.google.com/spreadsheets/d/{GSHEET_ID}/edit"

    st.markdown(f"""
    <div class="gsheet-btn" style="margin: 1rem 0 0.5rem 0;">
        <a href="{gsheet_url}" target="_blank" style="text-decoration:none;">
            <button style="
                font-size: 0.95rem; font-weight: 600;
                background: linear-gradient(135deg, #4285F4, #1a73e8);
                color: white; padding: 0.7rem 1.4rem;
                border-radius: 12px; border: none; cursor: pointer;
                box-shadow: 0 4px 15px rgba(66, 133, 244, 0.4);
                transition: all 0.25s ease; letter-spacing: 0.2px;
            ">
                📊 View Full Report in Google Sheets
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # ── Email Compliance Alert ──
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("📧 Compliance Alert")

    pdf_path = "ai_modified_clauses.pdf"
    pdf_data = generate_rewritten_pdf(df)
    with open(pdf_path, "wb") as f:
        f.write(pdf_data)

    if "email_status" not in st.session_state:
        st.session_state.email_status = None
    if "email_status_type" not in st.session_state:
        st.session_state.email_status_type = None

    if st.button("📨 Send to Compliance Officer"):
        with st.spinner("Sending email..."):
            success, msg = send_compliance_alert(
                subject="Compliance Risk Report",
                high_risk_count=high,
                medium_risk_count=medium,
                low_risk_count=low,
                gsheet_link=gsheet_url,
                recipient=None,
                contract_name=current_name,
                contract_description=generate_contract_summary(df, current_name),
                total_clauses=len(df),
                ai_modified_filepaths=[pdf_path] if os.path.exists(pdf_path) else []
            )
        if success:
            st.session_state.email_status = "✅ Email sent successfully to the compliance officer."
            st.session_state.email_status_type = "success"
        else:
            st.session_state.email_status = f"⚠️ Failed to send email: {msg}"
            st.session_state.email_status_type = "error"
        st.rerun()

    if st.session_state.email_status:
        if st.session_state.email_status_type == "success":
            st.success(st.session_state.email_status)
        else:
            st.error(st.session_state.email_status)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    with st.expander("✉️ Send to Another Recipient", expanded=False):
        email_modal(high, medium, low, gsheet_url)

    # ── Back Button ──
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([6, 2, 1])
    with col3:
        if st.button("⬅ Go Back", key="back_to_upload"):
            st.session_state.page = "upload"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Contract Summary
# ─────────────────────────────────────────────────────────────────────────────
def generate_contract_summary(df, contract_name: str) -> str:
    high = df[df["Risk Level"] == "High"].shape[0]
    medium = df[df["Risk Level"] == "Medium"].shape[0]
    low = df[df["Risk Level"] == "Low"].shape[0]
    total = len(df)
    summary = f"Contract '{contract_name}' contains {total} clauses: "
    summary += f"{high} high risk, {medium} medium risk, {low} low risk. "
    return summary.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.page == "upload":
    upload_page()
elif st.session_state.page == "results":
    results_page()



    
