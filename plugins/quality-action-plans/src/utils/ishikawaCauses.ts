import type { IshikawaAnalysis } from "../types/actionPlan";

export const ISHIKAWA_CATEGORY_KEYS = [
  "method_process",
  "machine",
  "manpower",
  "material",
  "measurement",
  "environment",
] as const;

export type IshikawaCategoryKey = (typeof ISHIKAWA_CATEGORY_KEYS)[number];

export type IshikawaCausesForm = Record<IshikawaCategoryKey, string[]>;

const EMPTY_CAUSES: IshikawaCausesForm = {
  machine: [""],
  method_process: [""],
  material: [""],
  manpower: [""],
  measurement: [""],
  environment: [""],
};

/** Converte valor da API (lista ou legado em string) para campos editáveis. */
export function parseIshikawaCategoryValue(
  value: string | string[] | null | undefined,
): string[] {
  if (Array.isArray(value)) {
    const items = value.map((item) => item.trim()).filter(Boolean);
    return items.length ? items : [""];
  }

  if (!value?.trim()) {
    return [""];
  }

  const items = value
    .split(/\r?\n/)
    .map((line) => line.replace(/^\s*[-•]\s*/, "").trim())
    .filter(Boolean);

  return items.length ? items : [""];
}

export function parseIshikawaCausesForm(data: IshikawaAnalysis | null | undefined): IshikawaCausesForm {
  return {
    machine: parseIshikawaCategoryValue(data?.machine),
    method_process: parseIshikawaCategoryValue(data?.method_process),
    material: parseIshikawaCategoryValue(data?.material),
    manpower: parseIshikawaCategoryValue(data?.manpower),
    measurement: parseIshikawaCategoryValue(data?.measurement),
    environment: parseIshikawaCategoryValue(data?.environment),
  };
}

export function serializeIshikawaCategoryValue(causes: string[]): string[] | null {
  const items = causes.map((item) => item.trim()).filter(Boolean);
  return items.length ? items : null;
}

export function serializeIshikawaCausesForm(
  form: IshikawaCausesForm,
  notes?: string | null,
): IshikawaAnalysis {
  return {
    machine: serializeIshikawaCategoryValue(form.machine),
    method_process: serializeIshikawaCategoryValue(form.method_process),
    material: serializeIshikawaCategoryValue(form.material),
    manpower: serializeIshikawaCategoryValue(form.manpower),
    measurement: serializeIshikawaCategoryValue(form.measurement),
    environment: serializeIshikawaCategoryValue(form.environment),
    notes: notes?.trim() || null,
  };
}

export function emptyIshikawaCausesForm(): IshikawaCausesForm {
  return {
    machine: [...EMPTY_CAUSES.machine],
    method_process: [...EMPTY_CAUSES.method_process],
    material: [...EMPTY_CAUSES.material],
    manpower: [...EMPTY_CAUSES.manpower],
    measurement: [...EMPTY_CAUSES.measurement],
    environment: [...EMPTY_CAUSES.environment],
  };
}
