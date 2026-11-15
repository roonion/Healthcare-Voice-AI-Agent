"""
FHIR R4 resource models as Pydantic schemas.

These are simplified FHIR-compatible models designed for streaming construction
via Instructor's Partial[T]. The final output can be converted to full FHIR R4
Transaction Bundles for POST to HAPI FHIR.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TriageSeverity(str, Enum):
    EMERGENT = "emergent"
    URGENT = "urgent"
    ROUTINE = "routine"


class PatientResource(BaseModel):
    """FHIR Patient resource — demographics."""

    full_name: str = Field(description="Patient's full legal name")
    date_of_birth: Optional[str] = Field(
        default=None, description="Date of birth (YYYY-MM-DD)"
    )
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    email: Optional[str] = Field(default=None, description="Contact email address")
    address: Optional[str] = Field(default=None, description="Full mailing address")
    language: Optional[str] = Field(
        default="en", description="Preferred language (ISO 639-1)"
    )


class ConditionResource(BaseModel):
    """FHIR Condition resource — a clinical condition or diagnosis."""

    description: str = Field(description="Clinical description of the condition")
    severity: Optional[str] = Field(
        default=None, description="Severity: mild, moderate, severe"
    )
    onset: Optional[str] = Field(
        default=None, description="When the condition started"
    )
    body_site: Optional[str] = Field(
        default=None, description="Affected body area"
    )


class AllergyResource(BaseModel):
    """FHIR AllergyIntolerance resource."""

    substance: str = Field(description="Allergen name")
    reaction: Optional[str] = Field(
        default=None, description="Known reaction type"
    )
    severity: Optional[str] = Field(
        default=None, description="Reaction severity: mild, moderate, severe"
    )


class MedicationResource(BaseModel):
    """FHIR MedicationStatement resource."""

    name: str = Field(description="Medication name")
    dosage: Optional[str] = Field(default=None, description="Dosage and frequency")
    status: str = Field(default="active", description="active, completed, stopped")


class TriageResource(BaseModel):
    """Triage assessment (maps to FHIR RiskAssessment)."""

    severity: Optional[TriageSeverity] = Field(
        default=None, description="Triage severity level"
    )
    reasoning: Optional[str] = Field(
        default=None, description="Clinical reasoning for triage decision"
    )
    emotion_summary: Optional[str] = Field(
        default=None,
        description="Summary of patient's emotional state during call",
    )


class IntakeBundle(BaseModel):
    """
    Complete intake bundle — the top-level model streamed via Instructor.

    Maps to a FHIR R4 Transaction Bundle containing all resources
    created during the intake call.
    """

    patient: Optional[PatientResource] = None
    chief_complaint: Optional[str] = Field(
        default=None, description="Primary reason for the visit"
    )
    conditions: list[ConditionResource] = Field(default_factory=list)
    allergies: list[AllergyResource] = Field(default_factory=list)
    medications: list[MedicationResource] = Field(default_factory=list)
    triage_assessment: Optional[TriageResource] = None
    appointment: Optional[str] = Field(
        default=None, description="Scheduled appointment details"
    )

    def to_fhir_transaction_bundle(self) -> dict:
        """Convert to a FHIR R4 Transaction Bundle for POST to HAPI FHIR."""
        entries = []

        if self.patient:
            name_parts = self.patient.full_name.split(" ", 1)
            entries.append({
                "resource": {
                    "resourceType": "Patient",
                    "name": [{
                        "family": name_parts[-1] if len(name_parts) > 1 else name_parts[0],
                        "given": [name_parts[0]] if len(name_parts) > 1 else [],
                    }],
                    "birthDate": self.patient.date_of_birth,
                    "telecom": [
                        t
                        for t in [
                            {"system": "phone", "value": self.patient.phone}
                            if self.patient.phone
                            else None,
                            {"system": "email", "value": self.patient.email}
                            if self.patient.email
                            else None,
                        ]
                        if t
                    ],
                    "communication": [
                        {"language": {"text": self.patient.language or "en"}}
                    ],
                },
                "request": {"method": "POST", "url": "Patient"},
            })

        for condition in self.conditions:
            entries.append({
                "resource": {
                    "resourceType": "Condition",
                    "code": {"text": condition.description},
                    "severity": {"text": condition.severity}
                    if condition.severity
                    else None,
                    "onsetString": condition.onset,
                    "bodySite": [{"text": condition.body_site}]
                    if condition.body_site
                    else None,
                },
                "request": {"method": "POST", "url": "Condition"},
            })

        for allergy in self.allergies:
            entries.append({
                "resource": {
                    "resourceType": "AllergyIntolerance",
                    "code": {"text": allergy.substance},
                    "reaction": [{"description": allergy.reaction}]
                    if allergy.reaction
                    else None,
                },
                "request": {"method": "POST", "url": "AllergyIntolerance"},
            })

        for med in self.medications:
            entries.append({
                "resource": {
                    "resourceType": "MedicationStatement",
                    "medicationCodeableConcept": {"text": med.name},
                    "dosage": [{"text": med.dosage}] if med.dosage else None,
                    "status": med.status,
                },
                "request": {"method": "POST", "url": "MedicationStatement"},
            })

        if self.triage_assessment and self.triage_assessment.severity:
            entries.append({
                "resource": {
                    "resourceType": "RiskAssessment",
                    "status": "final",
                    "prediction": [{
                        "outcome": {
                            "text": (
                                f"Triage: {self.triage_assessment.severity.value} — "
                                f"{self.triage_assessment.reasoning or 'N/A'}"
                            )
                        },
                    }],
                    "note": [{"text": self.triage_assessment.emotion_summary}]
                    if self.triage_assessment.emotion_summary
                    else None,
                },
                "request": {"method": "POST", "url": "RiskAssessment"},
            })

        # Strip None values from resources
        cleaned = []
        for entry in entries:
            resource = {k: v for k, v in entry["resource"].items() if v is not None}
            cleaned.append({"resource": resource, "request": entry["request"]})

        return {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": cleaned,
        }
