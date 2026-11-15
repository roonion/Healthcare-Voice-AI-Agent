import { useEffect, useRef, useState } from "react";

export type WSMessage =
  | { type: "transcript_update"; role: string; text: string; timestamp: number }
  | { type: "fhir_update"; bundle: Record<string, unknown> }
  | { type: "fhir_finalized"; bundle_id: string }
  | {
      type: "emotion_update";
      timestamp: number;
      scores: Record<string, number>;
      distress_composite: number;
    }
  | { type: "agent_change"; agent: string }
  | {
      type: "call_metrics";
      stt_ms: number;
      llm_ms: number;
      tts_ms: number;
      total_ms: number;
    }
  | { type: "call_start"; caller_phone: string }
  | { type: "call_end"; duration_seconds: number };

interface UseWebSocketOptions {
  url: string;
  onMessage?: (msg: WSMessage) => void;
}

export function useWebSocket({ url, onMessage }: UseWebSocketOptions) {
  const [connected, setConnected] = useState(false);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
    let disposed = false;

    function connect() {
      if (disposed) return;
      try {
        ws = new WebSocket(url);

        ws.onopen = () => {
          if (!disposed) setConnected(true);
        };
        ws.onclose = () => {
          if (disposed) return;
          setConnected(false);
          reconnectTimer = setTimeout(connect, 3000);
        };
        ws.onerror = () => ws?.close();
        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data) as WSMessage;
            onMessageRef.current?.(msg);
          } catch {
            // ignore malformed messages
          }
        };
      } catch {
        if (!disposed) {
          reconnectTimer = setTimeout(connect, 3000);
        }
      }
    }

    connect();

    return () => {
      disposed = true;
      clearTimeout(reconnectTimer);
      if (ws) {
        ws.onclose = null;
        ws.close();
      }
    };
  }, [url]);

  return { connected };
}
