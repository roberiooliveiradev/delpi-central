export const MEASUREMENT_FIELDS = [
  { key: "crimp_height_ch", code: "CH", label: "Altura de crimpagem" },
  { key: "crimp_width_cb", code: "CB", label: "Largura de crimpagem" },
  { key: "void_area_av", code: "AV", label: "Porcentagem de vazios" },
  { key: "left_burr_gh_e", code: "GH-E", label: "Rebarba esquerda" },
  { key: "right_burr_gh_d", code: "GH-D", label: "Rebarba direita" },
] as const;

export type MeasurementKey = (typeof MEASUREMENT_FIELDS)[number]["key"];

export const SAMPLE_FIELDS = [
  { key: "terminal_code", label: "Terminal" },
  { key: "terminal_part_number", label: "Part number" },
  { key: "product_harness", label: "Produto/chicote" },
  { key: "cable", label: "Cabo" },
  { key: "conductor_section", label: "Seção do condutor" },
  { key: "applicator_tool", label: "Aplicador" },
  { key: "press_equipment", label: "Prensa" },
  { key: "batch_production_order", label: "Lote/ordem de produção" },
  { key: "sample_identification", label: "Identificação da amostra" },
] as const;

export type SampleKey = (typeof SAMPLE_FIELDS)[number]["key"];

export type MeasurementPair = { criterion: string; measured: string };

export type ConclusionResult = "" | "conforming" | "nonconforming";

export type ReportFormState = {
  reportDate: string;
  revision: string;
  sample: Record<SampleKey, string>;
  measurements: Record<MeasurementKey, MeasurementPair>;
  conclusionResult: ConclusionResult;
  conclusionNotes: string;
  analystName: string;
};

export type ReportSnapshot = {
  id: string;
  report_number: string;
  report_date: string | null;
  revision: string;
  sample: Record<SampleKey, string | null>;
  measurements: Record<MeasurementKey, { criterion: string | null; measured: string | null }>;
  conclusion: { result: "conforming" | "nonconforming" | null; notes: string | null };
  analyst: { name: string | null; user_id: string | null };
  images: {
    original: { present: boolean; content_type: string | null; sha256: string | null };
    measured: { present: boolean; content_type: string | null; sha256: string | null };
  };
  status: string;
  version: number;
  created_at: string | null;
  updated_at: string | null;
};

const SAMPLE_MAX = 240;
const NOTES_MAX = 4000;
const CRITERION_MAX = 120;
const MEASURED_MAX = 40;
const REVISION_MAX = 16;
const ANALYST_MAX = 160;

function blankSample(): Record<SampleKey, string> {
  return {
    terminal_code: "",
    terminal_part_number: "",
    product_harness: "",
    cable: "",
    conductor_section: "",
    applicator_tool: "",
    press_equipment: "",
    batch_production_order: "",
    sample_identification: "",
  };
}

function blankMeasurements(): Record<MeasurementKey, MeasurementPair> {
  return {
    crimp_height_ch: { criterion: "", measured: "" },
    crimp_width_cb: { criterion: "", measured: "" },
    void_area_av: { criterion: "", measured: "" },
    left_burr_gh_e: { criterion: "", measured: "" },
    right_burr_gh_d: { criterion: "", measured: "" },
  };
}

export function emptyReportForm(): ReportFormState {
  return {
    reportDate: "",
    revision: "00",
    sample: blankSample(),
    measurements: blankMeasurements(),
    conclusionResult: "",
    conclusionNotes: "",
    analystName: "",
  };
}

function textOrNull(value: string, limit: number): string | null {
  const text = value.trim();
  if (!text) return null;
  return text.slice(0, limit);
}

export function isoToDisplayDate(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  if (!match) return text;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

export function displayDateToIso(value: string): string | null {
  const text = value.trim();
  if (!text) return null;
  const brazilian = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(text);
  if (brazilian) return `${brazilian[3]}-${brazilian[2]}-${brazilian[1]}`;
  return text.slice(0, 10);
}

export function formFromReport(report: ReportSnapshot): ReportFormState {
  const sample = blankSample();
  for (const field of SAMPLE_FIELDS) {
    sample[field.key] = report.sample[field.key] ?? "";
  }
  const measurements = blankMeasurements();
  for (const field of MEASUREMENT_FIELDS) {
    const pair = report.measurements[field.key];
    measurements[field.key] = {
      criterion: pair?.criterion ?? "",
      measured: pair?.measured ?? "",
    };
  }
  const result = report.conclusion.result;
  return {
    reportDate: isoToDisplayDate(report.report_date),
    revision: report.revision || "00",
    sample,
    measurements,
    conclusionResult: result === "conforming" || result === "nonconforming" ? result : "",
    conclusionNotes: report.conclusion.notes ?? "",
    analystName: report.analyst.name ?? "",
  };
}

export type ReportWritePayload = {
  report_date: string | null;
  revision: string;
  sample: Record<SampleKey, string | null>;
  measurements: Record<MeasurementKey, { criterion: string | null; measured: string | null }>;
  conclusion: { result: "conforming" | "nonconforming" | null; notes: string | null };
  analyst: { name: string | null };
  status: "draft";
};

export function toWritePayload(form: ReportFormState): ReportWritePayload {
  const sample = blankSample() as unknown as Record<SampleKey, string | null>;
  for (const field of SAMPLE_FIELDS) {
    sample[field.key] = textOrNull(form.sample[field.key], SAMPLE_MAX);
  }
  const measurements = blankMeasurements() as unknown as ReportWritePayload["measurements"];
  for (const field of MEASUREMENT_FIELDS) {
    const pair = form.measurements[field.key];
    measurements[field.key] = {
      criterion: textOrNull(pair.criterion, CRITERION_MAX),
      measured: textOrNull(pair.measured, MEASURED_MAX),
    };
  }
  return {
    report_date: displayDateToIso(form.reportDate),
    revision: textOrNull(form.revision, REVISION_MAX) ?? "00",
    sample,
    measurements,
    conclusion: {
      result: form.conclusionResult || null,
      notes: textOrNull(form.conclusionNotes, NOTES_MAX),
    },
    analyst: { name: textOrNull(form.analystName, ANALYST_MAX) },
    status: "draft",
  };
}

export function formsEqual(left: ReportFormState, right: ReportFormState): boolean {
  return JSON.stringify(toWritePayload(left)) === JSON.stringify(toWritePayload(right));
}

export function conclusionLabel(result: string | null | undefined): string {
  if (result === "conforming") return "Conforme";
  if (result === "nonconforming") return "Não conforme";
  return "Sem conclusão";
}
