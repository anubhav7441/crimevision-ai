# ⚖️ CrimeVision AI – Intelligent Multimodal Forensic Analysis Platform

> **Skill Wallet Capstone Project 2** · v2.0.0

A production-ready, AI-powered forensic analysis platform that processes crime scene images, witness audio, CCTV video, and generates court-admissible PDF reports — all in a single Streamlit application.

---

## 🚀 Live Demo

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app.streamlit.app)

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 📷 **Visual Evidence Tagger** | Upload crime scene photos → AI detects persons, weapons, blood spatter, forced entry with confidence scores & spatial coords |
| 🎙️ **Audio Transcription** | Upload 911 calls / witness audio → Groq Whisper transcription + timestamped forensic timeline |
| 📹 **CCTV Video Analysis** | Upload CCTV clips → Frame-by-frame event progression with suspect tracking & legal crime classification |
| 🔗 **Multimodal Fusion & Chat** | Unified evidence ledger + RAG chat — ask "Was a weapon visible before the suspect fled?" with zero-hallucination, cited answers |
| 📄 **PDF Report Export** | 1-click court-admissible forensic PDF via ReportLab with chain-of-custody header |

---

## 🏗️ Architecture

```
crimevision/
├── app.py                  # Main Streamlit entry point
├── config/
│   └── settings.py         # Constants, demo data, chain-of-custody helpers
├── modules/
│   ├── image_analysis.py   # Tab 1 – Visual Evidence (Epic 2)
│   ├── audio_analysis.py   # Tab 2 – Audio Transcription (Epic 3)
│   ├── video_analysis.py   # Tab 3 – CCTV Video Analysis (Epic 4)
│   ├── fusion.py           # Tab 4 – Multimodal Fusion & Chat (Epic 5)
│   └── pdf_report.py       # Tab 5 – PDF Export (Epic 6)
├── utils/
│   ├── groq_client.py      # Groq API wrapper with demo fallback
│   ├── ui_helpers.py       # CSS injection, header, sidebar helpers
│   └── evidence_store.py   # In-memory evidence ledger
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚡ Quick Start (Local)

### 1. Clone & enter the project
```bash
git clone https://github.com/YOUR_USERNAME/crimevision-ai.git
cd crimevision-ai
```

### 2. Create virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API key (optional — demo mode works without it)
```bash
cp .env.example .env
# Edit .env and add your Groq API key:
# GROQ_API_KEY=gsk_your_key_here
```
> Get a **free** Groq API key at [console.groq.com](https://console.groq.com)

### 5. Run the app
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🌐 Deploy to Streamlit Community Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo, branch `main`, and `app.py` as the entry point
4. In **Advanced settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
5. Click **Deploy** — done! 🎉

---

## 🔑 API Keys

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| [Groq](https://console.groq.com) | LLM inference (Llama 3.3) + Whisper transcription | ✅ Yes |

> **Demo Mode**: The app runs fully without any API key using pre-generated forensic data. All five tabs are functional in demo mode.

---

## 🛡️ Forensic Chain of Custody

Every analysis generates:
- **Evidence ID** — unique SHA-prefixed identifier (e.g., `EVD-20241028-A1B2C3D4`)
- **Timestamp** — UTC ISO-8601 acquisition time
- **Investigator Sign-off** — configurable lead investigator name
- **Case Hash** — SHA-256 integrity fingerprint

---

## 🧰 Tech Stack

- **Frontend**: Streamlit 1.35+
- **LLM / STT**: Groq API (Llama-3.3-70B, Whisper-large-v3)
- **Computer Vision**: OpenCV, Pillow
- **PDF Generation**: ReportLab
- **Visualization**: Plotly
- **Data**: Pandas, NumPy
- **Deployment**: Streamlit Community Cloud

---

## 📜 License

MIT — for educational and research use.

---

*CrimeVision AI is a capstone demonstration platform. It is not intended for operational law enforcement use without proper validation.*
