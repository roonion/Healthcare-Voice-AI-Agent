"""
Scheduling tools — appointment slot management.

In a production system these would integrate with an EHR scheduling API
(Epic, Athena, etc.). For the demo, they return mock slots.
"""

from __future__ import annotations

from datetime import datetime, timedelta


def get_available_slots(is_urgent: bool = False, count: int = 3) -> list[dict]:
    """Generate available appointment slots."""
    now = datetime.now()
    providers = ["Dr. Sarah Chen", "Dr. James Miller", "Dr. Priya Patel"]
    slots = []

    for i in range(count):
        if is_urgent:
            dt = now + timedelta(hours=2 + i * 3)
            location = "Urgent Care — Suite 200"
        else:
            dt = now + timedelta(days=2 + i, hours=9 + i * 2)
            location = "Primary Care — Suite 100"

        slots.append({
            "id": i + 1,
            "datetime": dt.isoformat(),
            "display": dt.strftime("%A, %B %d at %I:%M %p"),
            "provider": providers[i % len(providers)],
            "location": location,
        })

    return slots
