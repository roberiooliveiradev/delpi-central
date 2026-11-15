import { ENTRY_AUDIT_SEVERITY_URL } from "../../api/entryAuditApi";

export const ENTRY_AUDIT_TABS = [
  { value: "occurrences", label: "Ocorrências" },
  { value: "documents", label: "Notas casadas" },
  { value: "unmatched", label: "Sem correspondência" },
  { value: "cte", label: "CT-e" },
  { value: "tes", label: "TES utilizadas" },
] as const;

export type EntryAuditTab = (typeof ENTRY_AUDIT_TABS)[number]["value"];

export function parseEntryAuditTab(value: string | null): EntryAuditTab {
  return ENTRY_AUDIT_TABS.some((tab) => tab.value === value)
    ? (value as EntryAuditTab)
    : "occurrences";
}

export function severityFromUrl(value: string | null): string {
  return value ? ENTRY_AUDIT_SEVERITY_URL[value] ?? value : "";
}

export function severityToUrl(value: string): string {
  return (
    Object.entries(ENTRY_AUDIT_SEVERITY_URL).find(
      ([, label]) => label === value,
    )?.[0] ?? value
  );
}

export function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "number") return value.toLocaleString("pt-BR");
  return String(value);
}

export function formatAuditStatus(status: string): string {
  return (
    {
      queued: "Na fila",
      running: "Em processamento",
      done: "Concluída",
      partial: "Concluída parcialmente",
      failed: "Falhou",
      pending: "Pendente",
      resolved: "Resolvida",
    }[status] ?? status
  );
}

export function formatStage(stage: string): string {
  return (
    {
      reading_protheus: "Lendo dados do Protheus",
      reading_xml: "Lendo XML",
      auditing: "Conferindo documentos",
      saving: "Salvando resultado",
      done: "Concluído",
      partial: "Concluído parcialmente",
      failed: "Falhou",
      queued: "Na fila",
    }[stage] ?? stage
  );
}

export function formatPeriodLabel(dateFrom: string, dateTo: string): string {
  const from = new Date(`${dateFrom}T12:00:00`).toLocaleDateString("pt-BR");
  const to = new Date(`${dateTo}T12:00:00`).toLocaleDateString("pt-BR");
  return `${from} a ${to}`;
}

export function entryAuditClaraSuggestions(
  dateFrom: string,
  dateTo: string,
): string[] {
  const period = formatPeriodLabel(dateFrom, dateTo);
  return [
    `Explique a auditoria de entradas de ${period}`,
    "O que pede ação na Matriz?",
    "Por que as CT-e da J.J. Sul deram alta?",
    "Compare com a análise anterior",
  ];
}

export function entryAuditOccurrenceClaraPrompt(
  occurrenceKey: string,
  dateFrom: string,
  dateTo: string,
): string {
  return `Explique a ocorrência ${occurrenceKey} da auditoria de ${formatPeriodLabel(dateFrom, dateTo)} e o que devo corrigir`;
}

export function conformityRatio(clean: number, divergent: number): number {
  const total = clean + divergent;
  if (total <= 0) return 100;
  return Math.round((clean / total) * 100);
}
