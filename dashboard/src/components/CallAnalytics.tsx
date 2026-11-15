import type { CallMetrics } from "../types";

interface Props {
  metrics: CallMetrics[];
}

export function CallAnalytics({ metrics }: Props) {
  if (metrics.length === 0) {
    return (
      <div className="p-3 text-center text-gray-500 text-xs">
        Latency metrics will appear during the call
      </div>
    );
  }

  const latest = metrics[metrics.length - 1];
  const avgTotal =
    metrics.reduce((sum, m) => sum + m.total_ms, 0) / metrics.length;
  const p95Idx = Math.floor(metrics.length * 0.95);
  const sorted = [...metrics].sort((a, b) => a.total_ms - b.total_ms);
  const p95 = sorted[p95Idx]?.total_ms ?? latest.total_ms;

  return (
    <div className="p-3 space-y-2">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
        Call Analytics
      </h2>
      <div className="grid grid-cols-5 gap-2">
        <MetricCard label="STT" value={latest.stt_ms} unit="ms" />
        <MetricCard label="LLM" value={latest.llm_ms} unit="ms" />
        <MetricCard label="TTS" value={latest.tts_ms} unit="ms" />
        <MetricCard label="Avg Total" value={Math.round(avgTotal)} unit="ms" />
        <MetricCard label="p95" value={Math.round(p95)} unit="ms" />
      </div>
      <div className="flex gap-1 h-8 items-end">
        {metrics.slice(-40).map((m, i) => (
          <div
            key={i}
            className="flex-1 rounded-sm min-w-[3px]"
            style={{
              height: `${Math.min(100, (m.total_ms / 2000) * 100)}%`,
              backgroundColor:
                m.total_ms < 500
                  ? "#10b981"
                  : m.total_ms < 1000
                    ? "#eab308"
                    : "#ef4444",
            }}
          />
        ))}
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  unit,
}: {
  label: string;
  value: number;
  unit: string;
}) {
  return (
    <div className="rounded-md bg-gray-800/60 px-2 py-1.5 text-center">
      <div className="text-[10px] uppercase tracking-wider text-gray-500">
        {label}
      </div>
      <div className="text-sm font-mono font-semibold text-gray-200">
        {value}
        <span className="text-xs text-gray-500 ml-0.5">{unit}</span>
      </div>
    </div>
  );
}
