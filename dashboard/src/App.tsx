import { useState, useCallback } from "react";
import { useWebSocket, type WSMessage } from "./hooks/useWebSocket";
import type {
  EmotionDataPoint,
  TranscriptEntry,
  FHIRBundle,
  CallMetrics,
} from "./types";
import { Transcript } from "./components/Transcript";
import { FHIRBundleView } from "./components/FHIRBundleView";
import { EmotionTimeline } from "./components/EmotionTimeline";
import { Waveform } from "./components/Waveform";
import { CallAnalytics } from "./components/CallAnalytics";

const WS_URL =
  import.meta.env.PROD
    ? `ws://${window.location.hostname}:8765`
    : `ws://${window.location.host}/ws`;

export default function App() {
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [fhirBundle, setFhirBundle] = useState<FHIRBundle>({});
  const [fhirFinalized, setFhirFinalized] = useState(false);
  const [emotions, setEmotions] = useState<EmotionDataPoint[]>([]);
  const [activeAgent, setActiveAgent] = useState("IntakeAgent");
  const [metrics, setMetrics] = useState<CallMetrics[]>([]);
  const [callActive, setCallActive] = useState(false);
  const [callerPhone, setCallerPhone] = useState("");

  const onMessage = useCallback((msg: WSMessage) => {
    switch (msg.type) {
      case "transcript_update":
        setTranscript((prev) => [
          ...prev,
          {
            role: msg.role as "patient" | "agent",
            text: msg.text,
            timestamp: msg.timestamp,
          },
        ]);
        break;
      case "fhir_update":
        setFhirBundle(msg.bundle as FHIRBundle);
        break;
      case "fhir_finalized":
        setFhirFinalized(true);
        break;
      case "emotion_update":
        setEmotions((prev) => [
          ...prev,
          {
            timestamp: msg.timestamp,
            fear: msg.scores.fear ?? 0,
            pain: msg.scores.pain ?? 0,
            distress: msg.scores.distress ?? 0,
            anxiety: msg.scores.anxiety ?? 0,
            sadness: msg.scores.sadness ?? 0,
            anger: msg.scores.anger ?? 0,
            distress_composite: msg.distress_composite,
          },
        ]);
        break;
      case "agent_change":
        setActiveAgent(msg.agent);
        break;
      case "call_metrics":
        setMetrics((prev) => [
          ...prev,
          {
            stt_ms: msg.stt_ms,
            llm_ms: msg.llm_ms,
            tts_ms: msg.tts_ms,
            total_ms: msg.total_ms,
          },
        ]);
        break;
      case "call_start":
        setCallActive(true);
        setCallerPhone(msg.caller_phone);
        setTranscript([]);
        setFhirBundle({});
        setFhirFinalized(false);
        setEmotions([]);
        setMetrics([]);
        break;
      case "call_end":
        setCallActive(false);
        break;
    }
  }, []);

  const { connected } = useWebSocket({ url: WS_URL, onMessage });

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold tracking-tight">
            Clinical Intake Dashboard
          </h1>
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${
              callActive
                ? "bg-green-900/50 text-green-300"
                : "bg-gray-800 text-gray-400"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                callActive ? "bg-green-400 animate-pulse" : "bg-gray-500"
              }`}
            />
            {callActive ? `Live Call — ${callerPhone}` : "Waiting for call"}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <AgentBadge agent={activeAgent} />
          <span
            className={`h-2 w-2 rounded-full ${
              connected ? "bg-emerald-400" : "bg-red-500"
            }`}
            title={connected ? "WebSocket connected" : "WebSocket disconnected"}
          />
        </div>
      </header>

      {/* Main content: split-screen */}
      <div className="flex-1 grid grid-cols-2 divide-x divide-gray-800 overflow-hidden">
        {/* Left panel: conversation */}
        <div className="flex flex-col overflow-hidden">
          <div className="flex-1 overflow-hidden">
            <Transcript entries={transcript} />
          </div>
          <div className="border-t border-gray-800 h-24 shrink-0">
            <Waveform active={callActive} />
          </div>
        </div>

        {/* Right panel: structured data */}
        <div className="flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <FHIRBundleView bundle={fhirBundle} finalized={fhirFinalized} />
            <EmotionTimeline data={emotions} />
          </div>
          <div className="border-t border-gray-800 shrink-0">
            <CallAnalytics metrics={metrics} />
          </div>
        </div>
      </div>
    </div>
  );
}

function AgentBadge({ agent }: { agent: string }) {
  const colors: Record<string, string> = {
    IntakeAgent: "bg-blue-900/50 text-blue-300",
    TriageAgent: "bg-amber-900/50 text-amber-300",
    SchedulingAgent: "bg-purple-900/50 text-purple-300",
  };
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
        colors[agent] ?? "bg-gray-800 text-gray-400"
      }`}
    >
      {agent.replace("Agent", "")}
    </span>
  );
}
