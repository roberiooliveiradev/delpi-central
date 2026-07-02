import type {
  KaizenFormValues,
  KaizenParticipant,
  KaizenRecord,
  ParticipantRole,
  SavingsType,
} from "../types/kaizen";

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

export const PARTICIPANT_ROLES: Array<{ value: ParticipantRole; label: string }> = [
  { value: "responsavel", label: "Responsável" },
  { value: "participante", label: "Participante" },
  { value: "apoio", label: "Apoio" },
];

export const KAIZEN_CATEGORIES = [
  "Ergonomia",
  "Segurança",
  "Custo",
  "Qualidade",
  "Produtividade",
  "5S",
  "Meio ambiente",
] as const;

export function emptyFormValues(): KaizenFormValues {
  return {
    branch_code: "01",
    title: "",
    sector: "",
    category: "",
    investment: "",
    savings_type: "",
    seconds_per_occurrence: "",
    occurrences_per_day: "",
    hourly_cost: "",
    quantity_saved_per_day: "",
    unit_material_cost: "",
    fixed_daily_savings: "",
    realized_daily_savings: "",
    status: "em_andamento",
    date_implemented: "",
    date_discontinued: "",
    notes: "",
    process_description: "",
    problem_description: "",
    improvement_description: "",
    expected_result: "",
    participants: [],
  };
}

function participantsFromRecord(record: KaizenRecord): KaizenParticipant[] {
  if (record.participants && record.participants.length > 0) {
    return record.participants.map((p) => ({
      name: p.name,
      role: p.role,
      user_id: p.user_id ?? null,
    }));
  }
  if (record.accountable) {
    return [{ name: record.accountable, role: "responsavel" }];
  }
  return [];
}

export function recordToFormValues(record: KaizenRecord): KaizenFormValues {
  return {
    branch_code: record.branch_code,
    title: record.title,
    sector: record.sector ?? "",
    category: record.category ?? "",
    investment: record.investment?.toString() ?? "",
    savings_type: record.savings_type,
    seconds_per_occurrence: record.seconds_per_occurrence?.toString() ?? "",
    occurrences_per_day: record.occurrences_per_day?.toString() ?? "",
    hourly_cost: record.hourly_cost?.toString() ?? "",
    quantity_saved_per_day: record.quantity_saved_per_day?.toString() ?? "",
    unit_material_cost: record.unit_material_cost?.toString() ?? "",
    fixed_daily_savings: record.fixed_daily_savings?.toString() ?? "",
    realized_daily_savings: record.realized_daily_savings?.toString() ?? "",
    status: record.status,
    date_implemented: record.date_implemented ?? "",
    date_discontinued: record.date_discontinued ?? "",
    notes: record.notes ?? "",
    process_description: record.process_description ?? "",
    problem_description: record.problem_description ?? "",
    improvement_description: record.improvement_description ?? "",
    expected_result: record.expected_result ?? "",
    participants: participantsFromRecord(record),
  };
}

/** Valores de formulário a partir do snapshot de uma versão (mescla sobre o cabeçalho). */
export function snapshotToFormValues(
  record: KaizenRecord,
  snapshot: Partial<KaizenRecord>,
): KaizenFormValues {
  return recordToFormValues({ ...record, ...snapshot, id: record.id });
}

export function parseOptionalNumber(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number(trimmed.replace(",", "."));
  return Number.isFinite(parsed) ? parsed : null;
}

function cleanParticipants(participants: KaizenParticipant[]): KaizenParticipant[] {
  return participants
    .map((p) => ({ name: p.name.trim(), role: p.role, user_id: p.user_id ?? null }))
    .filter((p) => p.name.length > 0);
}

export function formValuesToPayload(values: KaizenFormValues): Record<string, unknown> {
  return {
    branch_code: values.branch_code,
    title: values.title.trim(),
    sector: values.sector.trim() || null,
    category: values.category.trim() || null,
    investment: parseOptionalNumber(values.investment),
    savings_type: values.savings_type || null,
    seconds_per_occurrence: parseOptionalNumber(values.seconds_per_occurrence),
    occurrences_per_day: parseOptionalNumber(values.occurrences_per_day),
    hourly_cost: parseOptionalNumber(values.hourly_cost),
    quantity_saved_per_day: parseOptionalNumber(values.quantity_saved_per_day),
    unit_material_cost: parseOptionalNumber(values.unit_material_cost),
    fixed_daily_savings: parseOptionalNumber(values.fixed_daily_savings),
    realized_daily_savings: parseOptionalNumber(values.realized_daily_savings),
    status: values.status,
    date_implemented: values.date_implemented || null,
    date_discontinued: values.date_discontinued || null,
    notes: values.notes.trim() || null,
    process_description: values.process_description.trim() || null,
    problem_description: values.problem_description.trim() || null,
    improvement_description: values.improvement_description.trim() || null,
    expected_result: values.expected_result.trim() || null,
    participants: cleanParticipants(values.participants),
  };
}

export type View = "dashboard" | "list" | "new" | "edit" | "detail";

export function parseRoute(pathname?: string): { view: View; id?: string } {
  const path = (pathname ?? "/apps/cadastro-kaizen").replace(/\/+$/, "");
  if (path.endsWith("/dashboard")) return { view: "dashboard" };
  if (path.endsWith("/novo")) return { view: "new" };
  const detailMatch = path.match(/\/detalhe\/([^/]+)$/);
  if (detailMatch) return { view: "detail", id: detailMatch[1] };
  const editMatch = path.match(/\/editar\/([^/]+)$/);
  if (editMatch) return { view: "detail", id: editMatch[1] };
  return { view: "list" };
}

export function listPath(): string {
  return "/apps/cadastro-kaizen";
}

export function dashboardPath(): string {
  return "/apps/cadastro-kaizen/dashboard";
}

export function newPath(): string {
  return "/apps/cadastro-kaizen/novo";
}

export function detailPath(id: string): string {
  return `/apps/cadastro-kaizen/detalhe/${id}`;
}

export function editPath(id: string): string {
  return detailPath(id);
}
