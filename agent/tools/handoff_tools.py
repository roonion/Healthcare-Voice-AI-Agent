"""
Agent handoff tools — enable mid-call transfers between agents.

These are registered as function tools on the agents that need them.
The actual handoff implementations are defined on each agent class.
This module provides shared utilities for handoff operations.
"""

from __future__ import annotations

import logging
from agents.user_data import UserData

logger = logging.getLogger("handoff-tools")


def prepare_handoff_context(user_data: UserData, target: str) -> str:
    """Build a context summary for the receiving agent."""
    parts = [f"--- Handoff to {target} ---"]

    if user_data.patient_name:
        parts.append(f"Patient: {user_data.patient_name}")
    if user_data.date_of_birth:
        parts.append(f"DOB: {user_data.date_of_birth}")
    if user_data.chief_complaint:
        parts.append(f"Chief complaint: {user_data.chief_complaint}")
    if user_data.symptoms:
        parts.append(f"Symptoms: {', '.join(user_data.symptoms)}")
    if user_data.symptom_severity:
        parts.append(f"Severity (self-reported): {user_data.symptom_severity}/10")
    if user_data.allergies:
        parts.append(f"Allergies: {', '.join(user_data.allergies)}")
    if user_data.medications:
        parts.append(f"Medications: {', '.join(user_data.medications)}")
    if user_data.triage_severity:
        parts.append(f"Triage: {user_data.triage_severity}")

    latest_emotion = user_data.latest_emotion()
    if latest_emotion:
        top = sorted(latest_emotion.scores.items(), key=lambda x: x[1], reverse=True)[:3]
        parts.append(
            "Emotional state: " + ", ".join(f"{k}: {v:.2f}" for k, v in top)
        )

    return "\n".join(parts)
