import type { ReportSnapshot } from "./reportForm";

export type ReportListFilters = {
  from: string;
  to: string;
  terminal: string;
  part: string;
  product: string;
  cable: string;
  section: string;
  applicator: string;
  press: string;
  lot: string;
  sample: string;
};

export const EMPTY_REPORT_FILTERS: ReportListFilters = {
  from: "",
  to: "",
  terminal: "",
  part: "",
  product: "",
  cable: "",
  section: "",
  applicator: "",
  press: "",
  lot: "",
  sample: "",
};

function normalize(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR").trim();
}

function dateKey(value: string | null | undefined): number | null {
  const text = (value ?? "").trim();
  if (!text) return null;
  let match = /^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$/.exec(text);
  if (match) return Date.UTC(Number(match[3]), Number(match[2]) - 1, Number(match[1]));
  match = /^(\d{4})-(\d{1,2})-(\d{1,2})/.exec(text);
  if (match) return Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  const date = new Date(text);
  if (Number.isNaN(date.getTime())) return null;
  return Date.UTC(date.getFullYear(), date.getMonth(), date.getDate());
}

export function reportMatches(report: ReportSnapshot, filters: ReportListFilters): boolean {
  const sample = report.sample;
  const pairs: Array<[string, string | null]> = [
    [filters.terminal, sample.terminal_code],
    [filters.part, sample.terminal_part_number],
    [filters.product, sample.product_harness],
    [filters.cable, sample.cable],
    [filters.section, sample.conductor_section],
    [filters.applicator, sample.applicator_tool],
    [filters.press, sample.press_equipment],
    [filters.lot, sample.batch_production_order],
    [filters.sample, sample.sample_identification],
  ];
  for (const [query, field] of pairs) {
    if (query && !normalize(field ?? "").includes(normalize(query))) return false;
  }
  const start = dateKey(filters.from);
  const end = dateKey(filters.to);
  if (start !== null || end !== null) {
    const key = dateKey(report.report_date) ?? dateKey(report.created_at) ?? dateKey(report.updated_at);
    if (key === null || (start !== null && key < start) || (end !== null && key > end)) return false;
  }
  return true;
}
