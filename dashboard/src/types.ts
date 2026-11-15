export interface EmotionDataPoint {
  timestamp: number;
  fear: number;
  pain: number;
  distress: number;
  anxiety: number;
  sadness: number;
  anger: number;
  distress_composite: number;
}

export interface TranscriptEntry {
  role: "patient" | "agent";
  text: string;
  timestamp: number;
}

export interface FHIRBundle {
  patient?: {
    full_name?: string;
    date_of_birth?: string;
    phone?: string;
    email?: string;
    address?: string;
    language?: string;
  };
  chief_complaint?: string;
  conditions?: Array<{
    description?: string;
    severity?: string;
    onset?: string;
    body_site?: string;
  }>;
  allergies?: Array<{
    substance?: string;
    reaction?: string;
    severity?: string;
  }>;
  medications?: Array<{
    name?: string;
    dosage?: string;
    status?: string;
  }>;
  triage_assessment?: {
    severity?: string;
    reasoning?: string;
    emotion_summary?: string;
  };
  appointment?: string;
}

export interface CallMetrics {
  stt_ms: number;
  llm_ms: number;
  tts_ms: number;
  total_ms: number;
}
