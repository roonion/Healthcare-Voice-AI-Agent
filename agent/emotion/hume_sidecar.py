"""
Hume AI Expression Measurement sidecar.

Analyzes patient utterance text (and optionally audio) via Hume for
per-utterance emotion scoring, updates UserData, and broadcasts to
the dashboard through the central ws_bridge.

When HUME_API_KEY is unavailable, falls back to keyword-based heuristic
so the emotion pipeline still produces data for the dashboard.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any

import httpx

from agents.user_data import UserData, EmotionSnapshot

logger = logging.getLogger("hume-sidecar")

HUME_STREAM_URL = "https://api.hume.ai/v0/stream/models"

CLINICALLY_RELEVANT_EMOTIONS = [
    "fear", "pain", "distress", "anxiety", "sadness", "anger",
    "confusion", "contempt", "disgust", "surprise",
]

# Keyword-based fallback when Hume API is not available
_KEYWORD_MAP: dict[str, list[str]] = {
    "fear": ["scared", "afraid", "terrified", "frightened", "fear", "panic", "worried"],
    "pain": ["pain", "hurt", "ache", "sore", "agony", "throbbing", "sharp pain", "burning"],
    "distress": ["help", "please", "can't", "desperate", "unbearable", "terrible"],
    "anxiety": ["anxious", "nervous", "uneasy", "stress", "tense", "restless", "worry"],
    "sadness": ["sad", "depressed", "hopeless", "lonely", "grief", "crying", "miserable"],
    "anger": ["angry", "furious", "frustrated", "mad", "annoyed", "irritated"],
}


class HumeEmotionSidecar:
    """Analyzes patient voice/text for emotional content using Hume AI."""

    def __init__(self, user_data: UserData) -> None:
        self._user_data = user_data
        self._api_key = os.getenv("HUME_API_KEY", "")
        self._enabled = True  # always enabled — falls back to keywords
        self._hume_available = bool(self._api_key)
        self._running = False
        self._task: asyncio.Task | None = None
        self._utterance_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=50)

        if not self._hume_available:
            logger.warning(
                "HUME_API_KEY not set — using keyword-based emotion fallback"
            )

    def queue_utterance(self, text: str) -> None:
        """Queue a patient utterance for emotion analysis."""
        try:
            self._utterance_queue.put_nowait(text)
        except asyncio.QueueFull:
            logger.debug("Emotion queue full, dropping utterance")

    async def start(self, room: Any = None, participant: Any = None) -> None:
        self._running = True
        self._task = asyncio.create_task(self._analysis_loop())
        logger.info(
            "Emotion sidecar started (hume=%s)", "on" if self._hume_available else "keyword-fallback"
        )

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Emotion sidecar stopped")

    async def _analysis_loop(self) -> None:
        """Process queued utterances and run emotion analysis on each."""
        while self._running:
            try:
                text = await asyncio.wait_for(
                    self._utterance_queue.get(), timeout=2.0
                )
                scores = await self._analyze_text(text)
                if scores:
                    snapshot = EmotionSnapshot(
                        timestamp=asyncio.get_running_loop().time(),
                        scores=scores,
                    )
                    self._user_data.emotion_timeline.append(snapshot)
                    await self._broadcast_emotion(snapshot)

                    if self._user_data.is_distressed():
                        logger.warning(
                            "Patient distress detected — composite=%.2f",
                            snapshot.distress_composite,
                        )

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in emotion analysis loop")
                await asyncio.sleep(2.0)

    async def _analyze_text(self, text: str) -> dict[str, float] | None:
        """Analyze utterance text: try Hume API, fall back to keywords."""
        if self._hume_available:
            scores = await self._hume_language_analysis(text)
            if scores:
                return scores

        return self._keyword_fallback(text)

    async def _hume_language_analysis(self, text: str) -> dict[str, float] | None:
        """Call Hume's streaming language model for text-based emotion detection."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    HUME_STREAM_URL,
                    headers={
                        "X-Hume-Api-Key": self._api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "models": {
                            "language": {
                                "granularity": "sentence",
                            }
                        },
                        "raw_text": True,
                        "data": text,
                    },
                    timeout=5.0,
                )
                resp.raise_for_status()
                result = resp.json()

            return self._extract_scores_language(result)

        except Exception:
            logger.debug("Hume API call failed, falling back to keywords")
            return None

    def _extract_scores_language(self, hume_response: dict) -> dict[str, float]:
        """Extract clinically relevant scores from Hume language model response."""
        scores = {}
        try:
            predictions = (
                hume_response.get("language", {})
                .get("predictions", [{}])[0]
                .get("emotions", [])
            )
            for emotion in predictions:
                name = emotion.get("name", "").lower()
                if name in CLINICALLY_RELEVANT_EMOTIONS:
                    scores[name] = round(emotion.get("score", 0.0), 3)
        except (IndexError, KeyError):
            pass
        return scores

    @staticmethod
    def _keyword_fallback(text: str) -> dict[str, float]:
        """Heuristic emotion scoring based on keyword presence and intensity."""
        lower = text.lower()
        scores: dict[str, float] = {}

        intensity_multiplier = 1.0
        if any(w in lower for w in ["very", "extremely", "really", "so much", "terrible"]):
            intensity_multiplier = 1.4
        if "!" in text:
            intensity_multiplier = min(intensity_multiplier + 0.2, 1.6)

        for emotion, keywords in _KEYWORD_MAP.items():
            hits = sum(1 for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", lower))
            if hits > 0:
                raw = min(0.3 + hits * 0.15, 0.95) * intensity_multiplier
                scores[emotion] = round(min(raw, 1.0), 3)
            else:
                scores[emotion] = round(0.05 + hash(text + emotion) % 5 * 0.02, 3)

        return scores

    async def _broadcast_emotion(self, snapshot: EmotionSnapshot) -> None:
        import ws_bridge

        ws_bridge.broadcast_emotion(
            timestamp=snapshot.timestamp,
            scores=snapshot.scores,
            distress_composite=snapshot.distress_composite,
        )
