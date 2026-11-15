"""
Multimodal vision module for dermatological triage.

Accepts an image (from camera frame or upload), analyzes it via GPT-4o vision,
and returns structured clinical observations for the triage agent.
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger("derma-vision")

DERMA_PROMPT = """\
You are a medical image analysis assistant supporting a clinical intake agent.
Analyze the provided image of a skin condition and describe what you observe.

You are NOT providing a diagnosis. You are providing structured observations
that will help a clinician during triage.

Provide:
1. Location on the body (if identifiable)
2. Visual characteristics: color, size estimate, texture, borders, pattern
3. Relevant observations: swelling, discharge, symmetry
4. Suggested follow-up questions for the patient
5. Urgency indicator: low / moderate / high (based on visual presentation only)

Be precise and clinical in your language. If the image is unclear or does not
show a medical condition, say so.
"""


class DermaObservation(BaseModel):
    body_location: str = Field(description="Location on the body")
    characteristics: str = Field(description="Visual characteristics observed")
    observations: str = Field(description="Additional clinical observations")
    follow_up_questions: list[str] = Field(
        description="Suggested questions for the patient"
    )
    urgency: str = Field(description="Visual urgency: low, moderate, or high")
    raw_description: str = Field(description="Full textual description")


class DermaTriageVision:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        self._client = AsyncOpenAI(api_key=api_key) if api_key else None
        self._enabled = bool(api_key)

    async def analyze_image(
        self,
        image_bytes: bytes,
        patient_description: str = "",
        media_type: str = "image/jpeg",
    ) -> Optional[DermaObservation]:
        """
        Analyze a skin condition image and return structured observations.

        Args:
            image_bytes: Raw image bytes (JPEG/PNG)
            patient_description: What the patient said about the condition
            media_type: MIME type of the image
        """
        if not self._enabled:
            logger.warning("Vision analysis unavailable — no API key")
            return None

        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        user_content = []
        if patient_description:
            user_content.append({
                "type": "text",
                "text": f"The patient describes this as: {patient_description}",
            })
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{media_type};base64,{b64_image}",
                "detail": "high",
            },
        })

        try:
            response = await self._client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": DERMA_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=1000,
            )

            text = response.choices[0].message.content or ""
            observation = self._parse_observation(text)
            logger.info("Vision analysis complete — urgency=%s", observation.urgency)
            return observation

        except Exception:
            logger.exception("Vision analysis failed")
            return None

    async def analyze_frame(
        self,
        frame_bytes: bytes,
        patient_description: str = "",
    ) -> Optional[DermaObservation]:
        """Analyze a video frame captured from LiveKit (JPEG at 1024x1024)."""
        return await self.analyze_image(
            frame_bytes, patient_description, "image/jpeg"
        )

    def _parse_observation(self, text: str) -> DermaObservation:
        """Parse GPT-4o's free-text response into a structured observation."""
        lines = text.strip().split("\n")

        urgency = "moderate"
        for line in lines:
            lower = line.lower()
            if "urgency" in lower or "urgent" in lower:
                if "high" in lower:
                    urgency = "high"
                elif "low" in lower:
                    urgency = "low"
                break

        questions = []
        in_questions = False
        for line in lines:
            if "follow-up" in line.lower() or "question" in line.lower():
                in_questions = True
                continue
            if in_questions and line.strip().startswith(("-", "•", "*")):
                questions.append(line.strip().lstrip("-•* "))
            elif in_questions and not line.strip():
                in_questions = False

        if not questions:
            questions = [
                "How long have you had this?",
                "Is it itchy, painful, or numb?",
                "Has it changed in size or color recently?",
            ]

        return DermaObservation(
            body_location=self._extract_section(text, "location", "unknown"),
            characteristics=self._extract_section(text, "characteristics", text[:200]),
            observations=self._extract_section(text, "observations", ""),
            follow_up_questions=questions,
            urgency=urgency,
            raw_description=text,
        )

    @staticmethod
    def _extract_section(text: str, keyword: str, default: str) -> str:
        for i, line in enumerate(text.split("\n")):
            if keyword.lower() in line.lower():
                content_parts = [line.split(":", 1)[-1].strip()] if ":" in line else []
                for subsequent in text.split("\n")[i + 1 : i + 4]:
                    if subsequent.strip() and not any(
                        k in subsequent.lower()
                        for k in ["location", "characteristics", "observation",
                                   "follow-up", "urgency"]
                    ):
                        content_parts.append(subsequent.strip())
                    else:
                        break
                if content_parts:
                    return " ".join(content_parts)
        return default
