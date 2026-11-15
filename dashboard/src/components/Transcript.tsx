import { useRef, useEffect } from "react";
import type { TranscriptEntry } from "../types";

interface Props {
  entries: TranscriptEntry[];
}

export function Transcript({ entries }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries.length]);

  if (entries.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500 text-sm">
        Transcript will appear here when a call begins...
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-3">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
        Live Transcript
      </h2>
      {entries.map((entry, i) => (
        <div
          key={i}
          className={`flex gap-3 ${
            entry.role === "agent" ? "flex-row-reverse" : ""
          }`}
        >
          <div
            className={`shrink-0 h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold ${
              entry.role === "patient"
                ? "bg-cyan-900/60 text-cyan-300"
                : "bg-indigo-900/60 text-indigo-300"
            }`}
          >
            {entry.role === "patient" ? "P" : "A"}
          </div>
          <div
            className={`max-w-[80%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
              entry.role === "patient"
                ? "bg-gray-800 text-gray-100"
                : "bg-indigo-900/30 text-indigo-100"
            }`}
          >
            {entry.text}
          </div>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
