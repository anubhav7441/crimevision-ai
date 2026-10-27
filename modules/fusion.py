"""
CrimeVision AI – Module 4: Multimodal Fusion & Grounded Evidence Chat
Tab 4 of the main application.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from utils.ui_helpers import section_header, cv_divider, evidence_id_tag, demo_mode_banner
from utils.evidence_store import (
    get_all_evidence, build_evidence_context,
    get_chat_history, append_chat, clear_chat, has_evidence
)
from utils.groq_client import GroqClient


# ─── Type-to-Icon Map ─────────────────────────────────────────────────────────

TYPE_META = {
    "IMAGE": {"icon": "📷", "color": "#00D4FF",  "label": "Crime Scene Image"},
    "AUDIO": {"icon": "🎙️", "color": "#FFD700",  "label": "Witness Audio"},
    "VIDEO": {"icon": "📹", "color": "#FF8C00",  "label": "CCTV Footage"},
}


# ─── Master Ledger ────────────────────────────────────────────────────────────

def render_master_ledger(records: list):
    """Render the unified evidence ledger table."""
    section_header("MASTER FORENSIC EVIDENCE LEDGER", "📚")

    rows = []
    for r in records:
        meta  = TYPE_META.get(r["type"], {"icon": "❓", "label": r["type"]})
        d     = r.get("data", {})

        if r["type"] == "IMAGE":
            detail = f"{d.get('scene_classification','—')} | Threat: {d.get('threat_level','—')}"
        elif r["type"] == "AUDIO":
            n = len(d.get("timeline", []))
            detail = f"{n} timeline events extracted"
        elif r["type"] == "VIDEO":
            n = len(d.get("events", []))
            detail = f"{n} chronological events logged"
        else:
            detail = "—"

        rows.append({
            "Evidence ID":   r["evidence_id"],
            "Type":          f"{meta['icon']} {meta['label']}",
            "Captured (UTC)":r["timestamp"],
            "Investigator":  r.get("investigator", "—"),
            "Summary":       detail,
            "Hash":          r.get("custody", {}).get("hash", "—")[:12] + "…",
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No evidence records yet. Analyze files in Tabs 1–3 first.")


# ─── Fusion Timeline Visualization ───────────────────────────────────────────

def render_fusion_timeline(records: list):
    """Render a combined Plotly timeline across all evidence types."""
    import plotly.graph_objects as go

    if not records:
        return

    fig = go.Figure()

    for r in records:
        meta = TYPE_META.get(r["type"], {"color": "#607080", "label": r["type"], "icon": ""})
        ts_str = r.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            ts_label = ts.strftime("%H:%M:%S")
        except Exception:
            ts_label = ts_str[:19]

        d = r.get("data", {})
        if r["type"] == "IMAGE":
            hover = f"Scene: {d.get('scene_classification','—')}<br>Threat: {d.get('threat_level','—')}"
        elif r["type"] == "AUDIO":
            hover = f"Audio events: {len(d.get('timeline',[]))}"
        else:
            hover = f"Video events: {len(d.get('events',[]))}"

        fig.add_trace(go.Scatter(
            x=[ts_label], y=[r["type"]],
            mode="markers+text",
            text=[r["evidence_id"]],
            textposition="top center",
            textfont=dict(size=8, color=meta["color"]),
            marker=dict(size=18, color=meta["color"], symbol="diamond",
                        line=dict(width=2, color="white")),
            name=meta["label"],
            hovertemplate=f"<b>{r['evidence_id']}</b><br>{hover}<extra></extra>",
        ))

    fig.update_layout(
        paper_bgcolor="#050A14",
        plot_bgcolor="#060C1A",
        xaxis=dict(title="Time of Analysis (UTC)", gridcolor="#1A2840", color="#607080"),
        yaxis=dict(title="Evidence Stream", gridcolor="#1A2840", color="#607080",
                   categoryorder="array", categoryarray=["IMAGE", "AUDIO", "VIDEO"]),
        font=dict(color="#C8D6E5", family="Inter"),
        margin=dict(l=20, r=20, t=40, b=20),
        title=dict(text="🔗 Multimodal Evidence Fusion Timeline",
                   font=dict(size=13, color="#00D4FF"), x=0.5),
        height=320,
        showlegend=True,
        legend=dict(bgcolor="#080E1C", bordercolor="#1A2840",
                    font=dict(color="#C8D6E5", size=10)),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─── Chat Interface ───────────────────────────────────────────────────────────

STARTER_QUESTIONS = [
    "Was a weapon visible before the suspect fled?",
    "What is the timeline of events across all evidence?",
    "Describe the suspect based on all evidence.",
    "Was the victim identified in the crime scene image?",
    "What vehicle was involved and when did it appear?",
]


def render_chat_interface(client: GroqClient):
    """Render the grounded RAG chat interface."""
    section_header("FORENSIC INTELLIGENCE CHAT", "💬")

    st.markdown("""
    <div style="font-size:0.78rem; color:#607080; margin-bottom:1rem; line-height:1.6;">
        Interrogate the evidence corpus using natural language. Responses are strictly grounded
        in analyzed evidence and will always cite
        <span style="font-family:'JetBrains Mono',monospace; color:#00D4FF;">Evidence IDs</span>.
        Zero hallucination policy enforced.
    </div>
    """, unsafe_allow_html=True)

    if not has_evidence() and not client.demo_mode:
        st.warning("⚠️ No evidence analyzed yet. Complete at least one analysis in Tabs 1–3, then return here.")
        return

    if client.demo_mode:
        demo_mode_banner()

    # ── Starter questions ──────────────────────────────────────────────────────
    st.markdown('<div style="font-size:0.72rem; color:#607080; margin-bottom:0.5rem; '
                'font-weight:600; letter-spacing:0.08em; text-transform:uppercase;">'
                'Quick Questions</div>', unsafe_allow_html=True)

    q_cols = st.columns(len(STARTER_QUESTIONS[:3]))
    chosen_starter = None
    for i, q in enumerate(STARTER_QUESTIONS[:3]):
        with q_cols[i]:
            if st.button(q, key=f"starter_{i}", use_container_width=True):
                chosen_starter = q

    q_cols2 = st.columns(2)
    for i, q in enumerate(STARTER_QUESTIONS[3:5]):
        with q_cols2[i]:
            if st.button(q, key=f"starter2_{i}", use_container_width=True):
                chosen_starter = q

    cv_divider()

    # ── Chat history display ───────────────────────────────────────────────────
    history = get_chat_history()
    if history:
        for msg in history:
            role = msg["role"]
            if role == "user":
                st.markdown(f"""
                <div class="chat-user">
                    <div class="chat-label chat-label-user">🔍 INVESTIGATOR</div>
                    {msg['content']}
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-assistant">
                    <div class="chat-label chat-label-ai">🤖 FORENSIC AI</div>
                    {msg['content']}
                </div>""", unsafe_allow_html=True)

    # ── Input ──────────────────────────────────────────────────────────────────
    col_input, col_btn = st.columns([5, 1], gap="small")
    with col_input:
        user_q = st.text_input(
            "Ask the evidence...",
            value=chosen_starter or "",
            placeholder="e.g. Was a weapon visible before the suspect fled?",
            key="chat_input",
            label_visibility="collapsed",
        )
    with col_btn:
        send = st.button("SEND", key="btn_chat_send", use_container_width=True)

    col_clr, _ = st.columns([1, 5])
    with col_clr:
        if st.button("🗑 Clear Chat", key="btn_clear_chat"):
            clear_chat()
            st.rerun()

    if send and user_q.strip():
        with st.spinner("Querying evidence corpus..."):
            ctx = build_evidence_context()
            hist = get_chat_history()
            answer = client.forensic_chat(user_q.strip(), ctx, hist)

        append_chat("user",      user_q.strip())
        append_chat("assistant", answer)
        st.rerun()


# ─── Main Tab Renderer ────────────────────────────────────────────────────────

def render_fusion_tab(client: GroqClient):
    """Render the complete Multimodal Fusion & Chat tab."""

    st.markdown("""
    <div style="font-size:0.82rem; color:#607080; margin-bottom:1.5rem; line-height:1.7;">
        The <strong style="color:#C8D6E5;">Multimodal Fusion Engine</strong> aggregates all analyzed
        image, audio, and video evidence into a unified forensic ledger.
        Use the grounded RAG chat to interrogate evidence with natural language queries —
        all answers are strictly sourced from analyzed evidence with zero speculation.
    </div>
    """, unsafe_allow_html=True)

    records = get_all_evidence()

    # ── Stats bar ──────────────────────────────────────────────────────────────
    img_count = sum(1 for r in records if r["type"] == "IMAGE")
    aud_count = sum(1 for r in records if r["type"] == "AUDIO")
    vid_count = sum(1 for r in records if r["type"] == "VIDEO")

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.markdown(f"""<div class="stat-box">
            <div class="stat-value">{len(records)}</div>
            <div class="stat-label">Total Evidence</div></div>""", unsafe_allow_html=True)
    with col_s2:
        st.markdown(f"""<div class="stat-box">
            <div class="stat-value" style="color:#00D4FF;">{img_count}</div>
            <div class="stat-label">Image Records</div></div>""", unsafe_allow_html=True)
    with col_s3:
        st.markdown(f"""<div class="stat-box">
            <div class="stat-value" style="color:#FFD700;">{aud_count}</div>
            <div class="stat-label">Audio Records</div></div>""", unsafe_allow_html=True)
    with col_s4:
        st.markdown(f"""<div class="stat-box">
            <div class="stat-value" style="color:#FF8C00;">{vid_count}</div>
            <div class="stat-label">Video Records</div></div>""", unsafe_allow_html=True)

    cv_divider()

    # ── Master ledger ──────────────────────────────────────────────────────────
    render_master_ledger(records)

    cv_divider()

    # ── Fusion timeline ────────────────────────────────────────────────────────
    if records:
        render_fusion_timeline(records)
        cv_divider()

    # ── Chat ───────────────────────────────────────────────────────────────────
    render_chat_interface(client)
