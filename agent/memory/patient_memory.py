"""
Patient memory layer backed by Mem0.

Maps caller phone number → patient profile.
Before each call: retrieve relevant memories and inject into system prompt.
After each call: store new facts for long-term recall.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("patient-memory")


class PatientMemory:
    """Thin wrapper around Mem0 for patient-scoped memory."""

    def __init__(self) -> None:
        api_key = os.getenv("MEM0_API_KEY", "")
        if api_key:
            try:
                from mem0 import MemoryClient

                self._memory = MemoryClient(api_key=api_key)
                self._enabled = True
            except Exception:
                logger.exception("Failed to initialize Mem0 — patient memory disabled")
                self._memory = None
                self._enabled = False
        else:
            self._memory = None
            self._enabled = False
            logger.warning("MEM0_API_KEY not set — patient memory disabled")

    async def recall(self, caller_phone: str) -> str | None:
        """Retrieve relevant memories for a returning patient."""
        if not self._enabled:
            return None

        try:
            results = self._memory.search(
                query="patient information, allergies, medications, recent visits",
                user_id=caller_phone,
                limit=10,
            )
            if not results:
                return None

            memories = []
            for r in results:
                text = r.get("memory", "") or r.get("text", "")
                if text:
                    memories.append(text)

            if not memories:
                return None

            combined = "\n".join(f"- {m}" for m in memories)
            logger.info("Retrieved %d memories for %s", len(memories), caller_phone)
            return combined

        except Exception:
            logger.exception("Failed to recall memories for %s", caller_phone)
            return None

    async def store(self, caller_phone: str, summary: str) -> None:
        """Store call summary as new memories for the patient."""
        if not self._enabled or not summary:
            return

        try:
            self._memory.add(
                messages=[{"role": "assistant", "content": summary}],
                user_id=caller_phone,
            )
            logger.info("Stored memory for %s: %s", caller_phone, summary[:100])
        except Exception:
            logger.exception("Failed to store memories for %s", caller_phone)
