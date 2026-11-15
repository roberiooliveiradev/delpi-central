import { createElement, type ReactNode } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Check,
  ChevronRight,
  Download,
  ExternalLink,
  FileCode2,
  FileText,
  Info,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
} from "lucide-react";

import { ENTRY_AUDIT_SEVERITY_URL } from "../../api/entryAuditApi";

export type EntryAuditBadgeTone =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger";

/** Campos em que diferença monetária/numérica não se aplica (G4). */
const CODE_DIFFERENCE_FIELDS = new Set([
  "cst",
  "cfop",
  "origin",
  "origem",
  "key",
  "chave",
  "series",
  "série",
  "serie",
  "species",
  "espécie",
  "especie",
  "number",
  "número",
  "numero",
  "supplier",
  "cnpj",
  "taker",
  "tomador",
  "ncm",
  "uf",
]);

export const ENTRY_AUDIT_TABS = [
  { value: "occurrences", label: "Ocorrências" },
  { value: "documents", label: "Notas casadas" },
  { value: "unmatched", label: "Sem par" },
  { value: "cte", label: "CT-e" },
  { value: "tes", label: "TES utilizadas" },
  /** Visão de `documents` com `situation=posted_outside_period` (doc 02). */
  { value: "posted_outside", label: "Lançadas fora do período" },
] as const;

export type EntryAuditTab = (typeof ENTRY_AUDIT_TABS)[number]["value"];

/** Resource HTTP da BFF para a aba (posted_outside → documents). */
export function entryAuditTabResource(
  tab: EntryAuditTab,
): "occurrences" | "documents" | "unmatched" | "cte" | "tes" {
  if (tab === "posted_outside") return "documents";
  if (tab === "tes") return "tes";
  return tab;
}

const THEME_LABELS: Record<string, string> = {
  cte: "CT-e",
  item: "Itens",
  header: "Cabeçalho",
  simples: "Simples Nacional",
  coherence: "Coerência fiscal",
  key: "Chave de acesso",
};

const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  nfe: "NF-e",
  cte: "CT-e",
  nfce: "NFC-e",
  nfs: "NFS-e",
};

const iconProps = { size: 16, strokeWidth: 1.75, "aria-hidden": true as const };

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

export function formatTheme(theme: string | null | undefined): string {
  if (!theme) return "—";
  const key = theme.trim().toLowerCase();
  return THEME_LABELS[key] ?? theme;
}

export function formatDocumentType(type: string | null | undefined): string {
  if (!type) return "—";
  const key = type.trim().toLowerCase();
  return DOCUMENT_TYPE_LABELS[key] ?? type.toUpperCase();
}

export function formatDocumentTypes(types: string[] | null | undefined): string {
  if (!types?.length) return "—";
  return types.map(formatDocumentType).join(", ");
}

/** Preferir nome curto das options; fallback «Filial {code}». */
export function formatBranchLabel(
  code: string,
  options?: Array<{ code: string; name?: string | null }>,
): string {
  const match = options?.find((option) => option.code === code);
  if (match?.name?.trim()) return match.name.trim();
  return `Filial ${code}`;
}

export function formatBranches(
  codes: string[],
  options?: Array<{ code: string; name?: string | null }>,
): string {
  if (!codes.length) return "—";
  return codes.map((code) => formatBranchLabel(code, options)).join(", ");
}

export function formatMoneyBRL(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

/**
 * Diferença na tabela/detalhe: R$ pt-BR para valores monetários;
 * «—» para campos de código (CST, CFOP, origem, chave…).
 */
export function formatDifference(
  value: string | number | null | undefined,
  field?: string | null,
): string {
  if (field) {
    const normalized = field.trim().toLowerCase();
    if (
      CODE_DIFFERENCE_FIELDS.has(normalized) ||
      CODE_DIFFERENCE_FIELDS.has(normalized.replace(/\s+/g, "_"))
    ) {
      return "—";
    }
  }
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "number") return formatMoneyBRL(value);
  const text = String(value).trim();
  if (!text) return "—";
  if (/^-?\d+\.\d{2}$/.test(text)) {
    return formatMoneyBRL(Number(text));
  }
  const asPt = Number(text.replace(/\./g, "").replace(",", "."));
  if (/^-?\d+([.,]\d+)?$/.test(text) && !Number.isNaN(asPt)) {
    return formatMoneyBRL(asPt);
  }
  return text;
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

export function auditStatusBadgeVariant(status: string): EntryAuditBadgeTone {
  switch (status) {
    case "done":
    case "resolved":
      return "success";
    case "partial":
    case "queued":
    case "running":
    case "pending":
      return "warning";
    case "failed":
      return "danger";
    default:
      return "neutral";
  }
}

/** Alta crítico, Média atenção, Baixa neutro, Info informativo (G5). */
export function severityBadgeVariant(
  severity: string | null | undefined,
): EntryAuditBadgeTone {
  const key = (severity ?? "").trim().toLowerCase();
  if (key === "alta" || key === "high") return "danger";
  if (key === "média" || key === "media" || key === "medium") return "warning";
  if (key === "baixa" || key === "low") return "neutral";
  if (
    key === "info" ||
    key === "informativo" ||
    key === "depends_on_tes" ||
    key === "depende da tes"
  ) {
    return "info";
  }
  return "neutral";
}

export function severityIcon(severity: string | null | undefined): ReactNode {
  const variant = severityBadgeVariant(severity);
  const props = { size: 14, strokeWidth: 2, "aria-hidden": true as const };
  switch (variant) {
    case "danger":
      return createElement(AlertCircle, props);
    case "warning":
      return createElement(AlertTriangle, props);
    case "info":
      return createElement(Info, props);
    default:
      return createElement(Check, props);
  }
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

/** dd/mm/aaaa hh:mm (E3) — sem segundos. */
export function formatDateTimeShort(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatNoteSeries(
  number: string | null | undefined,
  series: string | null | undefined,
): string {
  const n = (number ?? "").trim();
  const s = (series ?? "").trim();
  if (!n && !s) return "—";
  if (!s) return n;
  if (!n) return `Série ${s}`;
  return `${n}/${s}`;
}

export function entryAuditClaraSuggestions(
  dateFrom: string,
  dateTo: string,
): string[] {
  void dateFrom;
  void dateTo;
  return [
    "Explique as Altas",
    "O que fazer com as notas sem par?",
    "Compare com o período anterior",
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

/** Ícones de ação canônicos (G6) — ~16px. */
export const ENTRY_AUDIT_ACTION_ICONS = {
  play: createElement(Play, iconProps),
  download: createElement(Download, iconProps),
  refresh: createElement(RefreshCw, iconProps),
  plus: createElement(Plus, iconProps),
  check: createElement(Check, iconProps),
  reopen: createElement(RotateCcw, iconProps),
  xml: createElement(FileCode2, iconProps),
  external: createElement(ExternalLink, iconProps),
  open: createElement(ChevronRight, iconProps),
  note: createElement(FileText, iconProps),
} as const;
