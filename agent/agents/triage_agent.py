from __future__ import annotations

import logging

from livekit.agents import Agent, function_tool, RunContext

from .user_data import UserData
from .scheduling_agent import SchedulingAgent  # noqa: F401

logger = logging.getLogger("triage-agent")

TRIAGE_INSTRUCTIONS = """\
You are a clinical triage assistant. You have just received a patient's intake information.
Your job is to assess the urgency of their situation and assign a triage level.

Triage levels:
- EMERGENT: Life-threatening, needs immediate emergency care (call 911)
  Examples: chest pain, difficulty breathing, severe bleeding, stroke symptoms
- URGENT: Needs to be seen within 24 hours
  Examples: high fever, moderate pain, worsening symptoms, possible fractures
- ROUTINE: Can be scheduled for a normal appointment
  Examples: mild symptoms, chronic condition follow-up, preventive care

Process:
1. Review the intake information provided in the conversation context.
2. Ask 2-3 targeted follow-up questions to clarify severity.
3. Consider the patient's emotional state if emotion data is available.
4. Assign a triage level with clear reasoning.
5. For EMERGENT: instruct the patient to call 911 or go to the nearest ER immediately.
6. For URGENT/ROUTINE: transfer to scheduling to book an appointment.

IMPORTANT:
- You are NOT diagnosing. You are assessing urgency of the need to see a provider.
- If the patient shows signs of distress (emotional data indicates fear/pain > 0.6),
  use a calmer tone and consider upgrading urgency.
- If suicidal ideation is detected, activate crisis protocol: express care,
  provide 988 Suicide & Crisis Lifeline number, stay on the line, and transfer to a human.
"""


class TriageAgent(Agent):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            instructions=TRIAGE_INSTRUCTIONS,
            **kwargs,
        )

    @function_tool()
    async def assign_triage_level(
        self,
        ctx: RunContext[UserData],
        level: str,
        reasoning: str,
    ) -> str:
        """Assign a triage severity level. level must be 'emergent', 'urgent', or 'routine'."""
        level_lower = level.lower().strip()
        if level_lower not in ("emergent", "urgent", "routine"):
            return f"Invalid triage level '{level}'. Must be emergent, urgent, or routine."

        if ctx.userdata.is_distressed() and level_lower == "routine":
            level_lower = "urgent"
            reasoning += " [Upgraded from routine due to sustained patient distress signals.]"
            logger.info("Triage auto-upgraded to urgent due to distress")

        ctx.userdata.triage_severity = level_lower
        ctx.userdata.triage_reasoning = reasoning
        logger.info("Triage assigned: %s — %s", level_lower, reasoning)
        return f"Triage level set to {level_lower.upper()}."

    @function_tool()
    async def transfer_to_scheduling(
        self, ctx: RunContext[UserData]
    ) -> SchedulingAgent | str:
        """Transfer to scheduling after triage is complete (for urgent or routine cases)."""
        from .scheduling_agent import SchedulingAgent
        import ws_bridge

        if ctx.userdata.triage_severity == "emergent":
            logger.warning("Scheduling requested for emergent patient — denied")
            return (
                "Cannot schedule — this is an emergent case. Instruct the patient "
                "to call 911 or go to the nearest emergency room immediately."
            )

        logger.info(
            "Transferring to scheduling — severity=%s", ctx.userdata.triage_severity
        )
        ws_bridge.broadcast_agent_change("SchedulingAgent")
        return SchedulingAgent()

    @function_tool()
    async def activate_crisis_protocol(self, ctx: RunContext[UserData]) -> str:
        """Activate crisis protocol for suicidal ideation or self-harm risk."""
        ctx.userdata.triage_severity = "emergent"
        ctx.userdata.triage_reasoning = "Crisis protocol activated — suicidal ideation detected."
        logger.critical(
            "CRISIS PROTOCOL ACTIVATED for patient %s", ctx.userdata.patient_name
        )
        return (
            "Crisis protocol activated. Provide the patient with the 988 Suicide & Crisis "
            "Lifeline number (call or text 988). Stay on the line. A warm transfer to a "
            "human counselor will be initiated."
        )
