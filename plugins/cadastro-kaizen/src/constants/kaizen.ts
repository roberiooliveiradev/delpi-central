import type { KaizenFormValues, KaizenRecord, SavingsType } from "../types/kaizen";

export const BRANCHES = [
  { code: "01", label: "Filial 01" },
  { code: "02", label: "Filial 02" },
] as const;

export const SAVINGS_TYPES: Array<{ value: SavingsType; label: string }> = [
  { value: "tempo", label: "Tempo" },
  { value: "material", label: "Material" },
  { value: "financeiro", label: "Financeiro" },
  { value: "qualitativo", label: "Qualitativo" },
  { value: "misto", label: "Misto" },
];

export const KAIZEN_STATUSES = [
  { value: "em_andamento", label: "Em andamento" },
  { value: "implantado", label: "Implantado" },
  { value: "descontinuado", label: "Descontinuado" },
  { value: "cancelado", label: "Cancelado" },
] as const;

export function emptyFormValues(): KaizenFormValues {
  return {
    branch_code: "01",
    title: "",
    accountable: "",
    sector: "",
    investment: "",
    savings_type: "",
    seconds_per_occurrence: "",
    occurrences_per_day: "",
    hourly_cost: "",
    quantity_saved_per_day: "",
    unit_material_cost: "",
    fixed_daily_savings: "",
    status: "em_andamento",
    date_implemented: "",
    date_discontinued: "",
    notes: "",
  };
}

export function recordToFormValues(record: KaizenRecord): KaizenFormValues {
  return {
    branch_code: record.branch_code,
    title: record.title,
    accountable: record.accountable ?? "",
    sector: record.sector ?? "",
    investment: record.investment?.toString() ?? "",
    savings_type: record.savings_type,
    seconds_per_occurrence: record.seconds_per_occurrence?.toString() ?? "",
    occurrences_per_day: record.occurrences_per_day?.toString() ?? "",
    hourly_cost: record.hourly_cost?.toString() ?? "",
    quantity_saved_per_day: record.quantity_saved_per_day?.toString() ?? "",
    unit_material_cost: record.unit_material_cost?.toString() ?? "",
    fixed_daily_savings: record.fixed_daily_savings?.toString() ?? "",
    status: record.status,
    date_implemented: record.date_implemented ?? "",
    date_discontinued: record.date_discontinued ?? "",
    notes: record.notes ?? "",
  };
}

export function parseOptionalNumber(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number(trimmed.replace(",", "."));
  return Number.isFinite(parsed) ? parsed : null;
}

export function formValuesToPayload(values: KaizenFormValues) {
  return {
    branch_code: values.branch_code,
    title: values.title.trim(),
    accountable: values.accountable.trim() || null,
    sector: values.sector.trim() || null,
    investment: parseOptionalNumber(values.investment),
    savings_type: values.savings_type || null,
    seconds_per_occurrence: parseOptionalNumber(values.seconds_per_occurrence),
    occurrences_per_day: parseOptionalNumber(values.occurrences_per_day),
    hourly_cost: parseOptionalNumber(values.hourly_cost),
    quantity_saved_per_day: parseOptionalNumber(values.quantity_saved_per_day),
    unit_material_cost: parseOptionalNumber(values.unit_material_cost),
    fixed_daily_savings: parseOptionalNumber(values.fixed_daily_savings),
    status: values.status,
    date_implemented: values.date_implemented || null,
    date_discontinued: values.date_discontinued || null,
    notes: values.notes.trim() || null,
  };
}

export function parseRoute(pathname?: string): { view: "list" | "new" | "edit"; id?: string } {
  const path = (pathname ?? "/apps/cadastro-kaizen").replace(/\/+$/, "");
  if (path.endsWith("/novo")) return { view: "new" };
  const editMatch = path.match(/\/editar\/([^/]+)$/);
  if (editMatch) return { view: "edit", id: editMatch[1] };
  return { view: "list" };
}

export function listPath(): string {
  return "/apps/cadastro-kaizen";
}

export function newPath(): string {
  return "/apps/cadastro-kaizen/novo";
}

export function editPath(id: string): string {
  return `/apps/cadastro-kaizen/editar/${id}`;
}
