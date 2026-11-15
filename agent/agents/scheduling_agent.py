from __future__ import annotations

import logging
from datetime import datetime, timedelta

from livekit.agents import Agent, function_tool, RunContext

from .user_data import UserData

logger = logging.getLogger("scheduling-agent")

SCHEDULING_INSTRUCTIONS = """\
You are a friendly clinic scheduling assistant. The patient has completed intake and triage.
Your job is to help them schedule an appropriate appointment.

Process:
1. Briefly confirm the triage outcome (urgent = within 24 hours, routine = next available).
2. Check available appointment slots using the available tools.
3. Offer 2-3 options to the patient.
4. Confirm the selected slot.
5. Provide a summary: date/time, provider name, clinic address, and any preparation instructions.
6. Ask if the patient would like an SMS confirmation.

Keep it brief and efficient — the patient has already spent time on intake and triage.
"""


def _generate_mock_slots(is_urgent: bool) -> list[dict]:
    """Generate plausible appointment slots for demo purposes."""
    now = datetime.now()
    slots = []
    if is_urgent:
        for i in range(3):
            dt = now + timedelta(hours=2 + i * 3)
            slots.append({
                "datetime": dt.strftime("%A, %B %d at %I:%M %p"),
                "provider": ["Dr. Sarah Chen", "Dr. James Miller", "Dr. Priya Patel"][i],
                "location": "Main Campus — Urgent Care, Suite 200",
            })
    else:
        for i in range(3):
            dt = now + timedelta(days=2 + i, hours=9 + i * 2)
            slots.append({
                "datetime": dt.strftime("%A, %B %d at %I:%M %p"),
                "provider": ["Dr. Sarah Chen", "Dr. James Miller", "Dr. Priya Patel"][i],
                "location": "Main Campus — Primary Care, Suite 100",
            })
    return slots


class SchedulingAgent(Agent):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            instructions=SCHEDULING_INSTRUCTIONS,
            **kwargs,
        )

    @function_tool()
    async def get_available_slots(self, ctx: RunContext[UserData]) -> str:
        """Retrieve available appointment slots based on triage severity."""
        is_urgent = ctx.userdata.triage_severity == "urgent"
        slots = _generate_mock_slots(is_urgent)

        lines = [
            f"Available {'urgent care' if is_urgent else 'standard'} appointments:"
        ]
        for i, slot in enumerate(slots, 1):
            lines.append(
                f"  {i}. {slot['datetime']} with {slot['provider']} at {slot['location']}"
            )
        return "\n".join(lines)

    @function_tool()
    async def book_appointment(
        self,
        ctx: RunContext[UserData],
        slot_number: int,
        send_sms: bool = True,
    ) -> str:
        """Book the selected appointment slot (1-3). Optionally send SMS confirmation."""
        is_urgent = ctx.userdata.triage_severity == "urgent"
        slots = _generate_mock_slots(is_urgent)

        if slot_number < 1 or slot_number > len(slots):
            return f"Invalid slot number. Please choose 1–{len(slots)}."

        chosen = slots[slot_number - 1]
        ctx.userdata.scheduled_appointment = (
            f"{chosen['datetime']} with {chosen['provider']} at {chosen['location']}"
        )

        logger.info(
            "Appointment booked for %s: %s",
            ctx.userdata.patient_name,
            ctx.userdata.scheduled_appointment,
        )

        confirmation = (
            f"Appointment confirmed: {chosen['datetime']} with {chosen['provider']} "
            f"at {chosen['location']}."
        )
        if send_sms and ctx.userdata.caller_phone:
            confirmation += f" An SMS confirmation will be sent to {ctx.userdata.caller_phone}."

        return confirmation
