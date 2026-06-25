import type { FiveWhysAnalysis } from "../types/actionPlan";

const LEGACY_OCCURRENCE_KEYS = ["why_1", "why_2", "why_3", "why_4", "why_5"] as const;
const LEGACY_DETECTION_KEYS = [
  "detection_why_1",
  "detection_why_2",
  "detection_why_3",
  "detection_why_4",
  "detection_why_5",
] as const;

export type FiveWhysForm = {
  occurrence: string[];
  detection: string[];
  root_cause: string;
  confidence_level: string;
};

function parseWhysTrack(
  values: string[] | null | undefined,
  legacy: FiveWhysAnalysis | null | undefined,
  legacyKeys: readonly string[],
): string[] {
  if (Array.isArray(values)) {
    const items = values.map((item) => item.trim()).filter(Boolean);
    return items.length ? items : [""];
  }

  if (legacy) {
    const items = legacyKeys
      .map((key) => {
        const raw = legacy[key as keyof FiveWhysAnalysis];
        return typeof raw === "string" ? raw.trim() : "";
      })
      .filter(Boolean);
    if (items.length) {
      return items;
    }
  }

  return [""];
}

export function emptyFiveWhysForm(): FiveWhysForm {
  return {
    occurrence: [""],
    detection: [""],
    root_cause: "",
    confidence_level: "medium",
  };
}

export function parseFiveWhysForm(data: FiveWhysAnalysis | null | undefined): FiveWhysForm {
  return {
    occurrence: parseWhysTrack(data?.occurrence_whys, data ?? undefined, LEGACY_OCCURRENCE_KEYS),
    detection: parseWhysTrack(data?.detection_whys, data ?? undefined, LEGACY_DETECTION_KEYS),
    root_cause: data?.root_cause?.trim() ?? "",
    confidence_level: data?.confidence_level ?? "medium",
  };
}

function serializeWhysTrack(steps: string[]): string[] | null {
  const items = steps.map((item) => item.trim()).filter(Boolean);
  return items.length ? items : null;
}

export function serializeFiveWhysForm(form: FiveWhysForm): FiveWhysAnalysis {
  return {
    occurrence_whys: serializeWhysTrack(form.occurrence),
    detection_whys: serializeWhysTrack(form.detection),
    root_cause: form.root_cause.trim() || null,
    confidence_level: form.confidence_level || null,
  };
}

export function hasFilledWhysTrack(steps: string[] | null | undefined): boolean {
  return Boolean(steps?.some((item) => item.trim()));
}
