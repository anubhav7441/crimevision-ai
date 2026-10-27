"""
CrimeVision AI – Module 1: Crime Scene Visual Evidence Tagger
Tab 1 of the main application.
"""
import io
import random
import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from config.settings import DEMO_IMAGE_DETECTIONS, THREAT_LEVELS
from utils.ui_helpers import (
    section_header, cv_divider, threat_badge,
    evidence_id_tag, render_leads, analysis_status, demo_mode_banner
)
from utils.evidence_store import store_image_evidence
from utils.groq_client import GroqClient


# ─── Object Detection Simulation ─────────────────────────────────────────────

OBJECT_CLASSES = [
    ("Person",             0.85, 0.96, "HIGH"),
    ("Firearm",            0.80, 0.95, "CRITICAL"),
    ("Edged Weapon",       0.78, 0.93, "CRITICAL"),
    ("Blood Spatter",      0.70, 0.90, "HIGH"),
    ("Forced Entry Point", 0.72, 0.88, "MEDIUM"),
    ("Shell Casing",       0.68, 0.87, "HIGH"),
    ("Suspicious Package", 0.65, 0.84, "MEDIUM"),
    ("Mask/Disguise",      0.74, 0.91, "HIGH"),
    ("Vehicle",            0.82, 0.94, "LOW"),
    ("Contraband",         0.69, 0.86, "HIGH"),
]

THREAT_COLORS = {
    "CRITICAL": (255, 40,  40,  200),
    "HIGH":     (255, 140, 0,   200),
    "MEDIUM":   (255, 215, 0,   200),
    "LOW":      (0,   220, 100, 200),
}


def simulate_detections(image: Image.Image, seed: int = 42) -> list:
    """
    Simulate RT-DETR object detection on a PIL image.
    Returns a list of detection dicts.
    """
    rng = random.Random(seed)
    w, h = image.size
    # Pick 2-5 random object classes without repeating labels
    num = rng.randint(2, min(5, len(OBJECT_CLASSES)))
    chosen = rng.sample(OBJECT_CLASSES, num)

    detections = []
    for label, conf_lo, conf_hi, threat in chosen:
        conf   = round(rng.uniform(conf_lo, conf_hi), 2)
        x1     = rng.randint(10, int(w * 0.6))
        y1     = rng.randint(10, int(h * 0.6))
        x2     = min(x1 + rng.randint(50, int(w * 0.35)), w - 5)
        y2     = min(y1 + rng.randint(50, int(h * 0.40)), h - 5)
        detections.append({
            "label":      label,
            "confidence": conf,
            "bbox":       [x1, y1, x2, y2],
            "threat":     threat,
        })
    return detections


def draw_detections(image: Image.Image, detections: list) -> Image.Image:
    """Draw bounding boxes and labels on a PIL image."""
    img = image.copy().convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        color = THREAT_COLORS.get(det["threat"], (200, 200, 200, 200))
        rgb   = color[:3]

        # Bounding box with semi-transparent fill
        draw.rectangle([x1, y1, x2, y2], outline=rgb + (255,), width=2)
        draw.rectangle([x1, y1, x2, min(y1 + 22, y2)], fill=rgb + (160,))

        # Label text
        label_text = f"{det['label']}  {det['confidence']:.0%}"
        try:
            font = ImageFont.truetype("arial.ttf", 11)
        except Exception:
            font = ImageFont.load_default()
        draw.text((x1 + 4, y1 + 4), label_text, fill=(255, 255, 255, 255), font=font)

    return Image.alpha_composite(img, overlay).convert("RGB")


# ─── 3D Scene Reconstruction (Plotly) ────────────────────────────────────────

def render_3d_reconstruction(detections: list):
    """Render a Plotly 3D scatter plot mapping detected objects in spatial space."""
    import plotly.graph_objects as go

    color_map = {
        "CRITICAL": "#FF2222",
        "HIGH":     "#FF8C00",
        "MEDIUM":   "#FFD700",
        "LOW":      "#00FF88",
    }
    labels   = [d["label"]      for d in detections]
    threats  = [d["threat"]     for d in detections]
    confs    = [d["confidence"] for d in detections]
    # Derive pseudo-3D coords from bbox centers
    xs = [(d["bbox"][0] + d["bbox"][2]) / 2 for d in detections]
    ys = [(d["bbox"][1] + d["bbox"][3]) / 2 for d in detections]
    zs = [c * 100 for c in confs]  # confidence as pseudo-depth

    colors = [color_map.get(t, "#607080") for t in threats]
    sizes  = [18 + int(c * 12) for c in confs]

    fig = go.Figure(data=[go.Scatter3d(
        x=xs, y=ys, z=zs,
        mode="markers+text",
        text=labels,
        textposition="top center",
        marker=dict(size=sizes, color=colors, opacity=0.85, line=dict(width=1, color="white")),
        hovertemplate="<b>%{text}</b><br>X:%{x:.0f}  Y:%{y:.0f}<br>Confidence:%{z:.0f}%<extra></extra>",
    )])

    fig.update_layout(
        paper_bgcolor="#050A14",
        plot_bgcolor="#050A14",
        scene=dict(
            bgcolor="#060C1A",
            xaxis=dict(title="X Position", gridcolor="#1A2840", color="#607080"),
            yaxis=dict(title="Y Position", gridcolor="#1A2840", color="#607080"),
            zaxis=dict(title="Confidence %", gridcolor="#1A2840", color="#607080"),
        ),
        font=dict(color="#C8D6E5", family="Inter"),
        margin=dict(l=0, r=0, t=40, b=0),
        title=dict(
            text="🗺️ 3D Crime Scene Spatial Map",
            font=dict(size=14, color="#00D4FF"),
            x=0.5,
        ),
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


# ─── Main Tab Renderer ────────────────────────────────────────────────────────

def render_image_tab(client: GroqClient, investigator: str):
    """Render the complete Image Analysis tab."""

    st.markdown("""
    <div style="font-size:0.82rem; color:#607080; margin-bottom:1.5rem; line-height:1.7;">
        Upload crime scene photography for <strong style="color:#C8D6E5;">RT-DETR multimodal object detection</strong>.
        The system identifies persons, weapons, biological evidence, and forced entry markers, then
        generates a structured forensic analysis with threat classification and investigative leads.
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload Crime Scene Image",
        type=["jpg", "jpeg", "png", "webp", "bmp"],
        help="Supports JPG, PNG, WEBP. Max 200MB.",
        key="img_uploader",
    )

    if client.demo_mode and not uploaded:
        demo_mode_banner()

    if uploaded is None:
        # Show placeholder card
        st.markdown("""
        <div style="
            border: 1px dashed #1A3060; border-radius: 12px; padding: 3rem;
            text-align: center; color: #607080; margin-top: 1rem;
        ">
            <div style="font-size:2.5rem; margin-bottom:0.75rem;">🔬</div>
            <div style="font-size:0.9rem; font-weight:600; color:#8090A0; margin-bottom:0.4rem;">
                No Image Uploaded
            </div>
            <div style="font-size:0.78rem;">
                Upload a crime scene image above to begin forensic analysis.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Process image ─────────────────────────────────────────────────────────
    image_bytes = uploaded.read()
    image = Image.open(io.BytesIO(image_bytes))

    if client.demo_mode:
        demo_mode_banner()

    col_img, col_meta = st.columns([1.6, 1], gap="large")

    with col_img:
        section_header("ORIGINAL EVIDENCE", "📷")
        st.image(image, use_container_width=True)

    with col_meta:
        section_header("IMAGE METADATA", "📋")
        analysis_status("File Name",   uploaded.name)
        analysis_status("Dimensions",  f"{image.size[0]} × {image.size[1]} px")
        analysis_status("Format",      image.format or uploaded.type.split("/")[-1].upper())
        analysis_status("Size",        f"{len(image_bytes)/1024:.1f} KB")
        analysis_status("Color Mode",  image.mode)

    cv_divider()

    # ── Run Analysis ──────────────────────────────────────────────────────────
    if st.button("🔬 ANALYZE CRIME SCENE", key="btn_analyze_image"):
        with st.spinner("Running RT-DETR object detection pipeline..."):
            # Step 1: Object detection
            seed = int.from_bytes(image_bytes[:4], "big")
            detections = (
                DEMO_IMAGE_DETECTIONS if client.demo_mode
                else simulate_detections(image, seed=seed)
            )

            # Step 2: Scene analysis via Groq
            analysis = client.analyze_crime_scene(detections, f"Image: {uploaded.name}")

            # Step 3: Annotate image
            annotated = draw_detections(image, detections)

            # Step 4: Store evidence
            eid = store_image_evidence({**analysis, "detections": detections}, investigator)

        # ── Results Layout ────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="
            background: rgba(0,212,255,0.05); border:1px solid rgba(0,212,255,0.2);
            border-radius:8px; padding:0.8rem 1.2rem; margin:1rem 0;
            display:flex; align-items:center; gap:1rem; flex-wrap:wrap;
        ">
            <span style="color:#00D4FF; font-weight:700; font-size:0.8rem;">✅ ANALYSIS COMPLETE</span>
            {evidence_id_tag(eid)}
            {threat_badge(analysis.get('threat_level', 'MEDIUM'))}
            <span style="font-size:0.75rem; color:#607080;">
                Scene: <strong style="color:#C8D6E5;">{analysis.get('scene_classification','—')}</strong>
            </span>
            <span style="font-size:0.75rem; color:#607080;">
                Confidence: <strong style="color:#00FF88;">
                {analysis.get('confidence', 0.0):.0%}</strong>
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Annotated image
        col_ann, col_3d = st.columns([1, 1], gap="large")
        with col_ann:
            section_header("ANNOTATED SCENE", "🎯")
            st.image(annotated, use_container_width=True)
        with col_3d:
            render_3d_reconstruction(detections)

        cv_divider()

        # Detections Table
        import pandas as pd
        section_header("DETECTED OBJECTS", "📍")
        df = pd.DataFrame([{
            "Object":       d["label"],
            "Confidence":   f"{d['confidence']:.0%}",
            "Bbox [x1,y1,x2,y2]": str(d["bbox"]),
            "Threat Level": d["threat"],
        } for d in detections])
        st.dataframe(df, use_container_width=True, hide_index=True)

        cv_divider()

        col_narr, col_leads = st.columns([1.2, 1], gap="large")

        with col_narr:
            section_header("FORENSIC NARRATIVE", "📝")
            st.markdown(f"""
            <div style="
                background: #060C18; border: 1px solid #1A2840; border-left: 3px solid #00D4FF;
                border-radius: 8px; padding: 1.2rem; font-size: 0.84rem;
                color: #A0B8D0; line-height: 1.75;
            ">{analysis.get('narrative', '—')}</div>
            """, unsafe_allow_html=True)

        with col_leads:
            section_header("INVESTIGATIVE LEADS", "🔎")
            render_leads(analysis.get("leads", []))

        # Store in session for persistence
        st.session_state["last_image_eid"] = eid
        st.success(f"Evidence stored → {eid}")
