import type { FiveWhysAnalysis } from "../types/actionPlan";

const LEGACY_OCCURRENCE_KEYS = ["why_1", "why_2", "why_3", "why_4", "why_5"] as const;
const LEGACY_DETECTION_KEYS = [
  "detection_why_1",
  "detection_why_2",
  "detection_why_3",
  "detection_why_4",
  "detection_why_5",
] as const;

export type FiveWhyStep = {
  question: string;
  answer: string;
};

export type FiveWhysForm = {
  occurrence: FiveWhyStep[];
  detection: FiveWhyStep[];
  root_cause: string;
  confidence_level: string;
};

const EMPTY_STEP: FiveWhyStep = { question: "", answer: "" };

export function splitLegacyWhyText(text: string): FiveWhyStep {
  const cleaned = text.trim();
  if (!cleaned) {
    return { ...EMPTY_STEP };
  }
  const questionIndex = cleaned.indexOf("?");
  if (questionIndex >= 0) {
    return {
      question: cleaned.slice(0, questionIndex + 1).trim(),
      answer: cleaned.slice(questionIndex + 1).trim(),
    };
  }
  if (/^por\s*que\b/i.test(cleaned)) {
    return { question: cleaned, answer: "" };
  }
  return { question: "", answer: cleaned };
}

export function normalizeWhyStep(item: unknown): FiveWhyStep | null {
  if (item == null) {
    return null;
  }
  if (typeof item === "string") {
    const step = splitLegacyWhyText(item);
    return step.question.trim() || step.answer.trim() ? step : null;
  }
  if (typeof item === "object") {
    const record = item as Record<string, unknown>;
    const question = typeof record.question === "string" ? record.question.trim() : "";
    const answer = typeof record.answer === "string" ? record.answer.trim() : "";
    if (!question && !answer) {
      return null;
    }
    return { question, answer };
  }
  return null;
}

function parseWhysTrack(
  values: FiveWhysAnalysis["occurrence_whys"],
  legacy: FiveWhysAnalysis | null | undefined,
  legacyKeys: readonly string[],
): FiveWhyStep[] {
  if (Array.isArray(values)) {
    const items = values
      .map((item) => normalizeWhyStep(item))
      .filter((item): item is FiveWhyStep => item !== null);
    return items.length ? items : [{ ...EMPTY_STEP }];
  }

  if (legacy) {
    const items = legacyKeys
      .map((key) => {
        const raw = legacy[key as keyof FiveWhysAnalysis];
        return typeof raw === "string" ? normalizeWhyStep(raw) : null;
      })
      .filter((item): item is FiveWhyStep => item !== null);
    if (items.length) {
      return items;
    }
  }

  return [{ ...EMPTY_STEP }];
}

export function emptyFiveWhysForm(): FiveWhysForm {
  return {
    occurrence: [{ ...EMPTY_STEP }],
    detection: [{ ...EMPTY_STEP }],
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

function serializeWhysTrack(steps: FiveWhyStep[]): FiveWhyStep[] | null {
  const items = steps
    .map((step) => ({
      question: step.question.trim(),
      answer: step.answer.trim(),
    }))
    .filter((step) => step.question || step.answer);
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

export function isFilledWhyStep(step: FiveWhyStep): boolean {
  return Boolean(step.question.trim() || step.answer.trim());
}

export function hasFilledWhysTrack(
  steps: FiveWhysAnalysis["occurrence_whys"] | null | undefined,
): boolean {
  if (!steps?.length) {
    return false;
  }
  return steps.some((item) => {
    const step = normalizeWhyStep(item);
    return step ? isFilledWhyStep(step) : false;
  });
}
