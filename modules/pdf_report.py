"""
CrimeVision AI – Module 5: Automated Forensic PDF Export
Tab 5 of the main application. Uses ReportLab to generate court-admissible PDF reports.
"""
import io
from datetime import datetime, timezone

import streamlit as st

from utils.ui_helpers import section_header, cv_divider, demo_mode_banner
from utils.evidence_store import get_all_evidence, build_evidence_context, has_evidence
from utils.groq_client import GroqClient
from config.settings import APP_NAME, APP_VERSION

try:
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak, KeepTogether,
    )
    from reportlab.platypus.flowables import BalancedColumns
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ─── Color Palette (ReportLab HexColor) ──────────────────────────────────────

def _hex(h: str):
    """Convert hex string to ReportLab HexColor."""
    from reportlab.lib.colors import HexColor
    return HexColor(h)


# ─── PDF Builder ──────────────────────────────────────────────────────────────

def build_forensic_pdf(
    case_id: str,
    investigator: str,
    records: list,
    executive_summary: str,
) -> bytes:
    """Build and return a complete forensic PDF as bytes."""

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
        title=f"CrimeVision AI Forensic Report – {case_id}",
        author=investigator,
    )

    styles = getSampleStyleSheet()
    W, H   = A4
    now    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # ── Custom Styles ──────────────────────────────────────────────────────────

    def style(name, **kw):
        return ParagraphStyle(name, **kw)

    S = {
        "cover_title": style("cov_title",
            fontSize=28, textColor=_hex("#00D4FF"), alignment=TA_CENTER,
            fontName="Helvetica-Bold", spaceAfter=6, leading=34),
        "cover_sub": style("cov_sub",
            fontSize=12, textColor=_hex("#607080"), alignment=TA_CENTER,
            fontName="Helvetica", spaceAfter=4),
        "cover_meta": style("cov_meta",
            fontSize=9, textColor=_hex("#A0B8D0"), alignment=TA_CENTER,
            fontName="Helvetica", spaceAfter=3),
        "section_h1": style("sec_h1",
            fontSize=13, textColor=_hex("#00D4FF"), fontName="Helvetica-Bold",
            spaceBefore=16, spaceAfter=6, borderPad=4),
        "section_h2": style("sec_h2",
            fontSize=10, textColor=_hex("#8090A0"), fontName="Helvetica-Bold",
            spaceBefore=10, spaceAfter=4, textTransform="uppercase"),
        "body": style("body",
            fontSize=9, textColor=_hex("#C8D6E5"), fontName="Helvetica",
            leading=14, spaceAfter=4, alignment=TA_JUSTIFY),
        "mono": style("mono",
            fontSize=8, textColor=_hex("#A0B8D0"), fontName="Courier",
            leading=12, spaceAfter=2),
        "lead": style("lead",
            fontSize=9, textColor=_hex("#A0B8D0"), fontName="Helvetica",
            leading=13, spaceAfter=3, leftIndent=12),
        "caption": style("caption",
            fontSize=7.5, textColor=_hex("#607080"), fontName="Helvetica-Oblique",
            alignment=TA_CENTER, spaceAfter=4),
        "eid": style("eid",
            fontSize=8, textColor=_hex("#00D4FF"), fontName="Courier-Bold",
            spaceAfter=2),
        "warning": style("warning",
            fontSize=8.5, textColor=_hex("#FF8C00"), fontName="Helvetica-Bold",
            alignment=TA_CENTER, spaceAfter=6),
    }

    # ── Table style factory ────────────────────────────────────────────────────

    def table_style(header_bg="#0D2040"):
        return TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0),   _hex(header_bg)),
            ("TEXTCOLOR",   (0, 0), (-1, 0),   _hex("#00D4FF")),
            ("FONTNAME",    (0, 0), (-1, 0),   "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, 0),   8),
            ("FONTNAME",    (0, 1), (-1, -1),  "Courier"),
            ("FONTSIZE",    (0, 1), (-1, -1),  7.5),
            ("TEXTCOLOR",   (0, 1), (-1, -1),  _hex("#C8D6E5")),
            ("BACKGROUND",  (0, 1), (-1, -1),  _hex("#060C18")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_hex("#060C18"), _hex("#0A1628")]),
            ("ALIGN",       (0, 0), (-1, -1),  "LEFT"),
            ("VALIGN",      (0, 0), (-1, -1),  "TOP"),
            ("GRID",        (0, 0), (-1, -1),  0.4, _hex("#1A2840")),
            ("TOPPADDING",  (0, 0), (-1, -1),  4),
            ("BOTTOMPADDING",(0,0), (-1, -1),  4),
            ("LEFTPADDING", (0, 0), (-1, -1),  6),
            ("RIGHTPADDING",(0, 0), (-1, -1),  6),
        ])

    # ── Build Story ────────────────────────────────────────────────────────────

    story = []

    # ── COVER PAGE ─────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 3*cm),
        Paragraph("⚖ CRIMEVISION AI", S["cover_title"]),
        Paragraph("Intelligent Multimodal Forensic Analysis Platform", S["cover_sub"]),
        Spacer(1, 0.5*cm),
        HRFlowable(width="100%", thickness=1, color=_hex("#1A2840"), spaceAfter=0.4*cm),
        Paragraph("FORENSIC INTELLIGENCE REPORT", S["cover_sub"]),
        Paragraph("OFFICIAL — FOR INVESTIGATIVE USE ONLY", S["warning"]),
        HRFlowable(width="100%", thickness=1, color=_hex("#1A2840"), spaceBefore=0.4*cm, spaceAfter=0.5*cm),
        Spacer(1, 0.5*cm),
    ]

    # Cover metadata table
    cov_data = [
        ["CASE / EVIDENCE ID",   case_id],
        ["INVESTIGATOR",         investigator],
        ["REPORT GENERATED",     now],
        ["PLATFORM VERSION",     APP_VERSION],
        ["EVIDENCE STREAMS",     f"{len(records)} items analyzed"],
        ["CLASSIFICATION",       "SENSITIVE — LAW ENFORCEMENT ONLY"],
    ]
    cov_table = Table(cov_data, colWidths=[5*cm, 11*cm])
    cov_table.setStyle(table_style())
    story += [cov_table, Spacer(1, 1*cm)]

    from reportlab.lib.colors import HexColor
    # Hash block
    story += [
        Paragraph("CHAIN OF CUSTODY HASH", S["section_h2"]),
        Paragraph(
            " · ".join(
                r.get("custody", {}).get("hash", "—")
                for r in records[:4]
            ) or "No records",
            S["mono"]
        ),
        PageBreak(),
    ]

    # ── EXECUTIVE SUMMARY ──────────────────────────────────────────────────────
    story += [
        Paragraph("1. EXECUTIVE SUMMARY", S["section_h1"]),
        HRFlowable(width="100%", thickness=0.5, color=_hex("#1A2840"), spaceAfter=0.3*cm),
        Paragraph(executive_summary.replace("\n", "<br/>"), S["body"]),
        Spacer(1, 0.5*cm),
    ]

    # ── IMAGE EVIDENCE ─────────────────────────────────────────────────────────
    img_records = [r for r in records if r["type"] == "IMAGE"]
    if img_records:
        story += [
            Paragraph("2. VISUAL EVIDENCE ANALYSIS", S["section_h1"]),
            HRFlowable(width="100%", thickness=0.5, color=_hex("#1A2840"), spaceAfter=0.3*cm),
        ]
        for r in img_records:
            d = r["data"]
            story.append(Paragraph(f"Evidence ID: {r['evidence_id']}", S["eid"]))
            meta = [
                ["Scene Classification", d.get("scene_classification", "—")],
                ["Threat Level",         d.get("threat_level", "—")],
                ["Confidence",           f"{d.get('confidence', 0):.0%}"],
                ["Captured (UTC)",       r.get("timestamp", "—")],
            ]
            mt = Table(meta, colWidths=[5*cm, 11*cm])
            mt.setStyle(table_style())
            story.append(mt)
            story.append(Spacer(1, 0.25*cm))
            story.append(Paragraph(d.get("narrative", ""), S["body"]))
            story.append(Spacer(1, 0.25*cm))

            # Detections table
            dets = d.get("detections", [])
            if dets:
                story.append(Paragraph("Detected Objects", S["section_h2"]))
                det_data = [["Object", "Confidence", "Bounding Box", "Threat"]]
                for det in dets:
                    det_data.append([
                        det.get("label",""),
                        f"{det.get('confidence',0):.0%}",
                        str(det.get("bbox",[])),
                        det.get("threat",""),
                    ])
                dt = Table(det_data, colWidths=[4*cm, 2.5*cm, 5*cm, 2.5*cm], repeatRows=1)
                dt.setStyle(table_style())
                story.append(dt)

            leads = d.get("leads", [])
            if leads:
                story.append(Spacer(1, 0.2*cm))
                story.append(Paragraph("Investigative Leads", S["section_h2"]))
                for i, lead in enumerate(leads, 1):
                    story.append(Paragraph(f"{i}. {lead}", S["lead"]))
            story.append(Spacer(1, 0.4*cm))

    # ── AUDIO EVIDENCE ─────────────────────────────────────────────────────────
    aud_records = [r for r in records if r["type"] == "AUDIO"]
    if aud_records:
        story += [
            Paragraph("3. WITNESS AUDIO TRANSCRIPTION & TIMELINE", S["section_h1"]),
            HRFlowable(width="100%", thickness=0.5, color=_hex("#1A2840"), spaceAfter=0.3*cm),
        ]
        for r in aud_records:
            d = r["data"]
            story.append(Paragraph(f"Evidence ID: {r['evidence_id']}", S["eid"]))
            # Transcript snippet
            transcript = d.get("transcript", "")
            lines = transcript.split("\n")[:20]
            story.append(Paragraph("Transcript (first 20 lines)", S["section_h2"]))
            for line in lines:
                story.append(Paragraph(line, S["mono"]))
            if len(transcript.split("\n")) > 20:
                story.append(Paragraph("[ ... transcript continues ... ]", S["caption"]))
            story.append(Spacer(1, 0.25*cm))

            # Timeline table
            timeline = d.get("timeline", [])
            if timeline:
                story.append(Paragraph("Event Timeline", S["section_h2"]))
                tl_data = [["Timestamp", "Speaker", "Event", "Significance"]]
                for ev in timeline:
                    tl_data.append([
                        ev.get("timestamp",""),
                        ev.get("speaker",""),
                        Paragraph(ev.get("event",""), S["body"]),
                        ev.get("significance",""),
                    ])
                tlt = Table(tl_data, colWidths=[1.8*cm, 2.8*cm, 9*cm, 2.4*cm], repeatRows=1)
                tlt.setStyle(table_style())
                story.append(tlt)
            story.append(Spacer(1, 0.4*cm))

    # ── VIDEO EVIDENCE ─────────────────────────────────────────────────────────
    vid_records = [r for r in records if r["type"] == "VIDEO"]
    if vid_records:
        story += [
            Paragraph("4. CCTV VIDEO ANALYSIS & EVENT LOG", S["section_h1"]),
            HRFlowable(width="100%", thickness=0.5, color=_hex("#1A2840"), spaceAfter=0.3*cm),
        ]
        for r in vid_records:
            d = r["data"]
            story.append(Paragraph(f"Evidence ID: {r['evidence_id']}", S["eid"]))
            events = d.get("events", [])
            if events:
                ev_data = [["Timestamp", "Event", "Objects", "Category", "Conf."]]
                for ev in events:
                    ev_data.append([
                        ev.get("timestamp",""),
                        Paragraph(ev.get("event",""), S["body"]),
                        ", ".join(ev.get("objects",[])),
                        ev.get("category",""),
                        f"{ev.get('confidence',0.8):.0%}",
                    ])
                evt = Table(ev_data, colWidths=[1.8*cm, 5.5*cm, 3*cm, 3.2*cm, 1.5*cm], repeatRows=1)
                evt.setStyle(table_style())
                story.append(evt)
            story.append(Spacer(1, 0.4*cm))

    # ── CONCLUSIONS ────────────────────────────────────────────────────────────
    story += [
        Paragraph("5. MULTIMODAL FUSION CONCLUSIONS", S["section_h1"]),
        HRFlowable(width="100%", thickness=0.5, color=_hex("#1A2840"), spaceAfter=0.3*cm),
        Paragraph(
            f"This report synthesizes findings from {len(img_records)} image stream(s), "
            f"{len(aud_records)} audio stream(s), and {len(vid_records)} video stream(s). "
            "All evidence has been processed through the CrimeVision AI multimodal pipeline "
            "and the results above represent the system's best assessment based on available data. "
            "Investigators should treat AI-generated assessments as investigative support tools "
            "and not as standalone legal conclusions. All evidence items have been assigned "
            "unique chain-of-custody hashes for legal admissibility tracking.",
            S["body"]
        ),
        Spacer(1, 0.5*cm),
    ]

    # ── SIGNATURE BLOCK ────────────────────────────────────────────────────────
    sig_data = [
        ["Prepared by:", investigator, "Date:", now[:10]],
        ["Platform:",    f"CrimeVision AI v{APP_VERSION}", "Classification:", "LAW ENFORCEMENT SENSITIVE"],
    ]
    sig_t = Table(sig_data, colWidths=[3*cm, 8*cm, 2.5*cm, 4*cm])
    sig_t.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("TEXTCOLOR",   (0, 0), (0, -1),  _hex("#607080")),
        ("TEXTCOLOR",   (2, 0), (2, -1),  _hex("#607080")),
        ("TEXTCOLOR",   (1, 0), (1, -1),  _hex("#C8D6E5")),
        ("TEXTCOLOR",   (3, 0), (3, -1),  _hex("#C8D6E5")),
        ("GRID",        (0, 0), (-1, -1), 0.3, _hex("#1A2840")),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1),  5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND",  (0, 0), (-1, -1), _hex("#060C18")),
    ]))

    story += [
        HRFlowable(width="100%", thickness=0.5, color=_hex("#1A2840"), spaceAfter=0.4*cm),
        Paragraph("INVESTIGATOR SIGN-OFF", S["section_h2"]),
        sig_t,
        Spacer(1, 1.5*cm),
        Paragraph(
            "⚠ OFFICIAL DOCUMENT — Unauthorized disclosure is prohibited. "
            "This report was generated by an AI system and must be reviewed by a certified forensic examiner.",
            ParagraphStyle("footer", fontSize=7, textColor=_hex("#3A4A5A"),
                          alignment=TA_CENTER, fontName="Helvetica-Oblique")
        ),
    ]

    doc.build(story)
    return buf.getvalue()


# ─── Main Tab Renderer ────────────────────────────────────────────────────────

def render_pdf_tab(client: GroqClient, case_id: str, investigator: str):
    """Render the PDF export tab."""

    st.markdown("""
    <div style="font-size:0.82rem; color:#607080; margin-bottom:1.5rem; line-height:1.7;">
        Generate a <strong style="color:#C8D6E5;">court-admissible forensic summary PDF</strong>
        containing all analyzed evidence, chain-of-custody hashes, investigative conclusions,
        and an AI-generated executive summary. The report is formatted to professional forensic
        standards using ReportLab.
    </div>
    """, unsafe_allow_html=True)

    if not REPORTLAB_AVAILABLE:
        st.error("❌ ReportLab is not installed. Run: `pip install reportlab`")
        return

    records = get_all_evidence()

    if client.demo_mode:
        demo_mode_banner()

    # ── Report Config ──────────────────────────────────────────────────────────
    section_header("REPORT CONFIGURATION", "⚙️")
    col1, col2 = st.columns(2, gap="large")
    with col1:
        pdf_case_id    = st.text_input("Case / Evidence ID", value=case_id, key="pdf_case")
        pdf_investigator = st.text_input("Lead Investigator", value=investigator, key="pdf_inv")
    with col2:
        include_summary = st.checkbox("Include AI Executive Summary", value=True)
        st.markdown(f"""
        <div style="font-size:0.78rem; color:#607080; margin-top:0.5rem;">
            📋 Evidence streams ready for export:
            <strong style="color:#00D4FF;">{len(records)}</strong> total
            ({sum(1 for r in records if r['type']=='IMAGE')} img,
             {sum(1 for r in records if r['type']=='AUDIO')} aud,
             {sum(1 for r in records if r['type']=='VIDEO')} vid)
        </div>
        """, unsafe_allow_html=True)

    cv_divider()

    # ── Report Preview ─────────────────────────────────────────────────────────
    section_header("REPORT SECTIONS", "📑")
    sections = [
        ("📋 Cover Page",                  "Case ID, Investigator, Timestamp, Chain-of-Custody hashes"),
        ("📊 Executive Summary",           "AI-generated overview of all analyzed evidence"),
        ("📷 Visual Evidence",             "RT-DETR detections, scene classification, investigative leads"),
        ("🎙️ Audio Transcript & Timeline", "Full transcript, speaker timeline, critical event markers"),
        ("📹 CCTV Event Log",              "Chronological video events with crime classifications"),
        ("🔗 Multimodal Conclusions",      "Cross-evidence synthesis and investigative recommendations"),
        ("✍️ Investigator Sign-off",       "Digital signature block for legal admissibility"),
    ]
    for icon_title, desc in sections:
        st.markdown(f"""
        <div style="display:flex; gap:0.75rem; align-items:flex-start; padding:0.5rem 0;
                    border-bottom:1px solid #1A2840;">
            <span style="font-size:0.82rem; font-weight:600; color:#C8D6E5; min-width:14rem;">{icon_title}</span>
            <span style="font-size:0.78rem; color:#607080;">{desc}</span>
        </div>
        """, unsafe_allow_html=True)

    cv_divider()

    if st.button("📄 GENERATE FORENSIC PDF REPORT", key="btn_gen_pdf"):
        if not records and not client.demo_mode:
            st.warning("⚠️ No evidence analyzed yet. Complete analysis in Tabs 1–3 first.")
            return

        with st.spinner("Generating court-admissible forensic PDF report..."):
            # Generate executive summary
            if include_summary:
                ctx  = build_evidence_context()
                exec_summary = client.generate_executive_summary(ctx)
            else:
                exec_summary = "Executive summary omitted per investigator request."

            # Provide demo records if none exist
            if not records:
                from config.settings import (
                    DEMO_IMAGE_DETECTIONS, DEMO_SCENE_ANALYSIS,
                    DEMO_AUDIO_TRANSCRIPT, DEMO_AUDIO_TIMELINE,
                    DEMO_VIDEO_EVENTS, generate_evidence_id, build_custody_record
                )
                from datetime import datetime
                now = datetime.utcnow().isoformat() + "Z"
                records = [
                    {
                        "evidence_id": generate_evidence_id("IMG"),
                        "type":        "IMAGE",
                        "timestamp":   now,
                        "investigator": pdf_investigator,
                        "data":        {**DEMO_SCENE_ANALYSIS, "detections": DEMO_IMAGE_DETECTIONS},
                        "custody":     build_custody_record("DEMO-IMG", pdf_investigator, "Crime Scene Image"),
                    },
                    {
                        "evidence_id": generate_evidence_id("AUD"),
                        "type":        "AUDIO",
                        "timestamp":   now,
                        "investigator": pdf_investigator,
                        "data":        {"transcript": DEMO_AUDIO_TRANSCRIPT, "timeline": DEMO_AUDIO_TIMELINE},
                        "custody":     build_custody_record("DEMO-AUD", pdf_investigator, "Witness Audio"),
                    },
                    {
                        "evidence_id": generate_evidence_id("VID"),
                        "type":        "VIDEO",
                        "timestamp":   now,
                        "investigator": pdf_investigator,
                        "data":        {"events": DEMO_VIDEO_EVENTS},
                        "custody":     build_custody_record("DEMO-VID", pdf_investigator, "CCTV Footage"),
                    },
                ]

            pdf_bytes = build_forensic_pdf(
                case_id     = pdf_case_id,
                investigator= pdf_investigator,
                records     = records,
                executive_summary = exec_summary,
            )

        # ── Download ───────────────────────────────────────────────────────────
        fname = f"CrimeVision_Report_{pdf_case_id.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        st.success("✅ Forensic PDF report generated successfully!")
        st.markdown(f"""
        <div style="
            background:rgba(0,255,136,0.05); border:1px solid rgba(0,255,136,0.2);
            border-radius:8px; padding:0.8rem 1.2rem; margin:0.75rem 0;
            font-size:0.82rem; color:#00FF88;
        ">
            📄 <strong>{fname}</strong> — {len(pdf_bytes)/1024:.1f} KB
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label     = "⬇️ DOWNLOAD FORENSIC PDF",
            data      = pdf_bytes,
            file_name = fname,
            mime      = "application/pdf",
            key       = "btn_download_pdf",
        )

        st.markdown("""
        <div style="font-size:0.75rem; color:#607080; margin-top:0.5rem; line-height:1.6;">
            ⚠️ This report is AI-generated and must be reviewed by a certified forensic examiner
            before use as legal evidence. Ensure chain-of-custody documentation complies with
            your jurisdiction's evidentiary standards.
        </div>
        """, unsafe_allow_html=True)
