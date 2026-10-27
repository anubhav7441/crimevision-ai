"""
CrimeVision AI – UI Helpers
Shared CSS injection, styled components, and reusable Streamlit widgets.
"""
import streamlit as st
from config.settings import THREAT_LEVELS


# ─── Master CSS ───────────────────────────────────────────────────────────────

MASTER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Reset & Base ─────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    background: #050A14 !important;
    color: #C8D6E5 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Hide Streamlit Branding ──────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ──────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #060C1A 0%, #0A1628 100%) !important;
    border-right: 1px solid #1A2840 !important;
}
section[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem; }

/* ── Main Container ───────────────────────────────────────────── */
.main .block-container {
    max-width: 1280px !important;
    padding: 1.5rem 2rem 3rem !important;
}

/* ── Tabs ─────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #080E1C !important;
    border-bottom: 2px solid #0D2040 !important;
    gap: 4px;
    padding: 0 1rem;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #607080 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.9rem 1.4rem !important;
    border-radius: 0 !important;
    border-bottom: 3px solid transparent !important;
    transition: all 0.25s ease !important;
}
.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: #00D4FF !important;
    border-bottom: 3px solid #00D4FF !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #8BE8FF !important; }
.stTabs [data-baseweb="tab-panel"] {
    background: transparent !important;
    padding: 1.5rem 0 !important;
}

/* ── Buttons ──────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #0066FF 0%, #004DB3 100%) !important;
    color: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-size: 0.78rem !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.6rem 1.8rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 0 20px rgba(0, 102, 255, 0.3) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #0080FF 0%, #0060D6 100%) !important;
    box-shadow: 0 0 30px rgba(0, 128, 255, 0.5) !important;
    transform: translateY(-1px) !important;
}

/* ── File Uploader ────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: #0A1628 !important;
    border: 1px dashed #1A3060 !important;
    border-radius: 10px !important;
    padding: 1rem !important;
    transition: border-color 0.2s ease;
}
[data-testid="stFileUploader"]:hover { border-color: #00D4FF !important; }

/* ── Text Inputs ──────────────────────────────────────────────── */
.stTextInput input, .stTextArea textarea {
    background: #0A1628 !important;
    border: 1px solid #1A3060 !important;
    color: #C8D6E5 !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #00D4FF !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.15) !important;
}

/* ── Metrics ──────────────────────────────────────────────────── */
[data-testid="stMetricValue"] {
    color: #00D4FF !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.4rem !important;
}
[data-testid="stMetricLabel"] { color: #607080 !important; font-size: 0.75rem !important; }

/* ── DataFrames / Tables ──────────────────────────────────────── */
.stDataFrame { border-radius: 8px !important; overflow: hidden !important; }
[data-testid="stDataFrameResizable"] table {
    background: #080E1C !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
}
[data-testid="stDataFrameResizable"] th {
    background: #0D2040 !important;
    color: #00D4FF !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
[data-testid="stDataFrameResizable"] td { color: #C8D6E5 !important; }
[data-testid="stDataFrameResizable"] tr:hover td { background: #0F1E38 !important; }

/* ── Select / Dropdown ────────────────────────────────────────── */
.stSelectbox select, [data-baseweb="select"] {
    background: #0A1628 !important;
    color: #C8D6E5 !important;
    border: 1px solid #1A3060 !important;
}

/* ── Spinner ──────────────────────────────────────────────────── */
.stSpinner { color: #00D4FF !important; }

/* ── Progress ─────────────────────────────────────────────────── */
.stProgress > div > div {
    background: linear-gradient(90deg, #00D4FF, #0066FF) !important;
}

/* ── Custom Components ────────────────────────────────────────── */
.cv-card {
    background: linear-gradient(135deg, #0A1628 0%, #0D1E3A 100%);
    border: 1px solid #1A3060;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.cv-card:hover { border-color: #1E4080; box-shadow: 0 4px 32px rgba(0, 102, 255, 0.15); }

.cv-card-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #1A3060;
}
.cv-card-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #607080;
}
.cv-card-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1rem;
    font-weight: 600;
    color: #C8D6E5;
}

/* Threat badges */
.badge {
    display: inline-block;
    padding: 0.3rem 0.9rem;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.badge-critical { background: rgba(255,34,34,0.15); color: #FF4444; border: 1px solid #FF4444; }
.badge-high     { background: rgba(255,140,0,0.15);  color: #FF8C00; border: 1px solid #FF8C00; }
.badge-medium   { background: rgba(255,215,0,0.15);  color: #FFD700; border: 1px solid #FFD700; }
.badge-low      { background: rgba(0,255,136,0.15);  color: #00FF88; border: 1px solid #00FF88; }

/* Section headers */
.cv-section-header {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #00D4FF;
    margin-bottom: 0.75rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #0D2040;
}

/* Evidence ID tag */
.eid-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    background: rgba(0, 212, 255, 0.08);
    color: #00D4FF;
    border: 1px solid rgba(0, 212, 255, 0.25);
    border-radius: 4px;
    padding: 0.2rem 0.6rem;
    letter-spacing: 0.06em;
}

/* Pulse animation for live analysis */
@keyframes pulse-glow {
    0%   { box-shadow: 0 0 6px rgba(0, 212, 255, 0.4); }
    50%  { box-shadow: 0 0 20px rgba(0, 212, 255, 0.8); }
    100% { box-shadow: 0 0 6px rgba(0, 212, 255, 0.4); }
}
.analyzing { animation: pulse-glow 1.5s ease-in-out infinite; }

/* Chat message bubbles */
.chat-user {
    background: linear-gradient(135deg, #0A2040 0%, #0D2A50 100%);
    border: 1px solid #1A3060;
    border-radius: 12px 12px 4px 12px;
    padding: 0.9rem 1.2rem;
    margin: 0.5rem 0 0.5rem 20%;
    color: #C8D6E5;
    font-size: 0.88rem;
}
.chat-assistant {
    background: linear-gradient(135deg, #060E20 0%, #091830 100%);
    border: 1px solid #0D2040;
    border-left: 3px solid #00D4FF;
    border-radius: 4px 12px 12px 12px;
    padding: 0.9rem 1.2rem;
    margin: 0.5rem 20% 0.5rem 0;
    color: #C8D6E5;
    font-size: 0.88rem;
    line-height: 1.65;
}
.chat-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.chat-label-user { color: #4080C0; }
.chat-label-ai   { color: #00D4FF; }

/* Scrollable transcript */
.transcript-box {
    background: #060C18;
    border: 1px solid #1A2840;
    border-radius: 8px;
    padding: 1.2rem;
    max-height: 340px;
    overflow-y: auto;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    line-height: 1.8;
    color: #90A8C0;
}
.transcript-box::-webkit-scrollbar { width: 6px; }
.transcript-box::-webkit-scrollbar-track { background: #0A1628; }
.transcript-box::-webkit-scrollbar-thumb { background: #1A3060; border-radius: 3px; }

/* Lead item */
.lead-item {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    padding: 0.7rem 0.9rem;
    background: rgba(0, 102, 255, 0.06);
    border: 1px solid rgba(0, 102, 255, 0.15);
    border-radius: 8px;
    margin-bottom: 0.5rem;
    font-size: 0.84rem;
    color: #A0B8D0;
}
.lead-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 700;
    color: #0066FF;
    min-width: 1.5rem;
    padding-top: 1px;
}

/* Stat boxes */
.stat-box {
    background: linear-gradient(135deg, #0A1628 0%, #0D1E3A 100%);
    border: 1px solid #1A3060;
    border-radius: 10px;
    padding: 1.2rem;
    text-align: center;
}
.stat-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #00D4FF;
}
.stat-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #607080;
    margin-top: 0.3rem;
}

/* Timeline vertical line */
.timeline-container { position: relative; padding-left: 2rem; }
.timeline-container::before {
    content: '';
    position: absolute;
    left: 0.6rem;
    top: 0; bottom: 0;
    width: 2px;
    background: linear-gradient(180deg, #00D4FF, #0066FF, transparent);
}

/* Divider */
.cv-divider {
    border: none;
    border-top: 1px solid #1A2840;
    margin: 1.5rem 0;
}
</style>
"""


def inject_css():
    """Inject the master CSS into the Streamlit app."""
    st.markdown(MASTER_CSS, unsafe_allow_html=True)


# ─── Reusable Components ──────────────────────────────────────────────────────

def threat_badge(level: str) -> str:
    """Return HTML for a threat level badge."""
    lvl = level.upper()
    css_class = {
        "CRITICAL": "badge-critical",
        "HIGH":     "badge-high",
        "MEDIUM":   "badge-medium",
        "LOW":      "badge-low",
    }.get(lvl, "badge-medium")
    info = THREAT_LEVELS.get(lvl, THREAT_LEVELS["MEDIUM"])
    return f'<span class="badge {css_class}">{info["icon"]} {lvl} THREAT</span>'


def significance_badge(sig: str) -> str:
    """Return HTML badge for significance level."""
    css_class = {
        "CRITICAL": "badge-critical",
        "HIGH":     "badge-high",
        "MEDIUM":   "badge-medium",
        "LOW":      "badge-low",
    }.get(sig.upper(), "badge-medium")
    return f'<span class="badge {css_class}">{sig.upper()}</span>'


def evidence_id_tag(eid: str) -> str:
    """Return HTML for an evidence ID tag."""
    return f'<span class="eid-tag">🔑 {eid}</span>'


def section_header(title: str, icon: str = ""):
    """Render a styled section header."""
    prefix = f"{icon} " if icon else ""
    st.markdown(f'<div class="cv-section-header">{prefix}{title}</div>', unsafe_allow_html=True)


def cv_divider():
    """Render a styled divider."""
    st.markdown('<hr class="cv-divider">', unsafe_allow_html=True)


def demo_mode_banner():
    """Show a demo mode warning banner."""
    st.markdown("""
    <div style="
        background: rgba(255,165,0,0.08);
        border: 1px solid rgba(255,165,0,0.3);
        border-left: 4px solid #FFA500;
        border-radius: 8px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 1rem;
        font-size: 0.82rem;
        color: #FFC060;
    ">
        ⚠️ <strong>DEMO MODE ACTIVE</strong> — Running with pre-loaded forensic simulation data.
        Enter a valid Groq API key in the sidebar to enable live AI analysis.
    </div>
    """, unsafe_allow_html=True)


def analysis_status(label: str, value: str, color: str = "#00D4FF"):
    """Render a compact status row."""
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center;
                padding:0.5rem 0; border-bottom:1px solid #1A2840;">
        <span style="font-size:0.78rem; color:#607080; text-transform:uppercase; 
                     letter-spacing:0.08em; font-weight:600;">{label}</span>
        <span style="font-family:'JetBrains Mono',monospace; font-size:0.82rem;
                     color:{color}; font-weight:600;">{value}</span>
    </div>
    """, unsafe_allow_html=True)


def render_leads(leads: list):
    """Render investigative leads as styled list items."""
    for i, lead in enumerate(leads, 1):
        st.markdown(f"""
        <div class="lead-item">
            <span class="lead-num">#{i:02d}</span>
            <span>{lead}</span>
        </div>
        """, unsafe_allow_html=True)


def chain_of_custody_sidebar(custody: dict):
    """Render chain-of-custody record in sidebar."""
    st.markdown(f"""
    <div style="background:#060C18; border:1px solid #1A2840; border-radius:8px; 
                padding:0.9rem; font-family:'JetBrains Mono',monospace; font-size:0.68rem;">
        <div style="color:#00D4FF; font-weight:700; letter-spacing:0.1em; 
                    text-transform:uppercase; margin-bottom:0.6rem;">⛓ Chain of Custody</div>
        <div style="color:#607080;">EVIDENCE ID</div>
        <div style="color:#A0B8D0; margin-bottom:0.4rem;">{custody.get('evidence_id','—')}</div>
        <div style="color:#607080;">INVESTIGATOR</div>
        <div style="color:#A0B8D0; margin-bottom:0.4rem;">{custody.get('investigator','—')}</div>
        <div style="color:#607080;">TIMESTAMP (UTC)</div>
        <div style="color:#A0B8D0; margin-bottom:0.4rem;">{custody.get('timestamp','—')}</div>
        <div style="color:#607080;">HASH (SHA-256)</div>
        <div style="color:#00D4FF; word-break:break-all;">{custody.get('hash','—')}</div>
        <div style="margin-top:0.6rem; padding-top:0.4rem; border-top:1px solid #1A2840;">
            <span style="color:#00FF88;">✓ VERIFIED</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def app_header():
    """Render the main application header."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #060C1A 0%, #0A1628 50%, #060C1A 100%);
        border: 1px solid #1A2840;
        border-radius: 12px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute; top: 0; right: 0; width: 40%; height: 100%;
            background: radial-gradient(ellipse at right, rgba(0,102,255,0.12) 0%, transparent 70%);
        "></div>
        <div style="position: relative;">
            <div style="
                font-size: 0.65rem; font-weight: 700; letter-spacing: 0.2em;
                text-transform: uppercase; color: #00D4FF; margin-bottom: 0.5rem;
            ">🔬 SKILL WALLET CAPSTONE PROJECT 2</div>
            <div style="
                font-size: clamp(1.4rem, 3vw, 2rem); font-weight: 800;
                color: #FFFFFF; letter-spacing: -0.02em; line-height: 1.2;
                margin-bottom: 0.4rem;
            ">⚖️ CrimeVision AI</div>
            <div style="
                font-size: 0.88rem; color: #607080; font-weight: 400;
                letter-spacing: 0.03em;
            ">Intelligent Multimodal Forensic Analysis Platform</div>
            <div style="
                display: flex; gap: 1rem; margin-top: 1.2rem; flex-wrap: wrap;
            ">
                <span style="font-size:0.68rem; color:#00FF88; background:rgba(0,255,136,0.08);
                             border:1px solid rgba(0,255,136,0.2); padding:0.25rem 0.7rem;
                             border-radius:4px; font-weight:700; letter-spacing:0.1em;">
                    ● SYSTEM ONLINE
                </span>
                <span style="font-size:0.68rem; color:#607080; font-family:'JetBrains Mono',monospace;
                             padding:0.25rem 0; letter-spacing:0.06em;">
                    RT-DETR · Whisper · Groq LPU · ReportLab
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
