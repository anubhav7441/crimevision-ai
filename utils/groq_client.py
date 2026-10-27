"""
CrimeVision AI – Groq API Client
Handles all LLM calls with automatic demo/fallback mode when no API key is provided.
"""
import os
import json
import re
from typing import Optional

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


def _clean_json(raw: str) -> str:
    """Strip markdown fences from LLM JSON output."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


class GroqClient:
    """
    Wrapper around the Groq API with graceful demo-mode fallback.
    All methods return structured Python dicts / strings.
    """

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    WHISPER_MODEL = "whisper-large-v3"

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("GROQ_API_KEY", "")
        self.demo_mode = not (key and GROQ_AVAILABLE)
        self._client = None
        if not self.demo_mode:
            try:
                self._client = Groq(api_key=key)
            except Exception:
                self.demo_mode = True

    # ─── Internal Helper ──────────────────────────────────────────────────────

    def _chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        """Fire a single chat completion and return the text content."""
        resp = self._client.chat.completions.create(
            model=self.DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=temperature,
            max_tokens=2048,
        )
        return resp.choices[0].message.content.strip()

    # ─── Image / Scene Analysis ───────────────────────────────────────────────

    def analyze_crime_scene(self, detections: list, image_context: str = "") -> dict:
        """
        Given a list of detections, return structured scene analysis.
        Returns: {threat_level, scene_classification, confidence, narrative, leads}
        """
        if self.demo_mode:
            from config.settings import DEMO_SCENE_ANALYSIS
            return DEMO_SCENE_ANALYSIS

        system = (
            "You are a senior forensic AI analyst. Given detected objects from a crime scene image, "
            "return ONLY a JSON object with these exact keys: "
            "threat_level (one of LOW/MEDIUM/HIGH/CRITICAL), "
            "scene_classification (e.g. Homicide Scene, Burglary Scene), "
            "confidence (float 0-1), "
            "narrative (2-3 sentence forensic description), "
            "leads (list of 4-5 prioritized investigative actions). "
            "Respond with raw JSON only, no markdown fences."
        )
        det_str = "\n".join(
            f"- {d['label']} (confidence: {d['confidence']:.2f}) at bbox {d['bbox']}"
            for d in detections
        )
        user = f"Detected objects:\n{det_str}\n\nAdditional context: {image_context}"
        try:
            raw = self._chat(system, user)
            return json.loads(_clean_json(raw))
        except Exception:
            from config.settings import DEMO_SCENE_ANALYSIS
            return DEMO_SCENE_ANALYSIS

    # ─── Audio Analysis ───────────────────────────────────────────────────────

    def transcribe_audio(self, audio_bytes: bytes, filename: str) -> str:
        """
        Transcribe audio using Groq Whisper API.
        Returns plain-text transcript.
        """
        if self.demo_mode:
            from config.settings import DEMO_AUDIO_TRANSCRIPT
            return DEMO_AUDIO_TRANSCRIPT

        try:
            transcription = self._client.audio.transcriptions.create(
                file=(filename, audio_bytes),
                model=self.WHISPER_MODEL,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
            # Build formatted transcript from segments
            lines = []
            for seg in transcription.segments:
                start = int(seg.start)
                mm, ss = divmod(start, 60)
                lines.append(f"[{mm:02d}:{ss:02d}] {seg.text.strip()}")
            return "\n".join(lines) if lines else transcription.text
        except Exception:
            from config.settings import DEMO_AUDIO_TRANSCRIPT
            return DEMO_AUDIO_TRANSCRIPT

    def analyze_audio_timeline(self, transcript: str) -> list:
        """
        Extract structured timeline events from a transcript.
        Returns list of {timestamp, speaker, event, significance}.
        """
        if self.demo_mode:
            from config.settings import DEMO_AUDIO_TIMELINE
            return DEMO_AUDIO_TIMELINE

        system = (
            "You are a forensic audio analyst. Given a 911 call or witness statement transcript, "
            "extract a structured timeline. Return ONLY a JSON array where each item has: "
            "timestamp (MM:SS string), speaker (e.g. Witness/Dispatcher/Unknown), "
            "event (brief description), significance (LOW/MEDIUM/HIGH/CRITICAL). "
            "Respond with raw JSON array only."
        )
        try:
            raw = self._chat(system, f"Transcript:\n{transcript}")
            return json.loads(_clean_json(raw))
        except Exception:
            from config.settings import DEMO_AUDIO_TIMELINE
            return DEMO_AUDIO_TIMELINE

    # ─── Video Analysis ───────────────────────────────────────────────────────

    def classify_video_events(self, frame_descriptions: list) -> list:
        """
        Given descriptions of sampled video frames, generate chronological event log.
        Returns list of {timestamp, event, objects, category, confidence}.
        """
        if self.demo_mode:
            from config.settings import DEMO_VIDEO_EVENTS
            return DEMO_VIDEO_EVENTS

        system = (
            "You are a forensic video analyst. Given descriptions of CCTV frames sampled at intervals, "
            "produce a chronological crime event log. Return ONLY a JSON array where each item has: "
            "timestamp (MM:SS string), event (forensic description), objects (list of detected object labels), "
            "category (legal penal crime category), confidence (float 0-1). "
            "Respond with raw JSON array only."
        )
        desc_str = "\n".join(f"Frame {i}: {d}" for i, d in enumerate(frame_descriptions))
        try:
            raw = self._chat(system, f"Frame descriptions:\n{desc_str}")
            return json.loads(_clean_json(raw))
        except Exception:
            from config.settings import DEMO_VIDEO_EVENTS
            return DEMO_VIDEO_EVENTS

    # ─── Fusion & Chat ────────────────────────────────────────────────────────

    def forensic_chat(self, question: str, evidence_context: str, chat_history: list) -> str:
        """
        Answer an investigator's natural-language question using grounded evidence only.
        Returns a string answer with citations.
        """
        if self.demo_mode:
            return self._demo_chat_response(question)

        system = (
            "You are a forensic intelligence AI. You have access to structured evidence collected "
            "from crime scene images, audio recordings, and CCTV video analysis. "
            "Answer questions ONLY based on the evidence provided below. "
            "If the evidence does not support an answer, say so explicitly. "
            "Always cite the Evidence ID in brackets, e.g. [EVD-...]. "
            "Never speculate beyond the evidence.\n\n"
            f"EVIDENCE CONTEXT:\n{evidence_context}"
        )
        messages = [{"role": "system", "content": system}]
        for turn in chat_history[-6:]:  # keep last 6 turns for context
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": question})

        try:
            resp = self._client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=1024,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"⚠️ LLM query failed: {str(e)}"

    def generate_executive_summary(self, evidence_context: str) -> str:
        """Generate a concise executive summary of all collected evidence."""
        if self.demo_mode:
            return (
                "EXECUTIVE SUMMARY (DEMO MODE)\n\n"
                "The multimodal forensic analysis has identified a high-probability violent incident "
                "at the analyzed location. Visual evidence confirms the presence of a firearm, biological "
                "material consistent with a ballistic event, and a forced entry point. Audio evidence from "
                "a 911 witness call corroborates 3–4 shots fired, a fleeing suspect in a dark hoodie, and "
                "an unidentified vehicle. CCTV footage captures a chronological robbery/assault sequence "
                "lasting approximately 60 seconds. All evidence streams converge on a Robbery/Homicide "
                "classification with CRITICAL threat level. Immediate investigative priorities include "
                "ballistic recovery, DNA sampling, and canvassing for the black sedan."
            )

        system = (
            "You are a senior forensic analyst. Write a concise, professional executive summary "
            "for a court-admissible forensic report based on the evidence provided. "
            "Use formal language, cite evidence streams (image/audio/video), and conclude with "
            "a risk assessment and recommended next steps. Maximum 200 words."
        )
        try:
            return self._chat(system, f"Evidence context:\n{evidence_context}", temperature=0.2)
        except Exception:
            return "Executive summary generation failed. Please review individual module outputs."

    @staticmethod
    def _demo_chat_response(question: str) -> str:
        """Deterministic demo responses keyed by keyword."""
        q = question.lower()
        if any(w in q for w in ["weapon", "gun", "firearm", "arm"]):
            return (
                "**Yes.** A firearm was detected with 88% confidence at spatial coordinates "
                "bbox[178, 195, 235, 255] in the crime scene image [EVD-IMG-001]. "
                "This detection precedes the suspect's identified flight path per CCTV timeline [EVD-VID-001] "
                "at timestamp 00:21, where the weapon was visibly produced during the confrontation."
            )
        if any(w in q for w in ["suspect", "person", "fled", "flee", "run", "escape"]):
            return (
                "**Confirmed.** Witness audio [EVD-AUD-001] at 00:29 describes a suspect in a dark hoodie "
                "fleeing northbound on Monroe Street. CCTV evidence [EVD-VID-001] at 00:47 corroborates "
                "this — Subject-1 exits through the south door, consistent with a northbound trajectory. "
                "A black sedan departed northbound at 00:53 [EVD-VID-001] and may be associated."
            )
        if any(w in q for w in ["blood", "victim", "injury", "hurt"]):
            return (
                "**Affirmative.** Blood spatter was detected at confidence 76% in the image evidence "
                "[EVD-IMG-001] at coordinates bbox[60, 280, 160, 340], consistent with a ballistic event. "
                "Witness audio [EVD-AUD-001] at 00:36 confirms a victim down at the scene. "
                "DNA processing of this biological material is listed as Investigative Lead #2."
            )
        if any(w in q for w in ["vehicle", "car", "sedan"]):
            return (
                "**Yes.** A dark-colored vehicle was observed through the establishment window at CCTV "
                "timestamp 00:40 [EVD-VID-001] and departed northbound at 00:53. "
                "Witness audio [EVD-AUD-001] at 00:47 also references a black sedan arriving post-incident. "
                "The licence plate was not captured. Recommend requesting traffic camera footage for that corridor."
            )
        return (
            "Based on the current evidence corpus [EVD-IMG-001, EVD-AUD-001, EVD-VID-001], "
            "the multimodal analysis supports a CRITICAL threat classification with a Homicide/Robbery scenario. "
            "Please refine your query with specific evidence elements (e.g., weapon, suspect, timeline) "
            "for more targeted forensic intelligence."
        )
