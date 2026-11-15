import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { EmotionDataPoint } from "../types";

interface Props {
  data: EmotionDataPoint[];
}

const EMOTION_COLORS: Record<string, string> = {
  fear: "#ef4444",
  pain: "#f97316",
  distress: "#a855f7",
  anxiety: "#eab308",
  sadness: "#3b82f6",
  anger: "#dc2626",
  distress_composite: "#f43f5e",
};

export function EmotionTimeline({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-800 p-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
          Emotion Timeline
        </h2>
        <div className="h-32 flex items-center justify-center text-gray-500 text-sm">
          Emotion data will appear during the call...
        </div>
      </div>
    );
  }

  const formatted = data.map((d, i) => ({
    ...d,
    idx: i + 1,
  }));

  return (
    <div className="rounded-lg border border-gray-800 p-3">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
        Emotion Timeline
      </h2>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={formatted}>
          <XAxis
            dataKey="idx"
            tick={{ fill: "#6b7280", fontSize: 10 }}
            stroke="#374151"
          />
          <YAxis
            domain={[0, 1]}
            tick={{ fill: "#6b7280", fontSize: 10 }}
            stroke="#374151"
            width={30}
          />
          <Tooltip
            contentStyle={{
              background: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "0.5rem",
              fontSize: "0.75rem",
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: "0.65rem" }}
          />
          <ReferenceLine
            y={0.6}
            stroke="#ef4444"
            strokeDasharray="4 4"
            label={{ value: "Distress threshold", fill: "#ef4444", fontSize: 10 }}
          />
          {Object.entries(EMOTION_COLORS).map(([key, color]) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={color}
              strokeWidth={key === "distress_composite" ? 2.5 : 1.5}
              dot={false}
              opacity={key === "distress_composite" ? 1 : 0.7}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
