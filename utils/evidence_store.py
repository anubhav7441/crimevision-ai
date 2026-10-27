"""
CrimeVision AI – In-Memory Evidence Store
Session-state based evidence ledger with no external database dependencies.
"""
import streamlit as st
from datetime import datetime
from config.settings import generate_evidence_id, build_custody_record


def _init():
    """Initialize the evidence store in Streamlit session state."""
    if "evidence_store" not in st.session_state:
        st.session_state.evidence_store = {
            "image":  [],
            "audio":  [],
            "video":  [],
            "fusion": [],
        }
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def store_image_evidence(analysis: dict, investigator: str = "SYSTEM") -> str:
    """Store image analysis result and return evidence ID."""
    _init()
    eid = generate_evidence_id("IMG")
    record = {
        "evidence_id":  eid,
        "type":         "IMAGE",
        "timestamp":    datetime.utcnow().isoformat() + "Z",
        "investigator": investigator,
        "data":         analysis,
        "custody":      build_custody_record(eid, investigator, "Crime Scene Image"),
    }
    st.session_state.evidence_store["image"].append(record)
    return eid


def store_audio_evidence(transcript: str, timeline: list, investigator: str = "SYSTEM") -> str:
    """Store audio analysis result and return evidence ID."""
    _init()
    eid = generate_evidence_id("AUD")
    record = {
        "evidence_id":  eid,
        "type":         "AUDIO",
        "timestamp":    datetime.utcnow().isoformat() + "Z",
        "investigator": investigator,
        "data":         {"transcript": transcript, "timeline": timeline},
        "custody":      build_custody_record(eid, investigator, "Witness Audio"),
    }
    st.session_state.evidence_store["audio"].append(record)
    return eid


def store_video_evidence(events: list, investigator: str = "SYSTEM") -> str:
    """Store video analysis result and return evidence ID."""
    _init()
    eid = generate_evidence_id("VID")
    record = {
        "evidence_id":  eid,
        "type":         "VIDEO",
        "timestamp":    datetime.utcnow().isoformat() + "Z",
        "investigator": investigator,
        "data":         {"events": events},
        "custody":      build_custody_record(eid, investigator, "CCTV Footage"),
    }
    st.session_state.evidence_store["video"].append(record)
    return eid


def get_all_evidence() -> list:
    """Return a flat list of all stored evidence records."""
    _init()
    store = st.session_state.evidence_store
    return store["image"] + store["audio"] + store["video"] + store["fusion"]


def build_evidence_context() -> str:
    """Build a formatted text context string for LLM prompting."""
    records = get_all_evidence()
    if not records:
        return "No evidence has been analyzed yet."
    parts = []
    for r in records:
        parts.append(f"[{r['evidence_id']}] Type: {r['type']} | Captured: {r['timestamp']}")
        d = r["data"]
        if r["type"] == "IMAGE":
            parts.append(f"  Scene: {d.get('scene_classification','N/A')} | Threat: {d.get('threat_level','N/A')}")
            parts.append(f"  Narrative: {d.get('narrative','')}")
            leads = d.get("leads", [])
            if leads:
                parts.append(f"  Leads: {'; '.join(str(l) for l in leads[:3])}")
        elif r["type"] == "AUDIO":
            events = d.get("timeline", [])
            critical = [e for e in events if e.get("significance") == "CRITICAL"]
            parts.append(f"  Transcript events: {len(events)} total, {len(critical)} critical")
            for e in critical[:4]:
                parts.append(f"    [{e['timestamp']}] {e['speaker']}: {e['event']}")
        elif r["type"] == "VIDEO":
            events = d.get("events", [])
            parts.append(f"  Video events: {len(events)} logged")
            for e in events[:5]:
                objs = ", ".join(e.get("objects", []))
                parts.append(f"    [{e['timestamp']}] {e['event']} ({objs})")
        parts.append("")
    return "\n".join(parts)


def get_chat_history() -> list:
    """Return the current chat history."""
    _init()
    return st.session_state.chat_history


def append_chat(role: str, content: str):
    """Append a message to chat history."""
    _init()
    st.session_state.chat_history.append({
        "role":      role,
        "content":   content,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


def clear_chat():
    """Clear chat history."""
    _init()
    st.session_state.chat_history = []


def has_evidence() -> bool:
    """Return True if any evidence has been stored."""
    _init()
    return bool(get_all_evidence())
