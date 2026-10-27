"""
CrimeVision AI – Module 2: Witness Audio Transcription & Timeline
Tab 2 of the main application.
"""
import streamlit as st
import pandas as pd

from utils.ui_helpers import (
    section_header, cv_divider, significance_badge,
    evidence_id_tag, analysis_status, demo_mode_banner
)
from utils.evidence_store import store_audio_evidence
from utils.groq_client import GroqClient


# ─── Significance Color Map ───────────────────────────────────────────────────

SIG_COLORS = {
    "CRITICAL": "#FF4444",
    "HIGH":     "#FF8C00",
    "MEDIUM":   "#FFD700",
    "LOW":      "#00FF88",
}

SPEAKER_COLORS = {
    "Dispatcher": "#00D4FF",
    "Witness":    "#FFD700",
    "Caller":     "#FFD700",
    "Unknown":    "#607080",
    "Suspect":    "#FF4444",
}


def _speaker_color(speaker: str) -> str:
    for k, v in SPEAKER_COLORS.items():
        if k.lower() in speaker.lower():
            return v
    return "#A0B8D0"


def render_timeline_events(timeline: list):
    """Render a visual timeline of audio events."""
    section_header("FORENSIC AUDIO TIMELINE", "⏱️")
    for event in timeline:
        sig   = event.get("significance", "LOW").upper()
        color = SIG_COLORS.get(sig, "#607080")
        spk   = event.get("speaker", "Unknown")
        spk_c = _speaker_color(spk)

        st.markdown(f"""
        <div style="
            display:flex; gap:1rem; align-items:flex-start;
            padding:0.7rem; margin-bottom:0.4rem;
            background: rgba(10,22,40,0.6);
            border:1px solid #1A2840; border-left:3px solid {color};
            border-radius:6px;
        ">
            <div style="min-width:3rem; text-align:center;">
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem;
                            color:#00D4FF; font-weight:700;">{event.get('timestamp','?')}</div>
            </div>
            <div style="flex:1;">
                <div style="font-size:0.72rem; font-weight:700; letter-spacing:0.08em;
                            text-transform:uppercase; color:{spk_c}; margin-bottom:0.2rem;">
                    {spk}
                </div>
                <div style="font-size:0.84rem; color:#C8D6E5; line-height:1.5;">
                    {event.get('event','—')}
                </div>
            </div>
            <div style="min-width:5rem; text-align:right;">
                <span style="
                    font-size:0.63rem; font-weight:700; letter-spacing:0.1em;
                    text-transform:uppercase; color:{color};
                    background:rgba(255,255,255,0.04); border:1px solid {color}44;
                    padding:0.2rem 0.5rem; border-radius:4px;
                ">{sig}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_audio_tab(client: GroqClient, investigator: str):
    """Render the complete Audio Analysis tab."""

    st.markdown("""
    <div style="font-size:0.82rem; color:#607080; margin-bottom:1.5rem; line-height:1.7;">
        Upload witness statements or emergency 911/112 call recordings for
        <strong style="color:#C8D6E5;">Whisper-powered multilingual transcription</strong>.
        The system extracts speaker tags, key events, and generates a timestamped forensic timeline.
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload Audio Recording",
        type=["mp3", "wav", "m4a", "ogg", "flac", "webm"],
        help="Supports MP3, WAV, M4A, OGG, FLAC. Max 25MB for Groq API.",
        key="audio_uploader",
    )

    if client.demo_mode and not uploaded:
        demo_mode_banner()

    if uploaded is None:
        st.markdown("""
        <div style="
            border:1px dashed #1A3060; border-radius:12px; padding:3rem;
            text-align:center; color:#607080; margin-top:1rem;
        ">
            <div style="font-size:2.5rem; margin-bottom:0.75rem;">🎙️</div>
            <div style="font-size:0.9rem; font-weight:600; color:#8090A0; margin-bottom:0.4rem;">
                No Audio Uploaded
            </div>
            <div style="font-size:0.78rem;">
                Upload a witness statement or 911 call recording above.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    audio_bytes = uploaded.read()

    if client.demo_mode:
        demo_mode_banner()

    # File metadata
    col1, col2 = st.columns([1.6, 1], gap="large")
    with col1:
        section_header("AUDIO PLAYBACK", "🔊")
        st.audio(audio_bytes, format=uploaded.type)
    with col2:
        section_header("FILE METADATA", "📋")
        analysis_status("File Name", uploaded.name)
        analysis_status("Format",    uploaded.type.split("/")[-1].upper())
        analysis_status("Size",      f"{len(audio_bytes)/1024:.1f} KB")
        analysis_status("Engine",    "Groq Whisper-Large-V3" if not client.demo_mode else "DEMO MODE")

    cv_divider()

    if st.button("🎙️ TRANSCRIBE & ANALYZE AUDIO", key="btn_audio"):
        with st.spinner("Running Whisper transcription pipeline..."):
            # Step 1: Transcription
            transcript = client.transcribe_audio(audio_bytes, uploaded.name)

            # Step 2: Timeline extraction
            timeline = client.analyze_audio_timeline(transcript)

            # Step 3: Store evidence
            eid = store_audio_evidence(transcript, timeline, investigator)

        # ── Status banner ─────────────────────────────────────────────────────
        critical_count = sum(1 for e in timeline if e.get("significance", "").upper() == "CRITICAL")

        st.markdown(f"""
        <div style="
            background:rgba(0,212,255,0.05); border:1px solid rgba(0,212,255,0.2);
            border-radius:8px; padding:0.8rem 1.2rem; margin:1rem 0;
            display:flex; align-items:center; gap:1rem; flex-wrap:wrap;
        ">
            <span style="color:#00D4FF; font-weight:700; font-size:0.8rem;">✅ TRANSCRIPTION COMPLETE</span>
            {evidence_id_tag(eid)}
            <span style="font-size:0.75rem; color:#607080;">
                Events: <strong style="color:#C8D6E5;">{len(timeline)}</strong>
            </span>
            <span style="font-size:0.75rem; color:#607080;">
                Critical: <strong style="color:#FF4444;">{critical_count}</strong>
            </span>
        </div>
        """, unsafe_allow_html=True)

        # ── Summary stats ──────────────────────────────────────────────────────
        speakers = list({e.get("speaker", "Unknown") for e in timeline})
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-value">{len(timeline)}</div>
                <div class="stat-label">Timeline Events</div>
            </div>""", unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-value" style="color:#FF4444;">{critical_count}</div>
                <div class="stat-label">Critical Markers</div>
            </div>""", unsafe_allow_html=True)
        with col_c:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-value" style="color:#FFD700;">{len(speakers)}</div>
                <div class="stat-label">Speakers Detected</div>
            </div>""", unsafe_allow_html=True)

        cv_divider()

        # ── Transcript ─────────────────────────────────────────────────────────
        section_header("FULL TRANSCRIPT", "📄")
        st.markdown(f"""
        <div class="transcript-box">{transcript.replace(chr(10), '<br>')}</div>
        """, unsafe_allow_html=True)

        cv_divider()

        # ── Visual Timeline ────────────────────────────────────────────────────
        render_timeline_events(timeline)

        cv_divider()

        # ── Tabular view ───────────────────────────────────────────────────────
        section_header("STRUCTURED EVENT TABLE", "📊")
        df = pd.DataFrame([{
            "Timestamp":   e.get("timestamp", ""),
            "Speaker":     e.get("speaker", ""),
            "Key Event":   e.get("event", ""),
            "Significance":e.get("significance", ""),
        } for e in timeline])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.session_state["last_audio_eid"] = eid
        st.success(f"Evidence stored → {eid}")
