from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EmotionSnapshot:
    timestamp: float
    scores: dict[str, float]

    @property
    def distress_composite(self) -> float:
        weights = {"fear": 0.3, "pain": 0.25, "distress": 0.25, "anxiety": 0.2}
        return sum(self.scores.get(k, 0.0) * w for k, w in weights.items())


@dataclass
class UserData:
    """Shared patient state persisted across all agents in a single call."""

    caller_phone: str = ""
    patient_name: str = ""
    date_of_birth: str = ""
    email: str = ""
    address: str = ""

    chief_complaint: str = ""
    symptoms: list[str] = field(default_factory=list)
    symptom_duration: str = ""
    symptom_severity: str = ""

    allergies: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    medical_history: list[str] = field(default_factory=list)

    triage_severity: str = ""  # emergent / urgent / routine
    triage_reasoning: str = ""

    emotion_timeline: list[EmotionSnapshot] = field(default_factory=list)
    language_detected: str = "en"

    scheduled_appointment: str = ""
    fhir_bundle_id: str = ""

    call_start: datetime = field(default_factory=datetime.now)
    extra: dict[str, Any] = field(default_factory=dict)

    def latest_emotion(self) -> EmotionSnapshot | None:
        return self.emotion_timeline[-1] if self.emotion_timeline else None

    def is_distressed(self, threshold: float = 0.6, min_consecutive: int = 2) -> bool:
        if len(self.emotion_timeline) < min_consecutive:
            return False
        recent = self.emotion_timeline[-min_consecutive:]
        return all(s.distress_composite >= threshold for s in recent)

    def to_memory_summary(self) -> str:
        parts = [f"Patient: {self.patient_name}"] if self.patient_name else []
        if self.chief_complaint:
            parts.append(f"Chief complaint: {self.chief_complaint}")
        if self.symptoms:
            parts.append(f"Symptoms: {', '.join(self.symptoms)}")
        if self.allergies:
            parts.append(f"Allergies: {', '.join(self.allergies)}")
        if self.medications:
            parts.append(f"Medications: {', '.join(self.medications)}")
        if self.triage_severity:
            parts.append(f"Triage: {self.triage_severity}")
        if self.scheduled_appointment:
            parts.append(f"Appointment: {self.scheduled_appointment}")
        return "; ".join(parts)
