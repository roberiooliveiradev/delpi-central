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

import {
  ENTRY_AUDIT_SEVERITY_URL,
  type EntryAuditFilters,
} from "../../api/entryAuditApi";

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
  item: "Itens da nota",
  items: "Itens da nota",
  header: "Cabeçalho da nota",
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

/** Filtros de detalhamento (exclui tab, page, page_size, sort, order). */
export function entryAuditDetailFiltersFromSearch(
  params: URLSearchParams,
): EntryAuditFilters {
  return {
    branch: params.get("branch") ?? "",
    severity: severityFromUrl(params.get("severity")),
    theme: params.get("theme") ?? "",
    supplier: params.get("supplier") ?? "",
    tes: params.get("tes") ?? "",
    document_type: params.get("document_type") ?? "",
    status: params.get("status") ?? "",
    situation: params.get("situation") ?? "",
    q: params.get("q") ?? "",
    day: params.get("day") ?? "",
  };
}

export function entryAuditDetailFiltersKey(params: URLSearchParams): string {
  return JSON.stringify(entryAuditDetailFiltersFromSearch(params));
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
  // H5 / AC-KPI-4: mesma ordem canônica do hero (NF-e antes de CT-e).
  return formatDocumentTypesJoined(types) || "—";
}

/**
 * Abrevia chave de acesso (tipicamente 44 dígitos) para caber na tabela —
 * valor completo no title. Não aplica a datas/textos curtos de negócio.
 */
export function abbreviateAccessKey(
  value: string | null | undefined,
): { short: string; full: string } | null {
  const full = (value ?? "").trim();
  if (!full) return null;
  const digits = full.replace(/\D/g, "");
  const looksLikeAccessKey = digits.length >= 20 && digits.length / full.length >= 0.8;
  if (!looksLikeAccessKey) return null;
  if (full.length <= 16) return { short: full, full };
  return { short: `${full.slice(0, 6)}…${full.slice(-4)}`, full };
}

/** Preferir nome curto das options; fallback «Filial {code}». */
export function formatBranchLabel(
  code: string,
  options?: Array<{ code: string; name?: string | null; state?: string | null }>,
): string {
  const match = options?.find((option) => option.code === code);
  const state = match?.state?.trim();
  // U12 E3: rótulo pelo código (razão social só no title/ajuda).
  return state ? `Filial ${code} · ${state}` : `Filial ${code}`;
}

export function formatBranchTitle(
  code: string,
  options?: Array<{ code: string; name?: string | null }>,
): string {
  const match = options?.find((option) => option.code === code);
  const name = match?.name?.trim();
  return name || `Filial ${code}`;
}

export function formatBranches(
  codes: string[],
  options?: Array<{ code: string; name?: string | null; state?: string | null }>,
): string {
  if (!codes.length) return "—";
  if (codes.length === 1) return formatBranchLabel(codes[0], options);
  if (codes.length === 2) {
    return `Filiais ${codes[0]} e ${codes[1]}`;
  }
  return `Filiais ${codes.join(", ")}`;
}

/** Escopo do hero da análise: «Filiais 01 (SC) e 02 (ES) · NF-e e CT-e» (AC-KPI-4). */
export function formatAnalysisScope(
  branches: string[],
  documentTypes: string[],
  options?: Array<{ code: string; name?: string | null; state?: string | null }>,
): string {
  const branchPart = formatBranchesWithState(branches, options);
  const typesPart = formatDocumentTypesJoined(documentTypes);
  return [branchPart, typesPart].filter(Boolean).join(" · ");
}

function formatBranchesWithState(
  codes: string[],
  options?: Array<{ code: string; name?: string | null; state?: string | null }>,
): string {
  if (!codes.length) return "";
  const parts = codes.map((code) => {
    const state = options?.find((option) => option.code === code)?.state?.trim();
    return state ? `${code} (${state})` : code;
  });
  if (parts.length === 1) return `Filial ${parts[0]}`;
  if (parts.length === 2) return `Filiais ${parts[0]} e ${parts[1]}`;
  const head = parts.slice(0, -1).join(", ");
  return `Filiais ${head} e ${parts[parts.length - 1]}`;
}

/** Ordem canônica BFF (`DOCUMENT_TYPES`) — NF-e antes de CT-e (AC-KPI-4). */
const DOCUMENT_TYPE_ORDER = ["nfe", "cte"] as const;

function sortDocumentTypesCanonical(types: string[]): string[] {
  const rank = new Map(
    DOCUMENT_TYPE_ORDER.map((code, index) => [code, index]),
  );
  return [...types].sort((a, b) => {
    const ra = rank.get(a.toLowerCase() as (typeof DOCUMENT_TYPE_ORDER)[number]);
    const rb = rank.get(b.toLowerCase() as (typeof DOCUMENT_TYPE_ORDER)[number]);
    if (ra !== undefined && rb !== undefined) return ra - rb;
    if (ra !== undefined) return -1;
    if (rb !== undefined) return 1;
    return a.localeCompare(b, "pt-BR");
  });
}

function formatDocumentTypesJoined(types: string[]): string {
  if (!types.length) return "";
  const labels = sortDocumentTypesCanonical(types).map(formatDocumentType);
  if (labels.length === 1) return labels[0];
  if (labels.length === 2) return `${labels[0]} e ${labels[1]}`;
  return `${labels.slice(0, -1).join(", ")} e ${labels[labels.length - 1]}`;
}

export function formatMoneyBRL(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

/**
 * Valor de KPI monetário (AC-KPI-1 / U15R R2): compactar conforme o espaço —
 * ≥ 1 mi → «R$ 1,06 mi»; ≥ 1 mil → «R$ 136,1 mil»; abaixo → R$ completo.
 * `title` sempre guarda o valor completo; nunca reticências no display.
 */
export function formatMoneyBRLForKpi(value: number | null | undefined): {
  display: string;
  title: string;
} {
  const full = formatMoneyBRL(value);
  if (value === null || value === undefined || Number.isNaN(value)) {
    return { display: full, title: full };
  }
  const abs = Math.abs(value);
  if (abs >= 1_000_000) {
    const millions = value / 1_000_000;
    const compact = millions.toLocaleString("pt-BR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return { display: `R$ ${compact} mi`, title: full };
  }
  if (abs >= 1_000) {
    const thousands = value / 1_000;
    const compact = thousands.toLocaleString("pt-BR", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
    return { display: `R$ ${compact} mil`, title: full };
  }
  return { display: full, title: full };
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
  if (field && entryAuditFieldKind({ field }) === "percent") {
    return formatEntryAuditFieldValue(value, "percent");
  }
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

/* ------------------------------------------------------------------ */
/* Campos das regras — rótulo PT + tipo de valor (U12 W3)              */
/* ------------------------------------------------------------------ */

export type EntryAuditFieldKind = "money" | "percent" | "date" | "text";

type FieldCatalogEntry = { label: string; kind: EntryAuditFieldKind };

/**
 * Catálogo de campos conferidos pelas regras (domain/entry_audit/engine.py).
 * Chave = código gravado pela API (`FIELD_CODES` em application/entry_audit/vocabulary.py)
 * ou código canônico equivalente quando a API ainda grava o rótulo literal.
 */
export const ENTRY_AUDIT_FIELD_CATALOG: Readonly<
  Record<string, FieldCatalogEntry>
> = {
  total: { label: "Valor total da nota", kind: "money" },
  goods: { label: "Valor das mercadorias", kind: "money" },
  st: { label: "ICMS ST", kind: "money" },
  discount: { label: "Desconto", kind: "money" },
  series: { label: "Série", kind: "text" },
  icms: { label: "ICMS", kind: "money" },
  base: { label: "Base de ICMS", kind: "money" },
  ipi: { label: "IPI", kind: "money" },
  simple_rate: { label: "Alíquota de crédito do Simples", kind: "percent" },
  amount: { label: "Valor do item", kind: "money" },
  cfop: { label: "CFOP", kind: "text" },
  taker: { label: "Tomador do frete", kind: "text" },
  rate: { label: "Alíquota de ICMS", kind: "percent" },
  cst: { label: "CST", kind: "text" },
  key: { label: "Chave de acesso", kind: "text" },
  species: { label: "Espécie", kind: "text" },
  number: { label: "Número do documento", kind: "text" },
  supplier: { label: "CNPJ do fornecedor", kind: "text" },
  origin: { label: "Origem da mercadoria", kind: "text" },
  freight: { label: "Frete", kind: "money" },
  expense: { label: "Despesas", kind: "money" },
  insurance: { label: "Seguro", kind: "money" },
  book_icms: { label: "ICMS do livro fiscal", kind: "money" },
  /* Rótulos que a API hoje grava como «field» (sem código próprio). */
  tes: { label: "TES", kind: "text" },
  issue_date: { label: "Data de emissão", kind: "date" },
  ipi_base: { label: "Base de IPI", kind: "money" },
  other_expense: { label: "Outras despesas", kind: "money" },
};

/** Rótulos literais do motor/Protheus → código canônico do catálogo. */
const FIELD_LABEL_ALIASES: Readonly<Record<string, string>> = {
  "vlr total": "total",
  "vlr mercadorias": "goods",
  "icms st": "st",
  desconto: "discount",
  série: "series",
  serie: "series",
  "base icms": "base",
  "pcredsn (%)": "simple_rate",
  "vlr item": "amount",
  tomador: "taker",
  "alíq. icms": "rate",
  chave: "key",
  espécie: "species",
  especie: "species",
  número: "number",
  numero: "number",
  cnpj: "supplier",
  "cst (origem)": "origin",
  despesa: "expense",
  "icms livro": "book_icms",
  emissão: "issue_date",
  emissao: "issue_date",
  "base ipi": "ipi_base",
  "outras despesas": "other_expense",
};

export const ENTRY_AUDIT_UNKNOWN_FIELD_LABEL = "Campo não identificado";

export type EntryAuditFieldSource = {
  field?: string | null;
  field_label?: string | null;
  stable_key?: string | null;
};

function catalogCodeFor(raw: string | null | undefined): string | null {
  const text = (raw ?? "").trim();
  if (!text) return null;
  const lower = text.toLowerCase();
  if (lower in ENTRY_AUDIT_FIELD_CATALOG) return lower;
  return FIELD_LABEL_ALIASES[lower] ?? null;
}

/** Código de campo embutido na `stable_key` (`…|rule_id|<campo>|item`). */
function fieldFromStableKey(stableKey: string | null | undefined): string | null {
  const parts = (stableKey ?? "").split("|");
  const index = parts[1]?.startsWith("doc:") ? 6 : 3;
  return parts.length > index + 1 ? parts[index] || null : null;
}

/** Resolve o campo da ocorrência para o catálogo (código → rótulo → stable_key). */
export function resolveEntryAuditField(
  source: EntryAuditFieldSource,
): FieldCatalogEntry | null {
  const code =
    catalogCodeFor(source.field) ??
    catalogCodeFor(fieldFromStableKey(source.stable_key)) ??
    catalogCodeFor(source.field_label);
  return code ? ENTRY_AUDIT_FIELD_CATALOG[code] : null;
}

/** Rótulo PT do campo — nunca devolve códigos técnicos como «field». */
export function entryAuditFieldLabel(source: EntryAuditFieldSource): string {
  const entry = resolveEntryAuditField(source);
  if (entry) return entry.label;
  const apiLabel = (source.field_label ?? "").trim();
  if (apiLabel && apiLabel.toLowerCase() !== "field") return apiLabel;
  return ENTRY_AUDIT_UNKNOWN_FIELD_LABEL;
}

export function entryAuditFieldKind(
  source: EntryAuditFieldSource,
): EntryAuditFieldKind {
  return resolveEntryAuditField(source)?.kind ?? "text";
}

function parseDecimal(value: string | number): number | null {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const text = value.trim();
  if (/^-?\d+(\.\d+)?$/.test(text)) return Number(text);
  if (/^-?\d{1,3}(\.\d{3})*,\d+$/.test(text) || /^-?\d+,\d+$/.test(text)) {
    return Number(text.replace(/\./g, "").replace(",", "."));
  }
  return null;
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`;
}

function formatDateValue(value: string): string {
  const text = value.trim();
  const iso = /^(\d{4})-(\d{2})-(\d{2})(?:[T ].*)?$/.exec(text);
  if (iso) return `${iso[3]}/${iso[2]}/${iso[1]}`;
  return text;
}

/** Formata valor Protheus/XML conforme o tipo do campo (R$, %, dd/mm/aaaa, texto). */
export function formatEntryAuditFieldValue(
  value: string | number | null | undefined,
  kind: EntryAuditFieldKind,
): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string" && !value.trim()) return "—";
  if (kind === "money" || kind === "percent") {
    const parsed = parseDecimal(value);
    if (parsed === null) return String(value).trim();
    return kind === "money" ? formatMoneyBRL(parsed) : formatPercent(parsed);
  }
  if (kind === "date") return formatDateValue(String(value));
  return String(value).trim();
}

export function formatOccurrenceValue(
  value: string | number | null | undefined,
  source: EntryAuditFieldSource,
): string {
  return formatEntryAuditFieldValue(value, entryAuditFieldKind(source));
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

/** Eixo do gráfico diário — `dd/mm` a partir de ISO `YYYY-MM-DD`. */
export function formatEntryAuditChartDay(isoDate: string): string {
  const text = isoDate.trim();
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  if (match) return `${match[3]}/${match[2]}`;
  const parsed = new Date(`${text}T12:00:00`);
  if (!Number.isNaN(parsed.getTime())) {
    return parsed.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
    });
  }
  return text;
}

function parseIsoDateOnly(iso: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso.trim());
  if (!match) return null;
  const date = new Date(
    Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])),
  );
  return Number.isNaN(date.getTime()) ? null : date;
}

function addUtcDays(iso: string, delta: number): string {
  const base = parseIsoDateOnly(iso);
  if (!base) return iso;
  base.setUTCDate(base.getUTCDate() + delta);
  return base.toISOString().slice(0, 10);
}

function inclusiveDaySpan(dateFrom: string, dateTo: string): number {
  const from = parseIsoDateOnly(dateFrom);
  const to = parseIsoDateOnly(dateTo);
  if (!from || !to) return 1;
  const diff = Math.round((to.getTime() - from.getTime()) / 86_400_000);
  return Math.max(1, diff + 1);
}

/** Janela imediatamente anterior com o mesmo número de dias (regra da BFF). */
export function entryAuditPreviousPeriodRange(
  dateFrom: string,
  dateTo: string,
): [string, string] | null {
  if (!parseIsoDateOnly(dateFrom) || !parseIsoDateOnly(dateTo)) return null;
  const span = inclusiveDaySpan(dateFrom, dateTo);
  const previousTo = addUtcDays(dateFrom, -1);
  const previousFrom = addUtcDays(previousTo, -(span - 1));
  return [previousFrom, previousTo];
}

export function entryAuditPreviousPeriodLabel(
  dateFrom: string,
  dateTo: string,
): string | null {
  const range = entryAuditPreviousPeriodRange(dateFrom, dateTo);
  if (!range) return null;
  return formatPeriodLabel(range[0], range[1]);
}

export type EntryAuditDailyChartPoint = {
  /** Rótulo do eixo (`dd/mm`). */
  name: string;
  /** Data ISO do período atual (filtro `day`). */
  day: string;
  current: number;
  previous?: number;
  /** Data ISO do dia alinhado no período anterior (tooltip). */
  previousDay?: string;
};

/** Lista ISO YYYY-MM-DD inclusiva (AC-GRA-3: dia sem ocorrência = 0). */
export function enumerateIsoDateRange(
  dateFrom: string,
  dateTo: string,
): string[] {
  const start = Date.parse(`${dateFrom}T00:00:00Z`);
  const end = Date.parse(`${dateTo}T00:00:00Z`);
  if (!Number.isFinite(start) || !Number.isFinite(end) || start > end) {
    return [];
  }
  const days: string[] = [];
  for (let cursor = start; cursor <= end; cursor += 86_400_000) {
    days.push(new Date(cursor).toISOString().slice(0, 10));
  }
  return days;
}

/**
 * Preenche todos os dias do período com count 0 quando ausentes (AC-GRA-3).
 * Sem `dateFrom`/`dateTo`, devolve a série ordenada como veio.
 */
export function fillEntryAuditDailySeries(
  series: ReadonlyArray<{ name: string; count: number }>,
  dateFrom?: string | null,
  dateTo?: string | null,
): Array<{ name: string; count: number }> {
  const byDay = new Map(
    series
      .filter((item) => /^\d{4}-\d{2}-\d{2}$/.test(item.name))
      .map((item) => [item.name, item.count]),
  );
  if (dateFrom && dateTo) {
    const range = enumerateIsoDateRange(dateFrom, dateTo);
    if (range.length) {
      return range.map((day) => ({ name: day, count: byDay.get(day) ?? 0 }));
    }
  }
  return [...series]
    .filter((item) => /^\d{4}-\d{2}-\d{2}$/.test(item.name))
    .sort((a, b) => a.name.localeCompare(b.name));
}

/**
 * Alinha série anterior pela posição do dia (dia 1 com dia 1), não pela data ISO.
 * Sem série anterior → só `current`. Com período, preenche dias ausentes com 0.
 */
export function alignEntryAuditDailySeries(
  series: ReadonlyArray<{ name: string; count: number }>,
  previous: ReadonlyArray<{ name: string; count: number }> | null | undefined,
  period?: { dateFrom: string; dateTo: string } | null,
): EntryAuditDailyChartPoint[] {
  const sortedCurrent = fillEntryAuditDailySeries(
    series,
    period?.dateFrom,
    period?.dateTo,
  );
  // Anterior: preencher o período anterior espelho (mesmo nº de dias) e alinhar
  // por índice de dia (dia 1↔dia 1), não pela data ISO (AC-GRA-3 / OC-1).
  const previousRange =
    period?.dateFrom && period?.dateTo
      ? entryAuditPreviousPeriodRange(period.dateFrom, period.dateTo)
      : null;
  const sortedPrevious = previousRange
    ? fillEntryAuditDailySeries(previous ?? [], previousRange[0], previousRange[1])
    : [...(previous ?? [])]
        .filter((item) => /^\d{4}-\d{2}-\d{2}$/.test(item.name))
        .sort((a, b) => a.name.localeCompare(b.name));
  const hasPrevious = Boolean(previous?.length) || Boolean(previousRange);

  return sortedCurrent.map((item, index) => {
    const aligned = hasPrevious ? sortedPrevious[index] : undefined;
    const point: EntryAuditDailyChartPoint = {
      name: formatEntryAuditChartDay(item.name),
      day: item.name,
      current: item.count,
    };
    if (hasPrevious && aligned) {
      point.previous = aligned.count;
      point.previousDay = aligned.name;
    } else if (hasPrevious) {
      point.previous = 0;
    }
    return point;
  });
}

export function entryAuditDailyPointAriaLabel(
  point: EntryAuditDailyChartPoint,
  includePrevious: boolean,
): string {
  const current = `${point.name}: ${point.current.toLocaleString("pt-BR")}`;
  if (!includePrevious || point.previous == null) return current;
  const prevDay = point.previousDay
    ? formatEntryAuditChartDay(point.previousDay)
    : "—";
  const prevCount = point.previous.toLocaleString("pt-BR");
  return `${current} · anterior ${prevDay}: ${prevCount}`;
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
