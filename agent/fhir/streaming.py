"""
Streaming FHIR construction via Instructor's Partial[T].

Listens for transcript updates, pipes them through Instructor to produce
a progressively filling IntakeBundle, and broadcasts partial JSON to
the React dashboard via the central ws_bridge.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx
import instructor
from openai import AsyncOpenAI

from .models import IntakeBundle
from agents.user_data import UserData

logger = logging.getLogger("fhir-streaming")


class FHIRStreamBroadcaster:
    """
    Accumulates transcript text and periodically extracts structured FHIR data.

    Each extraction produces a streaming IntakeBundle via Instructor,
    broadcasting partial results to the dashboard through ws_bridge.
    """

    def __init__(self, user_data: UserData) -> None:
        self._user_data = user_data
        self._transcript_buffer: list[str] = []
        self._running = False
        self._task: asyncio.Task | None = None
        self._current_bundle: IntakeBundle | None = None
        self._fhir_server_url = os.getenv(
            "FHIR_SERVER_URL", "http://localhost:8080/fhir"
        )

        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            self._client = instructor.from_openai(AsyncOpenAI(api_key=api_key))
            self._enabled = True
        else:
            self._client = None
            self._enabled = False
            logger.warning("OPENAI_API_KEY not set — FHIR streaming disabled")

    def add_transcript(self, text: str, role: str = "patient") -> None:
        self._transcript_buffer.append(f"[{role}] {text}")

    async def start(self) -> None:
        if not self._enabled:
            return
        self._running = True
        self._task = asyncio.create_task(self._extraction_loop())
        logger.info("FHIR stream broadcaster started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _extraction_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(5.0)

                if not self._transcript_buffer:
                    continue

                transcript = "\n".join(self._transcript_buffer)
                await self._extract_and_stream(transcript)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in FHIR extraction loop")
                await asyncio.sleep(10.0)

    async def _extract_and_stream(self, transcript: str) -> None:
        import ws_bridge  # noqa: F811

        emotion_context = ""
        latest = self._user_data.latest_emotion()
        if latest:
            top_emotions = sorted(
                latest.scores.items(), key=lambda x: x[1], reverse=True
            )[:3]
            emotion_context = (
                "Patient emotional state: "
                + ", ".join(f"{k}: {v:.2f}" for k, v in top_emotions)
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "Extract structured medical intake data from the following "
                    "patient-agent conversation transcript. Produce a complete "
                    "IntakeBundle with all information gathered so far. "
                    "Only include information explicitly stated by the patient. "
                    f"{emotion_context}"
                ),
            },
            {"role": "user", "content": transcript},
        ]

        try:
            stream = self._client.chat.completions.create_partial(
                model="gpt-4.1-mini",
                response_model=IntakeBundle,
                messages=messages,
                stream=True,
            )

            async for partial_bundle in stream:
                self._current_bundle = partial_bundle
                ws_bridge.broadcast_fhir_update(
                    partial_bundle.model_dump(exclude_unset=True)
                )

        except Exception:
            logger.exception("Instructor extraction failed")

    async def finalize(self) -> None:
        import ws_bridge  # noqa: F811

        if not self._enabled:
            return

        if self._transcript_buffer:
            transcript = "\n".join(self._transcript_buffer)
            await self._extract_and_stream(transcript)

        if not self._current_bundle:
            logger.warning("No FHIR bundle to finalize")
            return

        # Enrich with triage and appointment data from UserData
        if self._current_bundle.triage_assessment is None:
            from .models import TriageResource, TriageSeverity

            if self._user_data.triage_severity:
                self._current_bundle.triage_assessment = TriageResource(
                    severity=TriageSeverity(self._user_data.triage_severity),
                    reasoning=self._user_data.triage_reasoning,
                )

        if self._user_data.scheduled_appointment:
            self._current_bundle.appointment = self._user_data.scheduled_appointment

        transaction_bundle = self._current_bundle.to_fhir_transaction_bundle()

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._fhir_server_url,
                    json=transaction_bundle,
                    headers={"Content-Type": "application/fhir+json"},
                    timeout=15.0,
                )
                if resp.status_code in (200, 201):
                    logger.info("FHIR bundle posted successfully")
                    self._user_data.fhir_bundle_id = resp.json().get("id", "")
                    ws_bridge.broadcast_fhir_finalized(
                        self._user_data.fhir_bundle_id
                    )
                else:
                    logger.error(
                        "FHIR POST failed: %d — %s",
                        resp.status_code,
                        resp.text[:200],
                    )
        except Exception:
            logger.exception("Failed to POST FHIR bundle")
