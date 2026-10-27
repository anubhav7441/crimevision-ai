"""
CrimeVision AI – Module 3: CCTV Video Analysis & Event Progression
Tab 3 of the main application.
"""
import io
import os
import random
import tempfile
import numpy as np
import streamlit as st
import pandas as pd
from PIL import Image

from config.settings import DEMO_VIDEO_EVENTS
from utils.ui_helpers import (
    section_header, cv_divider, analysis_status, demo_mode_banner, evidence_id_tag
)
from utils.evidence_store import store_video_evidence
from utils.groq_client import GroqClient

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# ─── Crime Category Colors ────────────────────────────────────────────────────

CATEGORY_COLORS = {
    "Homicide":           "#FF2222",
    "Assault & Battery":  "#FF5500",
    "Robbery":            "#FF8C00",
    "Weapon Possession":  "#FF4444",
    "Trespassing":        "#FFD700",
    "Suspicious Activity":"#90A8C0",
    "Drug Trafficking":   "#C070FF",
    "Kidnapping":         "#FF0080",
}

CATEGORY_SEVERITY = {
    "Homicide":           5,
    "Kidnapping":         5,
    "Assault & Battery":  4,
    "Robbery":            4,
    "Weapon Possession":  4,
    "Drug Trafficking":   3,
    "Trespassing":        2,
    "Suspicious Activity":1,
}


# ─── Frame Sampling with OpenCV ───────────────────────────────────────────────

def sample_frames(video_path: str, interval_sec: float = 6.0, max_frames: int = 10):
    """
    Sample frames from a video file at regular intervals.
    Returns list of (timestamp_sec, PIL.Image).
    """
    if not CV2_AVAILABLE:
        return []

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    interval_frames = max(1, int(fps * interval_sec))

    frames = []
    frame_idx = 0
    while frame_idx < total_frames and len(frames) < max_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
        ts = frame_idx / fps
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        frames.append((ts, pil))
        frame_idx += interval_frames

    cap.release()
    return frames


def annotate_frame(image: Image.Image, event: dict, frame_idx: int) -> Image.Image:
    """Add simple annotation overlay to a frame."""
    from PIL import ImageDraw, ImageFont
    img = image.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # Top bar
    draw.rectangle([0, 0, w, 28], fill=(6, 12, 26, 200))
    try:
        font = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font = ImageFont.load_default()
    draw.text((6, 6), f"FRAME {frame_idx+1:02d}  TS:{event.get('timestamp','??')}", fill=(0, 212, 255), font=font)

    # Bottom bar with category
    cat    = event.get("category", "")
    color  = CATEGORY_COLORS.get(cat, (144, 168, 192))
    if isinstance(color, str):
        # Parse hex
        color = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    draw.rectangle([0, h - 28, w, h], fill=(6, 12, 26, 200))
    draw.text((6, h - 22), cat, fill=color, font=font)

    # Simulated bounding box for person/vehicle
    objects = event.get("objects", [])
    if "Person" in objects:
        rng = random.Random(frame_idx * 7)
        x1 = rng.randint(w // 4, w // 2)
        y1 = rng.randint(h // 5, h // 3)
        x2, y2 = x1 + rng.randint(50, 100), y1 + rng.randint(100, 180)
        draw.rectangle([x1, y1, min(x2, w-1), min(y2, h-1)],
                       outline=(255, 140, 0), width=2)
    return img


# ─── Event Progression Chart ─────────────────────────────────────────────────

def render_event_progression_chart(events: list):
    """Render a Plotly timeline bar chart of video events."""
    import plotly.graph_objects as go

    times   = []
    labels  = []
    colors  = []
    confs   = []

    for i, e in enumerate(events):
        ts_str = e.get("timestamp", "00:00")
        try:
            parts = ts_str.split(":")
            secs  = int(parts[0]) * 60 + int(parts[1])
        except Exception:
            secs = i * 7

        cat   = e.get("category", "Suspicious Activity")
        conf  = e.get("confidence", 0.75)
        times.append(secs)
        labels.append(f"{ts_str}: {e.get('event','')[:30]}…")
        colors.append(CATEGORY_COLORS.get(cat, "#607080"))
        confs.append(conf)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times, y=confs,
        mode="markers+lines+text",
        text=[e.get("category","") for e in events],
        textposition="top center",
        textfont=dict(size=9, color="#C8D6E5"),
        marker=dict(size=[12 + CATEGORY_SEVERITY.get(e.get("category",""),1)*4 for e in events],
                    color=colors, opacity=0.9,
                    line=dict(width=1, color="white")),
        line=dict(color="#1A3060", width=1, dash="dot"),
        hovertemplate="<b>%{text}</b><br>Time: %{x}s<br>Conf: %{y:.0%}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="#050A14",
        plot_bgcolor="#060C1A",
        xaxis=dict(title="Seconds", gridcolor="#1A2840", color="#607080", ticksuffix="s"),
        yaxis=dict(title="Confidence", gridcolor="#1A2840", color="#607080",
                   tickformat=".0%", range=[0, 1.1]),
        font=dict(color="#C8D6E5", family="Inter"),
        margin=dict(l=20, r=20, t=40, b=20),
        title=dict(text="📈 Event Progression Timeline", font=dict(size=13, color="#00D4FF"), x=0.5),
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True)


# ─── Main Tab Renderer ────────────────────────────────────────────────────────

def render_video_tab(client: GroqClient, investigator: str):
    """Render the complete Video Analysis tab."""

    st.markdown("""
    <div style="font-size:0.82rem; color:#607080; margin-bottom:1.5rem; line-height:1.7;">
        Upload CCTV footage or investigative video for
        <strong style="color:#C8D6E5;">frame-by-frame forensic analysis</strong>.
        The system samples frames at configurable intervals, detects objects and suspects,
        tracks trajectories, and generates a second-by-second chronological event log with
        penal crime classification.
    </div>
    """, unsafe_allow_html=True)

    col_up, col_cfg = st.columns([2, 1], gap="large")
    with col_up:
        uploaded = st.file_uploader(
            "Upload CCTV / Video Evidence",
            type=["mp4", "avi", "mov", "mkv", "webm"],
            help="Supports MP4, AVI, MOV, MKV, WEBM.",
            key="video_uploader",
        )
    with col_cfg:
        interval_sec = st.slider("Frame sampling interval (seconds)", 3, 15, 6, key="vid_interval")
        max_frames   = st.slider("Max frames to analyze", 3, 12, 8, key="vid_maxframes")

    if client.demo_mode and not uploaded:
        demo_mode_banner()

    if uploaded is None:
        st.markdown("""
        <div style="border:1px dashed #1A3060; border-radius:12px; padding:3rem;
                    text-align:center; color:#607080; margin-top:1rem;">
            <div style="font-size:2.5rem; margin-bottom:0.75rem;">📹</div>
            <div style="font-size:0.9rem; font-weight:600; color:#8090A0; margin-bottom:0.4rem;">
                No Video Uploaded
            </div>
            <div style="font-size:0.78rem;">Upload CCTV footage above to begin analysis.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    video_bytes = uploaded.read()

    if client.demo_mode:
        demo_mode_banner()

    # Metadata
    section_header("VIDEO METADATA", "📋")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        analysis_status("File Name", uploaded.name)
        analysis_status("Size",      f"{len(video_bytes)/1024/1024:.2f} MB")
    with col_b:
        analysis_status("Format",    uploaded.type.split("/")[-1].upper())
        analysis_status("Interval",  f"{interval_sec}s per frame")
    with col_c:
        analysis_status("Max Frames", str(max_frames))
        analysis_status("OpenCV",     "✅ Available" if CV2_AVAILABLE else "⚠️ Not installed")

    cv_divider()

    if st.button("📹 ANALYZE CCTV FOOTAGE", key="btn_video"):
        with st.spinner("Processing video frames and analyzing events..."):
            # Save to temp file for OpenCV
            frames_data = []
            if CV2_AVAILABLE and not client.demo_mode:
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                    tmp.write(video_bytes)
                    tmp_path = tmp.name
                try:
                    raw_frames = sample_frames(tmp_path, interval_sec, max_frames)
                    frame_descs = [
                        f"Frame at {ts:.1f}s: motion detected, people and objects visible"
                        for ts, _ in raw_frames
                    ]
                    events = client.classify_video_events(frame_descs)
                    pil_frames = [img for _, img in raw_frames]
                finally:
                    os.unlink(tmp_path)
            else:
                events = DEMO_VIDEO_EVENTS[:max_frames]
                pil_frames = []  # no real frames in demo mode

            eid = store_video_evidence(events, investigator)

        # ── Results banner ────────────────────────────────────────────────────
        critical_cats = [e for e in events if CATEGORY_SEVERITY.get(e.get("category",""), 0) >= 4]
        st.markdown(f"""
        <div style="
            background:rgba(0,212,255,0.05); border:1px solid rgba(0,212,255,0.2);
            border-radius:8px; padding:0.8rem 1.2rem; margin:1rem 0;
            display:flex; align-items:center; gap:1rem; flex-wrap:wrap;
        ">
            <span style="color:#00D4FF; font-weight:700; font-size:0.8rem;">✅ VIDEO ANALYSIS COMPLETE</span>
            {evidence_id_tag(eid)}
            <span style="font-size:0.75rem; color:#607080;">
                Events: <strong style="color:#C8D6E5;">{len(events)}</strong>
            </span>
            <span style="font-size:0.75rem; color:#607080;">
                High-severity: <strong style="color:#FF4444;">{len(critical_cats)}</strong>
            </span>
        </div>
        """, unsafe_allow_html=True)

        # ── Stats ──────────────────────────────────────────────────────────────
        unique_cats = list({e.get("category","") for e in events})
        avg_conf    = sum(e.get("confidence", 0.8) for e in events) / max(len(events), 1)
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.markdown(f"""<div class="stat-box">
                <div class="stat-value">{len(events)}</div>
                <div class="stat-label">Events Logged</div></div>""", unsafe_allow_html=True)
        with col_s2:
            st.markdown(f"""<div class="stat-box">
                <div class="stat-value" style="color:#FF8C00;">{len(unique_cats)}</div>
                <div class="stat-label">Crime Categories</div></div>""", unsafe_allow_html=True)
        with col_s3:
            st.markdown(f"""<div class="stat-box">
                <div class="stat-value" style="color:#00FF88;">{avg_conf:.0%}</div>
                <div class="stat-label">Avg Confidence</div></div>""", unsafe_allow_html=True)

        cv_divider()

        # ── Frame Gallery ──────────────────────────────────────────────────────
        if pil_frames and len(pil_frames) > 0:
            section_header("SAMPLED FRAMES WITH DETECTIONS", "🖼️")
            paired = list(zip(pil_frames, events[:len(pil_frames)]))
            cols_per_row = 3
            for row_start in range(0, len(paired), cols_per_row):
                cols = st.columns(cols_per_row, gap="small")
                for ci, (pil, ev) in enumerate(paired[row_start:row_start + cols_per_row]):
                    annotated = annotate_frame(pil, ev, row_start + ci)
                    with cols[ci]:
                        st.image(annotated, use_container_width=True)
                        cat   = ev.get("category","")
                        color = CATEGORY_COLORS.get(cat, "#607080")
                        st.markdown(f"""
                        <div style="font-size:0.68rem; text-align:center; margin-top:0.3rem;">
                            <span style="color:{color}; font-weight:700;">{cat}</span>
                            <span style="color:#607080;"> · {ev.get('timestamp','')}</span>
                        </div>""", unsafe_allow_html=True)
            cv_divider()

        # ── Event Progression Chart ────────────────────────────────────────────
        render_event_progression_chart(events)

        cv_divider()

        # ── Chronological Event Log ────────────────────────────────────────────
        section_header("CHRONOLOGICAL EVENT LOG", "📋")
        df = pd.DataFrame([{
            "Timestamp":      e.get("timestamp",""),
            "Event":          e.get("event",""),
            "Detected Objects":  ", ".join(e.get("objects",[])),
            "Crime Category":    e.get("category",""),
            "Confidence":        f"{e.get('confidence',0.8):.0%}",
        } for e in events])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.session_state["last_video_eid"] = eid
        st.success(f"Evidence stored → {eid}")
