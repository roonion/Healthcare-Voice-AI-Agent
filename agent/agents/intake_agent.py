from __future__ import annotations

import logging

from livekit.agents import Agent, function_tool, RunContext

from .user_data import UserData
from .triage_agent import TriageAgent  # noqa: F401 — must be available at runtime for get_type_hints()

logger = logging.getLogger("intake-agent")

INTAKE_INSTRUCTIONS = """\
You are a friendly, professional medical intake assistant at a healthcare clinic.
Your role is to collect patient information before their appointment.

Collect the following in a natural conversational flow:
1. Full name and date of birth
2. Chief complaint (why they are calling / visiting today)
3. Symptom details: description, duration, severity (1-10 scale), any triggers
4. Current medications
5. Known allergies (especially drug allergies)
6. Relevant medical history

Guidelines:
- Be warm and empathetic. Use the patient's name once you have it.
- Ask ONE question at a time. Do not overwhelm.
- Confirm critical information by reading it back (allergies, medications).
- If the patient sounds distressed, acknowledge their feelings calmly.
- NEVER provide medical diagnoses or treatment advice.
- If the patient reports an emergency (chest pain, difficulty breathing, severe bleeding),
  immediately say "This sounds like it could be urgent. Let me connect you with our
  triage nurse right away." and transfer to triage.
- Speak in the patient's language if they are not speaking English.
- If the patient mentions a visible skin condition (rash, mole, wound, etc.) and
  the session supports images, offer to analyze a photo with the analyze_skin_photo tool.

When you have collected all required information, summarize what you've gathered,
confirm it with the patient, and transfer to the triage assessment.
"""


class IntakeAgent(Agent):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            instructions=INTAKE_INSTRUCTIONS,
            **kwargs,
        )

    @function_tool()
    async def transfer_to_triage(self, ctx: RunContext[UserData]) -> TriageAgent:
        """Transfer the patient to triage assessment after intake is complete."""
        from .triage_agent import TriageAgent
        import ws_bridge

        logger.info(
            "Transferring to triage — patient=%s complaint=%s",
            ctx.userdata.patient_name,
            ctx.userdata.chief_complaint,
        )
        ws_bridge.broadcast_agent_change("TriageAgent")
        return TriageAgent()

    @function_tool()
    async def record_patient_demographics(
        self,
        ctx: RunContext[UserData],
        full_name: str,
        date_of_birth: str,
        email: str = "",
        address: str = "",
    ) -> str:
        """Record the patient's demographic information."""
        ctx.userdata.patient_name = full_name
        ctx.userdata.date_of_birth = date_of_birth
        ctx.userdata.email = email
        ctx.userdata.address = address
        logger.info("Demographics recorded: %s, DOB=%s", full_name, date_of_birth)
        return f"Recorded demographics for {full_name}."

    @function_tool()
    async def record_chief_complaint(
        self,
        ctx: RunContext[UserData],
        complaint: str,
        symptoms: list[str],
        duration: str = "",
        severity: str = "",
    ) -> str:
        """Record the patient's chief complaint and symptom details."""
        ctx.userdata.chief_complaint = complaint
        ctx.userdata.symptoms = symptoms
        ctx.userdata.symptom_duration = duration
        ctx.userdata.symptom_severity = severity
        logger.info("Chief complaint: %s", complaint)
        return f"Recorded chief complaint: {complaint}."

    @function_tool()
    async def record_medications(
        self, ctx: RunContext[UserData], medications: list[str]
    ) -> str:
        """Record the patient's current medications."""
        ctx.userdata.medications = medications
        logger.info("Medications: %s", medications)
        return f"Recorded {len(medications)} medication(s)."

    @function_tool()
    async def record_allergies(
        self, ctx: RunContext[UserData], allergies: list[str]
    ) -> str:
        """Record the patient's known allergies."""
        ctx.userdata.allergies = allergies
        logger.info("Allergies: %s", allergies)
        return f"Recorded {len(allergies)} allergy/allergies."

    @function_tool()
    async def record_medical_history(
        self, ctx: RunContext[UserData], conditions: list[str]
    ) -> str:
        """Record relevant past medical history."""
        ctx.userdata.medical_history = conditions
        logger.info("Medical history: %s", conditions)
        return f"Recorded {len(conditions)} historical condition(s)."

    @function_tool()
    async def lookup_existing_patient(
        self,
        ctx: RunContext[UserData],
        name: str = "",
        phone: str = "",
        date_of_birth: str = "",
    ) -> str:
        """Search the FHIR server for an existing patient record to pre-fill intake data."""
        from tools.fhir_tools import search_patient

        results = await search_patient(name=name, phone=phone, dob=date_of_birth)
        if not results:
            return "No existing patient records found."

        lines = ["Found existing patient record(s):"]
        for r in results[:3]:
            lines.append(
                f"  - {r['name']} (DOB: {r.get('birthDate', 'N/A')}, "
                f"Phone: {r.get('phone', 'N/A')})"
            )
        return "\n".join(lines)

    @function_tool()
    async def analyze_skin_photo(
        self,
        ctx: RunContext[UserData],
        image_base64: str,
        patient_description: str = "",
    ) -> str:
        """
        Analyze a photo of a skin condition using GPT-4o vision.
        image_base64: base64-encoded JPEG or PNG image data.
        patient_description: what the patient says about the condition.
        Returns structured observations for triage.
        """
        import base64
        from vision.derma_triage import DermaTriageVision

        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception:
            return "Invalid image data. Please provide a valid base64-encoded image."

        vision = DermaTriageVision()
        observation = await vision.analyze_image(image_bytes, patient_description)
        if not observation:
            return "Unable to analyze the image at this time."

        lines = [
            f"Visual Analysis Results:",
            f"  Location: {observation.body_location}",
            f"  Characteristics: {observation.characteristics}",
            f"  Observations: {observation.observations}",
            f"  Visual urgency: {observation.urgency}",
            f"  Suggested follow-up questions:",
        ]
        for q in observation.follow_up_questions:
            lines.append(f"    - {q}")
        return "\n".join(lines)
