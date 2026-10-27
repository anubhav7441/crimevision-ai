"""
CrimeVision AI – Configuration & Constants
"""
import hashlib
import uuid
from datetime import datetime

# ─── App Metadata ────────────────────────────────────────────────────────────
APP_NAME = "CrimeVision AI"
APP_SUBTITLE = "Intelligent Multimodal Forensic Analysis Platform"
APP_VERSION = "2.0.0"
PROJECT_LABEL = "Skill Wallet Capstone Project 2"

# ─── Threat Level Definitions ────────────────────────────────────────────────
THREAT_LEVELS = {
    "LOW":      {"color": "#00FF88", "icon": "🟢", "badge": "LOW THREAT"},
    "MEDIUM":   {"color": "#FFD700", "icon": "🟡", "badge": "MEDIUM THREAT"},
    "HIGH":     {"color": "#FF8C00", "icon": "🟠", "badge": "HIGH THREAT"},
    "CRITICAL": {"color": "#FF2222", "icon": "🔴", "badge": "CRITICAL THREAT"},
}

# ─── Crime Categories ─────────────────────────────────────────────────────────
CRIME_CATEGORIES = [
    "Homicide", "Assault & Battery", "Robbery", "Burglary",
    "Vandalism", "Arson", "Kidnapping", "Drug Trafficking",
    "Weapon Possession", "Trespassing", "Suspicious Activity",
]

# ─── Detectable Object Classes ────────────────────────────────────────────────
DETECTABLE_OBJECTS = [
    "Person", "Firearm", "Edged Weapon", "Blood Spatter",
    "Forced Entry Point", "Vehicle", "Suspicious Package",
    "Shell Casing", "Mask/Disguise", "Contraband",
]

# ─── Scene Classifications ────────────────────────────────────────────────────
SCENE_CLASSIFICATIONS = [
    "Homicide Scene", "Burglary Scene", "Assault Scene",
    "Vandalism Scene", "Robbery Scene", "Arson Scene",
    "Drug-Related Scene", "Suspicious Activity",
]

# ─── Chain of Custody ─────────────────────────────────────────────────────────

def generate_evidence_id(prefix: str = "EVD") -> str:
    """Generate a unique forensic evidence ID."""
    uid = str(uuid.uuid4()).upper()[:8]
    ts  = datetime.utcnow().strftime("%Y%m%d")
    return f"{prefix}-{ts}-{uid}"

def generate_case_hash(case_id: str, investigator: str, timestamp: str) -> str:
    """Generate a SHA-256 chain-of-custody hash."""
    payload = f"{case_id}|{investigator}|{timestamp}"
    return hashlib.sha256(payload.encode()).hexdigest()[:24].upper()

def build_custody_record(evidence_id: str, investigator: str, source: str) -> dict:
    """Build a chain-of-custody record."""
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "evidence_id":  evidence_id,
        "investigator": investigator,
        "source":       source,
        "timestamp":    ts,
        "hash":         generate_case_hash(evidence_id, investigator, ts),
        "status":       "VERIFIED",
    }

# ─── Demo / Fallback Data ─────────────────────────────────────────────────────

DEMO_IMAGE_DETECTIONS = [
    {"label": "Person",              "confidence": 0.94, "bbox": [120, 45, 200, 310],  "threat": "HIGH"},
    {"label": "Firearm",             "confidence": 0.88, "bbox": [178, 195, 235, 255], "threat": "CRITICAL"},
    {"label": "Blood Spatter",       "confidence": 0.76, "bbox": [60,  280, 160, 340], "threat": "HIGH"},
    {"label": "Forced Entry Point",  "confidence": 0.82, "bbox": [300, 10,  430, 120], "threat": "MEDIUM"},
    {"label": "Shell Casing",        "confidence": 0.71, "bbox": [200, 310, 240, 340], "threat": "HIGH"},
]

DEMO_SCENE_ANALYSIS = {
    "threat_level":        "CRITICAL",
    "scene_classification":"Homicide Scene",
    "confidence":          0.91,
    "narrative": (
        "The scene exhibits strong indicators of a violent confrontation. "
        "A firearm was detected with high confidence near the central subject, "
        "and biological material (blood spatter) is consistent with a ballistic event. "
        "Forced entry markers on the upper-right structure suggest the scene was not a consensual encounter. "
        "Shell casings near the subject's feet indicate discharge occurred at close range."
    ),
    "leads": [
        "Recover ballistic evidence – shell casings at coordinates (200,310).",
        "Process biological material for DNA – blood spatter cluster at (60,280).",
        "Examine forced entry point for latent fingerprints and tool marks.",
        "Canvass area for witnesses within 500m radius.",
        "Request CCTV footage from adjacent establishments.",
    ],
}

DEMO_AUDIO_TRANSCRIPT = """[00:00] Caller: 911, what's your emergency?
[00:03] Witness: Yes – hello – I need police NOW. There were gunshots!
[00:08] Caller: Where are you located?
[00:10] Witness: 4th and Monroe, the alley behind the convenience store.
[00:15] Witness: Two men – they were arguing outside. One pulled a gun.
[00:22] Caller: How many shots did you hear?
[00:24] Witness: Three… maybe four. It happened so fast.
[00:29] Witness: One guy ran north on Monroe. Dark hoodie, medium build.
[00:36] Witness: The other one… he's on the ground. Please hurry!
[00:41] Caller: Units are on the way. Stay on the line and stay away from the area.
[00:47] Witness: There's a black sedan – it just pulled up, licence plate… I can't see it."""

DEMO_AUDIO_TIMELINE = [
    {"timestamp": "00:00", "speaker": "Dispatcher", "event": "Emergency call initiated",                           "significance": "LOW"},
    {"timestamp": "00:03", "speaker": "Witness",     "event": "Reports gunshots at location",                      "significance": "CRITICAL"},
    {"timestamp": "00:10", "speaker": "Witness",     "event": "Location confirmed: 4th & Monroe alley",            "significance": "HIGH"},
    {"timestamp": "00:15", "speaker": "Witness",     "event": "Two male suspects described arguing",               "significance": "HIGH"},
    {"timestamp": "00:22", "speaker": "Witness",     "event": "3–4 shots fired confirmed",                         "significance": "CRITICAL"},
    {"timestamp": "00:29", "speaker": "Witness",     "event": "Suspect fled north – dark hoodie, medium build",    "significance": "CRITICAL"},
    {"timestamp": "00:36", "speaker": "Witness",     "event": "Victim confirmed down at scene",                    "significance": "CRITICAL"},
    {"timestamp": "00:47", "speaker": "Witness",     "event": "Black sedan arrived post-incident",                 "significance": "HIGH"},
]

DEMO_VIDEO_EVENTS = [
    {"timestamp": "00:02", "event": "Subject enters frame from east entrance",       "objects": ["Person"],                    "category": "Trespassing",          "confidence": 0.87},
    {"timestamp": "00:08", "event": "Subject moves towards counter area",            "objects": ["Person"],                    "category": "Suspicious Activity",  "confidence": 0.81},
    {"timestamp": "00:14", "event": "Second subject enters; confrontation begins",   "objects": ["Person", "Person"],          "category": "Assault & Battery",    "confidence": 0.79},
    {"timestamp": "00:21", "event": "Firearm produced by Subject-1",                 "objects": ["Person", "Firearm"],         "category": "Weapon Possession",    "confidence": 0.93},
    {"timestamp": "00:27", "event": "Subject-2 retreats toward exit",                "objects": ["Person"],                    "category": "Robbery",              "confidence": 0.88},
    {"timestamp": "00:33", "event": "Subject-1 removes items from register",         "objects": ["Person", "Contraband"],      "category": "Robbery",              "confidence": 0.91},
    {"timestamp": "00:40", "event": "Dark vehicle visible through window",           "objects": ["Vehicle"],                   "category": "Suspicious Activity",  "confidence": 0.74},
    {"timestamp": "00:47", "event": "Subject-1 flees through south exit",            "objects": ["Person"],                    "category": "Robbery",              "confidence": 0.96},
    {"timestamp": "00:53", "event": "Vehicle departs northbound at speed",           "objects": ["Vehicle"],                   "category": "Robbery",              "confidence": 0.85},
    {"timestamp": "01:02", "event": "Scene static – victim remains at counter",      "objects": ["Person"],                    "category": "Assault & Battery",    "confidence": 0.89},
]
