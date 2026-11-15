import type { FHIRBundle } from "../types";

interface Props {
  bundle: FHIRBundle;
  finalized: boolean;
}

type FieldStatus = "pending" | "partial" | "confirmed";

function fieldStatus(value: unknown): FieldStatus {
  if (value === undefined || value === null) return "pending";
  if (typeof value === "string" && value.length < 3) return "partial";
  if (Array.isArray(value) && value.length === 0) return "pending";
  return "confirmed";
}

const statusColors: Record<FieldStatus, string> = {
  pending: "border-gray-700 bg-gray-800/40 text-gray-500",
  partial: "border-yellow-700/50 bg-yellow-900/20 text-yellow-200",
  confirmed: "border-green-700/50 bg-green-900/20 text-green-200",
};

const statusDot: Record<FieldStatus, string> = {
  pending: "bg-gray-600",
  partial: "bg-yellow-500",
  confirmed: "bg-green-500",
};

function Field({
  label,
  value,
}: {
  label: string;
  value: unknown;
}) {
  const status = fieldStatus(value);
  const display =
    value === undefined || value === null
      ? "—"
      : Array.isArray(value)
        ? value.length === 0
          ? "—"
          : value.map((v) => (typeof v === "object" ? JSON.stringify(v) : v)).join(", ")
        : String(value);

  return (
    <div
      className={`rounded-md border px-3 py-2 text-sm ${statusColors[status]}`}
    >
      <div className="flex items-center gap-1.5 mb-0.5">
        <span className={`h-1.5 w-1.5 rounded-full ${statusDot[status]}`} />
        <span className="text-xs font-medium uppercase tracking-wider opacity-70">
          {label}
        </span>
      </div>
      <div className="truncate">{display}</div>
    </div>
  );
}

export function FHIRBundleView({ bundle, finalized }: Props) {
  const triageSeverity = bundle.triage_assessment?.severity;
  const triageColors: Record<string, string> = {
    emergent: "bg-red-600 text-white",
    urgent: "bg-amber-600 text-white",
    routine: "bg-green-600 text-white",
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
          FHIR Intake Bundle
        </h2>
        {finalized && (
          <span className="text-xs font-medium bg-green-900/50 text-green-300 rounded-full px-2.5 py-0.5 animate-pulse">
            Posted to FHIR Server
          </span>
        )}
        {triageSeverity && (
          <span
            className={`text-xs font-bold rounded-full px-2.5 py-0.5 uppercase ${
              triageColors[triageSeverity] ?? "bg-gray-700"
            }`}
          >
            {triageSeverity}
          </span>
        )}
      </div>

      {/* Patient Demographics */}
      <div className="rounded-lg border border-gray-800 p-3 space-y-2">
        <h3 className="text-xs font-semibold text-gray-400">Patient</h3>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Name" value={bundle.patient?.full_name} />
          <Field label="DOB" value={bundle.patient?.date_of_birth} />
          <Field label="Phone" value={bundle.patient?.phone} />
          <Field label="Language" value={bundle.patient?.language} />
        </div>
      </div>

      {/* Chief Complaint */}
      <div className="rounded-lg border border-gray-800 p-3 space-y-2">
        <h3 className="text-xs font-semibold text-gray-400">Chief Complaint</h3>
        <Field label="Reason for Visit" value={bundle.chief_complaint} />
      </div>

      {/* Conditions */}
      <div className="rounded-lg border border-gray-800 p-3 space-y-2">
        <h3 className="text-xs font-semibold text-gray-400">
          Conditions ({bundle.conditions?.length ?? 0})
        </h3>
        {(bundle.conditions ?? []).map((c, i) => (
          <div key={i} className="grid grid-cols-2 gap-2">
            <Field label="Description" value={c.description} />
            <Field label="Severity" value={c.severity} />
          </div>
        ))}
        {(!bundle.conditions || bundle.conditions.length === 0) && (
          <Field label="Symptoms" value={undefined} />
        )}
      </div>

      {/* Allergies & Medications side by side */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-gray-800 p-3 space-y-2">
          <h3 className="text-xs font-semibold text-gray-400">
            Allergies ({bundle.allergies?.length ?? 0})
          </h3>
          {(bundle.allergies ?? []).map((a, i) => (
            <Field key={i} label={a.substance ?? "Allergen"} value={a.reaction ?? a.substance} />
          ))}
          {(!bundle.allergies || bundle.allergies.length === 0) && (
            <Field label="Allergies" value={undefined} />
          )}
        </div>
        <div className="rounded-lg border border-gray-800 p-3 space-y-2">
          <h3 className="text-xs font-semibold text-gray-400">
            Medications ({bundle.medications?.length ?? 0})
          </h3>
          {(bundle.medications ?? []).map((m, i) => (
            <Field key={i} label={m.name ?? "Medication"} value={m.dosage ?? m.name} />
          ))}
          {(!bundle.medications || bundle.medications.length === 0) && (
            <Field label="Medications" value={undefined} />
          )}
        </div>
      </div>

      {/* Triage */}
      {bundle.triage_assessment && (
        <div className="rounded-lg border border-gray-800 p-3 space-y-2">
          <h3 className="text-xs font-semibold text-gray-400">Triage Assessment</h3>
          <Field label="Reasoning" value={bundle.triage_assessment.reasoning} />
          <Field
            label="Emotional State"
            value={bundle.triage_assessment.emotion_summary}
          />
        </div>
      )}

      {/* Appointment */}
      {bundle.appointment && (
        <div className="rounded-lg border border-gray-800 p-3">
          <Field label="Scheduled Appointment" value={bundle.appointment} />
        </div>
      )}
    </div>
  );
}
