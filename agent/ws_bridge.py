"""
WebSocket bridge server.

Runs in a daemon thread (started during worker prewarm) and broadcasts events
to connected dashboard clients. All broadcast functions are thread-safe and
can be called from any thread/event loop.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from websockets.server import serve, WebSocketServerProtocol

logger = logging.getLogger("ws-bridge")

_clients: set[WebSocketServerProtocol] = set()
_loop: asyncio.AbstractEventLoop | None = None
_started = False


async def _handler(ws: WebSocketServerProtocol) -> None:
    _clients.add(ws)
    logger.info("Dashboard client connected (%d total)", len(_clients))
    try:
        async for _ in ws:
            pass
    finally:
        _clients.discard(ws)
        logger.info("Dashboard client disconnected (%d total)", len(_clients))


async def _send_all(payload: str) -> None:
    if not _clients:
        return
    dead: list[WebSocketServerProtocol] = []
    for ws in _clients:
        try:
            await ws.send(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _clients.discard(ws)


def _fire(event: dict[str, Any]) -> None:
    """Thread-safe broadcast: schedules the send on the WS bridge's own loop."""
    if _loop is None:
        logger.warning("WS bridge not started, dropping %s", event.get("type"))
        return
    if not _clients:
        return
    payload = json.dumps(event)
    logger.debug("Broadcasting %s to %d client(s)", event.get("type"), len(_clients))
    asyncio.run_coroutine_threadsafe(_send_all(payload), _loop)


# --- Public broadcast API (all synchronous, all thread-safe) ---


def broadcast_transcript(role: str, text: str, timestamp: float) -> None:
    _fire({
        "type": "transcript_update",
        "role": role,
        "text": text,
        "timestamp": timestamp,
    })


def broadcast_agent_change(agent_name: str) -> None:
    _fire({"type": "agent_change", "agent": agent_name})


def broadcast_call_start(caller_phone: str) -> None:
    _fire({"type": "call_start", "caller_phone": caller_phone})


def broadcast_call_end(duration_seconds: float) -> None:
    _fire({"type": "call_end", "duration_seconds": duration_seconds})


def broadcast_metrics(
    stt_ms: float, llm_ms: float, tts_ms: float, total_ms: float
) -> None:
    _fire({
        "type": "call_metrics",
        "stt_ms": round(stt_ms),
        "llm_ms": round(llm_ms),
        "tts_ms": round(tts_ms),
        "total_ms": round(total_ms),
    })


def broadcast_fhir_update(bundle: dict[str, Any]) -> None:
    _fire({"type": "fhir_update", "bundle": bundle})


def broadcast_fhir_finalized(bundle_id: str) -> None:
    _fire({"type": "fhir_finalized", "bundle_id": bundle_id})


def broadcast_emotion(
    timestamp: float,
    scores: dict[str, float],
    distress_composite: float,
) -> None:
    _fire({
        "type": "emotion_update",
        "timestamp": timestamp,
        "scores": scores,
        "distress_composite": round(distress_composite, 3),
    })


async def start_server(host: str = "0.0.0.0", port: int = 8765) -> None:
    global _loop
    _loop = asyncio.get_running_loop()
    async with serve(_handler, host, port):
        logger.info("WS bridge listening on ws://%s:%d", host, port)
        await asyncio.Future()


def ensure_started(host: str = "0.0.0.0", port: int = 8765) -> None:
    """Start the WS bridge in a daemon thread if not already running."""
    global _started
    if _started:
        return
    _started = True

    import threading, time  # noqa: E401

    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_server(host, port))

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    time.sleep(0.5)
