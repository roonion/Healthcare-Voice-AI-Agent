# Healthcare Voice AI Agent

A production-grade voice AI agent for clinical patient intake, built with LiveKit Agents v1.5, demonstrating phone-based intake, emotion-aware triage, streaming FHIR construction, multimodal vision, and persistent patient memory.

## Architecture

```
                   ┌─────────────────┐
                   │   Twilio SIP    │
                   │  Phone Number   │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │  LiveKit Cloud  │
                   │   (SIP Trunk)   │
                   └────────┬────────┘
                            │
              ┌─────────────▼─────────────┐
              │     LiveKit Agents v1.5   │
              │                           │
              │  ┌─────────────────────┐  │
              │  │   Pipeline Toggle   │  │
              │  │                     │  │
              │  │ CASCADE:            │  │
              │  │  Deepgram Nova-3    │  │
              │  │  → GPT-4.1         │  │
              │  │  → ElevenLabs v2.5  │  │
              │  │                     │  │
              │  │ REALTIME:           │  │
              │  │  OpenAI Realtime    │  │
              │  │  (speech-to-speech) │  │
              │  └─────────────────────┘  │
              │                           │
              │  ┌─────────────────────┐  │
              │  │  Multi-Agent Flow   │  │
              │  │                     │  │
              │  │  IntakeAgent        │  │
              │  │    → TriageAgent    │  │
              │  │    → SchedulingAgent│  │
              │  └─────────────────────┘  │
              │                           │
              │  ┌──────┐ ┌──────────┐   │
              │  │ Hume │ │Instructor│   │
              │  │Emotion│ │ FHIR    │   │
              │  │Sidecar│ │Streaming│   │
              │  └──┬───┘ └────┬─────┘   │
              └─────┼──────────┼─────────┘
                    │          │
           ┌────────▼──────────▼────────┐
           │   WebSocket Bridge (:8765) │
           └────────────┬───────────────┘
                        │
           ┌────────────▼───────────────┐
           │   React/TS Dashboard       │
           │                            │
           │  ┌──────────┬───────────┐  │
           │  │Transcript│ FHIR View │  │
           │  │Waveform  │ Emotion   │  │
           │  │          │ Timeline  │  │
           │  │          │ Analytics │  │
           │  └──────────┴───────────┘  │
           └────────────────────────────┘
                        │
           ┌────────────▼───────────────┐
           │   HAPI FHIR R4 Server     │
           │   (100 Synthea patients)   │
           └────────────────────────────┘
```

## Key Features

| Feature | Technology | Description |
|---------|-----------|-------------|
| Dual voice pipeline | LiveKit Agents v1.5 | Toggle between cascading (Deepgram→GPT-4.1→ElevenLabs) and OpenAI Realtime S2S |
| Adaptive interruption | LiveKit CNN model | 86% precision distinguishing true barge-ins from backchannels at 30ms |
| Multi-agent handoff | LiveKit Agents | IntakeAgent → TriageAgent → SchedulingAgent with shared patient state |
| Phone integration | Twilio SIP + LiveKit | Real phone number anyone can call for a live demo |
| Emotion detection | Hume AI | Per-utterance emotion analysis feeding into triage severity |
| Streaming FHIR | Instructor + Pydantic | FHIR R4 Bundle constructs progressively as the patient speaks |
| Multimodal vision | GPT-4o | Dermatological image analysis mid-conversation |
| Patient memory | Mem0 | Returning patients greeted by name with prior visit context |
| Multilingual | Deepgram + ElevenLabs | Spanish intake → English clinical FHIR summary |
| Guardrails | NeMo + Guardrails AI | Five-layer safety: input screening, dialog control, output validation |
| Evaluation | DeepEval | 25 clinical scenarios with automated metrics |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- API keys: LiveKit, OpenAI, Deepgram, ElevenLabs, Hume AI, Twilio

### 1. Clone and configure

```bash
git clone <repo-url>
cd healthcare-voice-agent
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start infrastructure

```bash
cd infra
docker compose up -d
```

This starts:
- HAPI FHIR R4 server on `localhost:8080`
- Redis on `localhost:6379`

### 3. Load synthetic patients

```bash
# Download Synthea: https://github.com/synthetichealth/synthea/releases
# Generate 100 patients:
java -jar synthea-with-dependencies.jar -p 100

# Load into HAPI FHIR:
cd infra/synthea
python load_patients.py --fhir-dir ./output/fhir
```

### 4. Install agent dependencies

```bash
cd agent
python -m venv .venv
.venv/Scripts/activate  # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 5. Start the agent

```bash
cd agent
python main.py dev
```

### 6. Start the dashboard

```bash
cd dashboard
npm install
npm run dev
```

Dashboard runs at `http://localhost:3000`.

### 7. Configure Twilio SIP (for phone calls)

1. Purchase a phone number in Twilio Console
2. Create a SIP Trunk pointing to `sip:inbound.livekit.cloud;transport=tcp`
3. Add your LiveKit project credentials to the trunk
4. Configure a dispatch rule in LiveKit Cloud to route inbound calls to the agent

## Pipeline Modes

### Cascade Mode (default)

```
Patient speech → Deepgram Nova-3 Medical → GPT-4.1 → ElevenLabs Flash v2.5
```

- **Latency**: 800–1,500ms round-trip
- **Advantages**: Best-of-breed at each stage, medical STT model, voice selection
- **Cost**: ~$0.01–0.03 per minute

### Realtime Mode

```
Patient speech → OpenAI Realtime API → Patient hears response
```

- **Latency**: 200–500ms round-trip (native speech-to-speech)
- **Advantages**: Lowest latency, native function calling during speech
- **Cost**: ~$0.05–0.08 per minute ($32/M input + $64/M output tokens)

Toggle via `PIPELINE_MODE=cascade|realtime` in `.env`.

## Multi-Agent Flow

```
IntakeAgent                    TriageAgent              SchedulingAgent
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Collect:         │    │ Assess:          │    │ Schedule:        │
│ - Demographics   │───>│ - Severity level │───>│ - Offer slots    │
│ - Chief complaint│    │ - Emotion factor │    │ - Confirm booking│
│ - Symptoms       │    │ - Crisis detect  │    │ - SMS confirm    │
│ - Medications    │    │ - Follow-up Qs   │    │                  │
│ - Allergies      │    │                  │    │                  │
│ - History        │    │ Levels:          │    │                  │
│                  │    │ EMERGENT → 911   │    │                  │
│                  │    │ URGENT → 24hr    │    │                  │
│                  │    │ ROUTINE → normal │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         ↑                                               │
         └───────── Shared UserData (patient state) ─────┘
```

## Evaluation

25 clinical scenarios across 5 categories:

| Category | Scenarios | Tests |
|----------|-----------|-------|
| Normal Intake | 5 | Symptom collection, data extraction accuracy |
| Emergency Escalation | 5 | Chest pain, breathing, suicidal ideation, stroke, bleeding |
| Edge Cases | 5 | Spanish speaker, unresponsive, background noise, rambling, pediatric |
| Memory Continuity | 5 | Returning patient, new allergies, dropped call resume |
| Guardrail Testing | 5 | Diagnosis refusal, prompt injection, off-topic, PII, dangerous advice |

Run evaluations:

```bash
cd agent
python -m eval.test_runner                      # all 25 scenarios
python -m eval.test_runner --category emergency  # one category
python -m eval.test_runner --scenario edge_01_spanish_speaker  # one scenario
```

## HIPAA Compliance Awareness

This project demonstrates awareness of healthcare data regulations required for
production deployment. It is a **portfolio demo** and does not process real PHI.

### Implemented safeguards

- **No PHI storage**: Demo uses Synthea-generated synthetic patients only
- **Output validation**: PII pattern detection and redaction before responses
- **Guardrails**: NeMo Colang 2.0 flows prevent diagnosis and treatment advice
- **Audit logging**: All agent interactions logged with timestamps
- **Crisis protocol**: Suicidal ideation detection → 988 referral → human handoff
- **Emotion detection provider**: Hume AI is HIPAA-compliant with BAA and zero data retention

### Production considerations (per HIPAA Security Rule 2026 update)

The February 2026 HIPAA Security Rule update explicitly requires AI-specific risk analyses:

- **Hallucination risk**: Constrained outputs via Instructor structured extraction reduce free-text hallucination surface
- **Prompt injection**: Five-layer guardrail stack with input screening (Lakera/LLM Guard pattern) and NeMo Colang flows
- **Training data leakage**: No patient data used for model training; all LLM calls use commercial APIs with data processing agreements
- **Access controls**: Production deployment requires role-based access, encryption at rest and in transit, audit trails
- **BAAs required**: OpenAI, Deepgram, ElevenLabs, Hume AI, and LiveKit all offer HIPAA BAAs for enterprise tiers

## Project Structure

```
healthcare-voice-agent/
├── agent/                          # Python backend
│   ├── main.py                     # Entrypoint with pipeline toggle
│   ├── ws_bridge.py                # WebSocket bridge to dashboard
│   ├── agents/                     # Multi-agent definitions
│   │   ├── intake_agent.py         # Patient intake collection
│   │   ├── triage_agent.py         # Severity assessment
│   │   ├── scheduling_agent.py     # Appointment booking
│   │   └── user_data.py            # Shared patient state
│   ├── emotion/
│   │   └── hume_sidecar.py         # Hume AI emotion detection
│   ├── memory/
│   │   └── patient_memory.py       # Mem0 cross-session memory
│   ├── fhir/
│   │   ├── models.py               # FHIR R4 Pydantic models
│   │   └── streaming.py            # Instructor Partial[T] streaming
│   ├── vision/
│   │   └── derma_triage.py         # GPT-4o image analysis
│   ├── guardrails/
│   │   ├── nemo_config/            # Colang 2.0 guardrail flows
│   │   └── output_validators.py    # PII, diagnosis, toxicity checks
│   ├── tools/                      # Agent function tools
│   │   ├── fhir_tools.py           # HAPI FHIR read/write
│   │   ├── scheduling_tools.py     # Appointment management
│   │   └── handoff_tools.py        # Agent transfer utilities
│   ├── eval/                       # Evaluation framework
│   │   ├── test_runner.py          # DeepEval test runner
│   │   └── scenarios/              # 25 clinical test scenarios
│   └── requirements.txt
├── dashboard/                      # React/TypeScript frontend
│   ├── src/
│   │   ├── App.tsx                 # Split-screen layout
│   │   ├── components/
│   │   │   ├── FHIRBundleView.tsx  # Live FHIR construction view
│   │   │   ├── EmotionTimeline.tsx # Emotion score chart
│   │   │   ├── Transcript.tsx      # Real-time transcript
│   │   │   ├── Waveform.tsx        # Audio waveform visualizer
│   │   │   └── CallAnalytics.tsx   # Latency metrics
│   │   └── hooks/
│   │       └── useWebSocket.ts     # Dashboard WS connection
│   └── package.json
├── infra/
│   ├── docker-compose.yml          # HAPI FHIR + Redis
│   └── synthea/
│       └── load_patients.py        # Synthea → HAPI FHIR loader
├── .env.example
└── README.md
```

## Technology Choices

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent framework | LiveKit Agents v1.5 (Python) | Most mature SDK for adaptive interruption, Tasks, multi-agent handoffs |
| STT | Deepgram Nova-3 Medical | Medical vocabulary, multilingual, code-switching support |
| LLM | GPT-4.1 | Best balance of quality, speed, and function calling reliability |
| TTS | ElevenLabs Flash v2.5 | ~75ms latency, 32 languages, natural prosody |
| Emotion | Hume AI Expression Measurement | 48 emotions, HIPAA-compliant, official LiveKit plugin |
| Structured output | Instructor + Pydantic | Streaming Partial[T] for progressive FHIR construction |
| Memory | Mem0 | 26% better than OpenAI memory on LOCOMO, 91% lower p95 latency |
| FHIR server | HAPI FHIR v7 | Open-source R4 reference implementation |
| Frontend | React + TypeScript + Tailwind | Type safety, rapid development, demonstrates TS competency |
| Guardrails | NeMo Colang 2.0 + Guardrails AI | Dialog-level + output-level safety |
| Evaluation | DeepEval | 50+ metrics, conversation-specific, LLM-as-judge |

## License

MIT
