"""
CrimeVision AI – Main Application Entry Point
Intelligent Multimodal Forensic Analysis Platform
Skill Wallet Capstone Project 2
"""
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv()

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="CrimeVision AI | Forensic Analysis Platform",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help":     "https://github.com/crimevision-ai",
        "Report a bug": None,
        "About":        "CrimeVision AI v2.0 – Skill Wallet Capstone Project 2",
    },
)

# ── Imports (after page config) ───────────────────────────────────────────────
from config.settings import (
    APP_NAME, APP_SUBTITLE, APP_VERSION, PROJECT_LABEL,
    generate_evidence_id, build_custody_record, generate_case_hash,
)
from utils.ui_helpers import inject_css, app_header, chain_of_custody_sidebar, cv_divider
from utils.groq_client import GroqClient
from utils.evidence_store import get_all_evidence

from modules.image_analysis import render_image_tab
from modules.audio_analysis  import render_audio_tab
from modules.video_analysis  import render_video_tab
from modules.fusion          import render_fusion_tab
from modules.pdf_report      import render_pdf_tab


# ── CSS ───────────────────────────────────────────────────────────────────────
inject_css()


# ── Session state initialisation ─────────────────────────────────────────────

def _init_session():
    defaults = {
        "groq_api_key":      os.getenv("GROQ_API_KEY", ""),
        "case_id":           generate_evidence_id("CASE"),
        "investigator":      "Det. J. Smith",
        "active_custody":    None,
        "evidence_store":    {"image": [], "audio": [], "video": [], "fusion": []},
        "chat_history":      [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_session()


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:

    # Branding
    st.markdown(f"""
    <div style="text-align:center; padding:1rem 0 0.5rem;">
        <div style="font-size:2rem; margin-bottom:0.3rem;">⚖️</div>
        <div style="font-size:0.85rem; font-weight:800; color:#FFFFFF; letter-spacing:0.06em;">
            CRIMEVISION AI
        </div>
        <div style="font-size:0.62rem; color:#607080; letter-spacing:0.1em; text-transform:uppercase;">
            {PROJECT_LABEL}
        </div>
        <div style="font-size:0.6rem; color:#1A3060; margin-top:0.3rem;">v{APP_VERSION}</div>
    </div>
    <hr style="border:none; border-top:1px solid #1A2840; margin:0.75rem 0;">
    """, unsafe_allow_html=True)

    # ── API Key ────────────────────────────────────────────────────────────────
    st.markdown('<div style="font-size:0.68rem; font-weight:700; letter-spacing:0.1em; '
                'text-transform:uppercase; color:#607080; margin-bottom:0.4rem;">🔑 API Configuration</div>',
                unsafe_allow_html=True)

    api_key = st.text_input(
        "Groq API Key",
        value=st.session_state.groq_api_key,
        type="password",
        placeholder="gsk_...",
        help="Get a free key at console.groq.com. Leave blank for demo mode.",
        key="_api_key_input",
    )
    st.session_state.groq_api_key = api_key

    # Instantiate client
    client = GroqClient(api_key=api_key)

    if client.demo_mode:
        st.markdown("""
        <div style="background:rgba(255,165,0,0.08); border:1px solid rgba(255,165,0,0.25);
                    border-radius:6px; padding:0.5rem 0.75rem; font-size:0.72rem; color:#FFA500;">
            ⚠️ <strong>DEMO MODE</strong> — Simulated forensic data active.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(0,255,136,0.06); border:1px solid rgba(0,255,136,0.2);
                    border-radius:6px; padding:0.5rem 0.75rem; font-size:0.72rem; color:#00FF88;">
            ✅ <strong>GROQ API CONNECTED</strong>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr style="border:none; border-top:1px solid #1A2840; margin:0.75rem 0;">', unsafe_allow_html=True)

    # ── Case Settings ──────────────────────────────────────────────────────────
    st.markdown('<div style="font-size:0.68rem; font-weight:700; letter-spacing:0.1em; '
                'text-transform:uppercase; color:#607080; margin-bottom:0.4rem;">🗂 Case Settings</div>',
                unsafe_allow_html=True)

    case_id = st.text_input(
        "Case / Evidence ID",
        value=st.session_state.case_id,
        key="_case_id_input",
    )
    st.session_state.case_id = case_id

    investigator = st.text_input(
        "Lead Investigator",
        value=st.session_state.investigator,
        key="_investigator_input",
    )
    st.session_state.investigator = investigator

    # ── Chain of Custody ───────────────────────────────────────────────────────
    st.markdown('<hr style="border:none; border-top:1px solid #1A2840; margin:0.75rem 0;">', unsafe_allow_html=True)

    custody = build_custody_record(case_id, investigator, "CrimeVision AI Platform")
    chain_of_custody_sidebar(custody)

    st.markdown('<hr style="border:none; border-top:1px solid #1A2840; margin:0.75rem 0;">', unsafe_allow_html=True)

    # ── Evidence Counter ───────────────────────────────────────────────────────
    all_ev = get_all_evidence()
    img_n  = sum(1 for r in all_ev if r["type"] == "IMAGE")
    aud_n  = sum(1 for r in all_ev if r["type"] == "AUDIO")
    vid_n  = sum(1 for r in all_ev if r["type"] == "VIDEO")

    st.markdown(f"""
    <div style="font-size:0.68rem; font-weight:700; letter-spacing:0.1em;
                text-transform:uppercase; color:#607080; margin-bottom:0.6rem;">
        📦 Evidence Collected
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.4rem; margin-bottom:0.5rem;">
        <div style="background:#0A1628; border:1px solid #1A2840; border-radius:6px;
                    padding:0.5rem; text-align:center;">
            <div style="font-family:'JetBrains Mono',monospace; font-size:1.1rem;
                        color:#00D4FF; font-weight:700;">{img_n}</div>
            <div style="font-size:0.58rem; color:#607080; text-transform:uppercase;">Images</div>
        </div>
        <div style="background:#0A1628; border:1px solid #1A2840; border-radius:6px;
                    padding:0.5rem; text-align:center;">
            <div style="font-family:'JetBrains Mono',monospace; font-size:1.1rem;
                        color:#FFD700; font-weight:700;">{aud_n}</div>
            <div style="font-size:0.58rem; color:#607080; text-transform:uppercase;">Audio</div>
        </div>
        <div style="background:#0A1628; border:1px solid #1A2840; border-radius:6px;
                    padding:0.5rem; text-align:center;">
            <div style="font-family:'JetBrains Mono',monospace; font-size:1.1rem;
                        color:#FF8C00; font-weight:700;">{vid_n}</div>
            <div style="font-size:0.58rem; color:#607080; text-transform:uppercase;">Video</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── System Status ──────────────────────────────────────────────────────────
    st.markdown('<hr style="border:none; border-top:1px solid #1A2840; margin:0.75rem 0;">', unsafe_allow_html=True)

    try:
        import cv2
        cv2_status = "✅ OpenCV"
    except ImportError:
        cv2_status = "⚠️ No OpenCV"

    try:
        from reportlab.platypus import SimpleDocTemplate
        rl_status = "✅ ReportLab"
    except ImportError:
        rl_status = "⚠️ No ReportLab"

    try:
        from groq import Groq
        groq_status = "✅ Groq SDK"
    except ImportError:
        groq_status = "⚠️ No Groq SDK"

    st.markdown(f"""
    <div style="font-size:0.68rem; color:#607080; line-height:1.8; font-family:'JetBrains Mono',monospace;">
        <div>{cv2_status}</div>
        <div>{rl_status}</div>
        <div>{groq_status}</div>
        <div style="color:#1A3060; margin-top:0.4rem;">
            {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Main Content ─────────────────────────────────────────────────────────────

app_header()

# Tab definitions
tab_labels = [
    "📷  Visual Evidence",
    "🎙️  Audio Transcription",
    "📹  CCTV Video",
    "🔗  Fusion & Chat",
    "📄  PDF Export",
]

tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)

with tab1:
    render_image_tab(client, st.session_state.investigator)

with tab2:
    render_audio_tab(client, st.session_state.investigator)

with tab3:
    render_video_tab(client, st.session_state.investigator)

with tab4:
    render_fusion_tab(client)

with tab5:
    render_pdf_tab(client, st.session_state.case_id, st.session_state.investigator)
