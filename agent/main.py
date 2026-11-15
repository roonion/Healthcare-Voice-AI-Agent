"""
Healthcare Voice AI Agent — Main Entrypoint

Supports two pipeline modes via PIPELINE_MODE env var:
  - "cascade"  : Deepgram STT → GPT-4.1 → ElevenLabs TTS (best-of-breed)
  - "realtime" : OpenAI Realtime API (speech-to-speech, lowest latency)
"""

from __future__ import annotations

import logging
import os
import time


from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions
from livekit.agents.voice import AgentSession

from livekit.plugins import deepgram, openai, elevenlabs  # noqa: F401

from agents import IntakeAgent, UserData
from memory.patient_memory import PatientMemory
from emotion.hume_sidecar import HumeEmotionSidecar
from fhir.streaming import FHIRStreamBroadcaster
from guardrails.output_validators import check_crisis_input, validate_output
import ws_bridge

from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

logger = logging.getLogger("healthcare-agent")
logging.basicConfig(level=logging.INFO)
logging.getLogger("websockets").setLevel(logging.WARNING)


PIPELINE_MODE = os.getenv("PIPELINE_MODE", "cascade")  # noqa: E501


TURN_HANDLING = {
    "interruption": {
        "min_duration": 0.7,
        "min_words": 1,
        "resume_false_interruption": True,
        "false_interruption_timeout": 2.5,
    },
}


def _build_cascade_session(user_data: UserData) -> AgentSession:
    tts_provider = os.getenv("TTS_PROVIDER", "openai")
    if tts_provider == "elevenlabs":
        tts = elevenlabs.TTS(
            model="eleven_flash_v2_5",
            voice_id="pNInz6obpgDQGcFmaJgB",
        )
    else:
        tts = openai.TTS(voice="nova")

    return AgentSession(
        stt=deepgram.STT(model="nova-3-medical"),
        llm="gpt-4.1",
        tts=tts,
        turn_handling=TURN_HANDLING,
        userdata=user_data,
    )


def _build_realtime_session(user_data: UserData) -> AgentSession:
    model = openai.realtime.RealtimeModel(
        voice="ash",
        turn_detection="server_vad",
        modalities=["text", "audio"],
    )
    return AgentSession(
        stt=model,
        llm=model,
        tts=model,
        turn_handling=TURN_HANDLING,
        userdata=user_data,
    )


def prewarm(proc: JobProcess) -> None:
    pass


async def entrypoint(ctx: JobContext) -> None:
    ws_bridge.ensure_started()

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()

    caller_phone = ""
    sip_attrs = participant.attributes
    if sip_attrs:
        caller_phone = sip_attrs.get("sip.callerNumber", "")
    if not caller_phone:
        caller_phone = participant.identity or "unknown"

    user_data = UserData(caller_phone=caller_phone)
    logger.info("New call from %s — pipeline=%s", caller_phone, PIPELINE_MODE)

    memory = PatientMemory()
    prior_context = await memory.recall(caller_phone)
    memory_prompt = ""
    if prior_context:
        memory_prompt = (
            f"\n\n[RETURNING PATIENT CONTEXT]\n{prior_context}\n"
            "Greet them warmly by name and reference their previous visits.\n"
        )

    intake_agent = IntakeAgent()
    if memory_prompt:
        intake_agent.instructions += memory_prompt

    if PIPELINE_MODE == "realtime":
        session = _build_realtime_session(user_data)
    else:
        session = _build_cascade_session(user_data)

    emotion_sidecar = HumeEmotionSidecar(user_data=user_data)
    fhir_broadcaster = FHIRStreamBroadcaster(user_data=user_data)

    # --- Wire session events to subsystems ---

    @session.on("user_input_transcribed")
    def on_user_input(ev) -> None:
        text = getattr(ev, "transcript", "") or ""
        if not text.strip() or not getattr(ev, "is_final", True):
            return

        logger.debug("Patient: %s", text[:80])
        ws_bridge.broadcast_transcript("patient", text, time.time())
        fhir_broadcaster.add_transcript(text, "patient")
        emotion_sidecar.queue_utterance(text)

        if check_crisis_input(text):
            logger.critical("CRISIS KEYWORDS detected: %s", text[:100])

    @session.on("conversation_item_added")
    def on_conversation_item(ev) -> None:
        item = getattr(ev, "item", None)
        if item is None:
            return
        role = getattr(item, "role", "")
        if role != "assistant":
            return
        content = getattr(item, "content", "")
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        text = str(content).strip()
        if not text:
            return
        logger.debug("Agent: %s", text[:80])

        result = validate_output(text)
        if not result.passed:
            logger.warning("Output validation flags: %s", result.flags)

        ws_bridge.broadcast_transcript("agent", result.sanitized_text, time.time())
        fhir_broadcaster.add_transcript(result.sanitized_text, "agent")

    @session.on("metrics_collected")
    def on_metrics(ev) -> None:
        try:
            metrics = getattr(ev, "metrics", ev)
            stt_dur = getattr(metrics, "stt_duration", 0) or 0
            llm_dur = getattr(metrics, "llm_duration", 0) or 0
            tts_dur = getattr(metrics, "tts_duration", 0) or 0
            total = stt_dur + llm_dur + tts_dur
            ws_bridge.broadcast_metrics(
                stt_ms=stt_dur * 1000,
                llm_ms=llm_dur * 1000,
                tts_ms=tts_dur * 1000,
                total_ms=total * 1000,
            )
        except Exception:
            logger.debug("Metrics event structure not as expected: %s", type(ev))

    await emotion_sidecar.start()
    await fhir_broadcaster.start()

    ws_bridge.broadcast_call_start(caller_phone)
    ws_bridge.broadcast_agent_change("IntakeAgent")

    await session.start(intake_agent, room=ctx.room)

    @ctx.add_shutdown_callback
    async def on_shutdown():
        call_duration = time.time() - user_data.call_start.timestamp()
        await emotion_sidecar.stop()
        await fhir_broadcaster.finalize()
        await memory.store(caller_phone, user_data.to_memory_summary())
        ws_bridge.broadcast_call_end(call_duration)
        logger.info("Session ended for %s — memory stored", caller_phone)


if __name__ == "__main__":
    agents.cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            num_idle_processes=1,
        )
    )
