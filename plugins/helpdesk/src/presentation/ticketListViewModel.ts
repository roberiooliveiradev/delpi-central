/**
 * Declarative list view model for Meus Chamados.
 *
 * Mirrors the GLPI Search UI shapes (rules/groups, multi-sort, column prefs)
 * so the MFE can grow without rewriting TicketListTable / HelpdeskPage.
 * Mapping to today's flat URL query stays in adapters below — the BFF still
 * speaks the ADDITIVE query of 03-contrato until a dedicated list-query
 * contract ships (H13 / HD-027).
 */

import type { TicketSummary } from "../api/helpdeskApi";
import {
  absoluteDateTimeLabel,
  TICKET_LIST_SORTABLE_COLUMNS,
  type TicketListFilters,
  type TicketListSortKey,
} from "./ticketView";

export type ListFilterCombinator = "and" | "or";

export type ListFilterOperator =
  | "eq"
  | "neq"
  | "contains"
  | "not_contains"
  | "gt"
  | "gte"
  | "lt"
  | "lte"
  | "in"
  | "empty"
  | "not_empty";

/** One criterion — GLPI «+ regra». */
export type TicketListFilterRule = {
  id: string;
  field: TicketListFilterFieldKey;
  operator: ListFilterOperator;
  value: string;
};

/** Nested group — GLPI «+ grupo». */
export type TicketListFilterGroup = {
  id: string;
  combinator: ListFilterCombinator;
  rules: TicketListFilterRule[];
  groups: TicketListFilterGroup[];
};

export type TicketListSortLevel = {
  field: TicketListSortKey | "closed_at";
  direction: "asc" | "desc";
};

export type TicketListViewMode = "table" | "map";

export type TicketListColumnKey =
  | "id"
  | "title"
  | "status"
  | "category"
  | "urgency"
  | "assigned"
  | "created_at"
  | "updated_at"
  | "solved_at"
  | "closed_at"
  | "requester"
  | "entity"
  | "last_editor";

export type TicketListFilterFieldKey =
  | "q"
  | "status"
  | "urgency_id"
  | "category_id"
  | "updated_from"
  | "updated_to"
  | "created_from"
  | "created_to"
  | "solved_from"
  | "solved_to";

export type TicketListColumnDefinition = {
  key: TicketListColumnKey;
  header: string;
  /** Fixed columns cannot be hidden or reordered (GLPI: ID / Título / Entidade). */
  fixed: boolean;
  sortable: boolean;
  /** Available in the solicitante catalog; false = console-only slot reserved. */
  solicitante: boolean;
  defaultVisible: boolean;
};

export type TicketListColumnPreference = {
  key: TicketListColumnKey;
  visible: boolean;
  order: number;
};

/**
 * Full view model the list chrome consumes.
 * Today only a subset is hydrated from the URL; empty slots stay typed.
 */
export type TicketListViewModel = {
  filterRoot: TicketListFilterGroup;
  sorts: TicketListSortLevel[];
  columns: TicketListColumnPreference[];
  viewMode: TicketListViewMode;
  page: number;
  pageSize: number;
  /** Active filter chip labels for the toolbar (e.g. «Filtrado por Status»). */
  activeFilterLabels: string[];
  /** Primary sort chip (e.g. «Ordenado por Última atualização»). */
  primarySortLabel: string;
};

export const TICKET_LIST_COLUMN_CATALOG: readonly TicketListColumnDefinition[] = [
  { key: "id", header: "Chamado", fixed: true, sortable: true, solicitante: true, defaultVisible: true },
  { key: "title", header: "Título", fixed: true, sortable: true, solicitante: true, defaultVisible: true },
  { key: "status", header: "Status", fixed: false, sortable: true, solicitante: true, defaultVisible: true },
  { key: "category", header: "Categoria", fixed: false, sortable: true, solicitante: true, defaultVisible: true },
  { key: "urgency", header: "Urgência", fixed: false, sortable: true, solicitante: true, defaultVisible: true },
  { key: "assigned", header: "Técnico", fixed: false, sortable: false, solicitante: true, defaultVisible: true },
  { key: "created_at", header: "Aberto", fixed: false, sortable: true, solicitante: true, defaultVisible: true },
  { key: "updated_at", header: "Atualizado", fixed: false, sortable: true, solicitante: true, defaultVisible: true },
  { key: "solved_at", header: "Resolvido", fixed: false, sortable: true, solicitante: true, defaultVisible: true },
  { key: "closed_at", header: "Fechado", fixed: false, sortable: false, solicitante: true, defaultVisible: true },
  { key: "requester", header: "Requerente", fixed: false, sortable: false, solicitante: true, defaultVisible: false },
  { key: "entity", header: "Entidade", fixed: false, sortable: false, solicitante: false, defaultVisible: false },
  { key: "last_editor", header: "Última edição por", fixed: false, sortable: false, solicitante: false, defaultVisible: false },
] as const;

const COLUMN_BY_KEY = new Map(TICKET_LIST_COLUMN_CATALOG.map((column) => [column.key, column]));

const SORT_LABELS: Record<string, string> = {
  id: "Chamado",
  title: "Título",
  status: "Status",
  category: "Categoria",
  urgency: "Urgência",
  created_at: "Aberto",
  updated_at: "Última atualização",
  solved_at: "Resolvido",
  closed_at: "Fechado",
};

const STATUS_FILTER_LABELS: Record<string, string> = {
  open: "Abertos",
  in_progress: "Em atendimento",
  pending: "Pendentes",
  approval: "Aguardando aprovação",
  solved: "Solucionados",
  closed: "Fechados",
};

export function defaultTicketListColumnPreferences(): TicketListColumnPreference[] {
  return TICKET_LIST_COLUMN_CATALOG.filter((column) => column.solicitante).map((column, index) => ({
    key: column.key,
    visible: column.defaultVisible,
    order: index,
  }));
}

export function resolveVisibleColumns(
  preferences: TicketListColumnPreference[] = defaultTicketListColumnPreferences(),
): TicketListColumnDefinition[] {
  const byKey = new Map(preferences.map((pref) => [pref.key, pref]));
  return TICKET_LIST_COLUMN_CATALOG.filter((column) => {
    if (!column.solicitante) return false;
    if (column.fixed) return true;
    const pref = byKey.get(column.key);
    return pref ? pref.visible : column.defaultVisible;
  }).sort((left, right) => {
    const leftOrder = byKey.get(left.key)?.order ?? Number.MAX_SAFE_INTEGER;
    const rightOrder = byKey.get(right.key)?.order ?? Number.MAX_SAFE_INTEGER;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    return left.key.localeCompare(right.key);
  });
}

export function emptyFilterGroup(id = "root"): TicketListFilterGroup {
  return { id, combinator: "and", rules: [], groups: [] };
}

/** Adapts today's flat URL filters into the declarative model (no behavior change). */
export function ticketListViewModelFromFilters(
  filters: TicketListFilters,
  columnPreferences: TicketListColumnPreference[] = defaultTicketListColumnPreferences(),
): TicketListViewModel {
  const rules: TicketListFilterRule[] = [];
  const push = (field: TicketListFilterFieldKey, value: string, operator: ListFilterOperator = "eq") => {
    if (!value.trim()) return;
    rules.push({ id: `${field}:${rules.length}`, field, operator, value: value.trim() });
  };
  push("q", filters.q, "contains");
  push("status", filters.status);
  push("urgency_id", filters.urgency_id);
  push("category_id", filters.category_id);
  push("updated_from", filters.updated_from, "gte");
  push("updated_to", filters.updated_to, "lte");
  push("created_from", filters.created_from, "gte");
  push("created_to", filters.created_to, "lte");

  const parsedLevels = parseTicketSortLevels(filters.sort);
  const sorts: TicketListSortLevel[] = parsedLevels;
  const activeFilterLabels: string[] = [];
  if (filters.status.trim()) {
    activeFilterLabels.push(`Status: ${STATUS_FILTER_LABELS[filters.status] ?? filters.status}`);
  }
  if (filters.q.trim()) activeFilterLabels.push("Busca");
  if (filters.urgency_id.trim()) activeFilterLabels.push("Urgência");
  if (filters.category_id.trim()) activeFilterLabels.push("Categoria");
  if (filters.updated_from.trim() || filters.updated_to.trim()) activeFilterLabels.push("Atualizado");
  if (filters.created_from.trim() || filters.created_to.trim()) activeFilterLabels.push("Aberto");

  const primary = sorts[0] ?? { field: "updated_at" as const, direction: "desc" as const };
  const sortLabel =
    sorts.length > 1
      ? `Ordenado por ${SORT_LABELS[primary.field] ?? primary.field} (+${sorts.length - 1})`
      : `Ordenado por ${SORT_LABELS[primary.field] ?? primary.field}`;

  return {
    filterRoot: { id: "root", combinator: "and", rules, groups: [] },
    sorts,
    columns: columnPreferences,
    viewMode: "table",
    page: filters.page,
    pageSize: filters.page_size,
    activeFilterLabels,
    primarySortLabel: sortLabel,
  };
}

export function cellTextForColumn(row: TicketSummary, key: TicketListColumnKey): string {
  switch (key) {
    case "id":
      return String(row.id);
    case "title":
      return row.title;
    case "status":
      return row.status;
    case "category":
      return row.category;
    case "urgency":
      return row.urgency;
    case "assigned":
      return row.assigned_display_name ?? "";
    case "created_at":
      return absoluteDateTimeLabel(row.created_at);
    case "updated_at":
      return absoluteDateTimeLabel(row.updated_at);
    case "solved_at":
      return absoluteDateTimeLabel(row.solved_at ?? "");
    case "closed_at":
      return absoluteDateTimeLabel(row.closed_at ?? "");
    case "requester":
      return "";
    case "entity":
    case "last_editor":
      return "";
    default:
      return "";
  }
}

export function columnDefinition(key: TicketListColumnKey): TicketListColumnDefinition | undefined {
  return COLUMN_BY_KEY.get(key);
}

const FILTER_FIELD_LABELS: Record<TicketListFilterFieldKey, string> = {
  q: "Busca",
  status: "Status",
  urgency_id: "Urgência",
  category_id: "Categoria",
  updated_from: "Atualizado de",
  updated_to: "Atualizado até",
  created_from: "Aberto de",
  created_to: "Aberto até",
  solved_from: "Resolvido de",
  solved_to: "Resolvido até",
};

/** Fields the solicitante builder can send today (flat ADDITIVE BFF query). */
export const TICKET_LIST_BUILDER_FIELDS: readonly {
  key: TicketListFilterFieldKey;
  label: string;
  input: "text" | "status" | "urgency" | "category" | "date";
  operator: ListFilterOperator;
}[] = [
  { key: "q", label: FILTER_FIELD_LABELS.q, input: "text", operator: "contains" },
  { key: "status", label: FILTER_FIELD_LABELS.status, input: "status", operator: "eq" },
  { key: "urgency_id", label: FILTER_FIELD_LABELS.urgency_id, input: "urgency", operator: "eq" },
  { key: "category_id", label: FILTER_FIELD_LABELS.category_id, input: "category", operator: "eq" },
  { key: "updated_from", label: FILTER_FIELD_LABELS.updated_from, input: "date", operator: "gte" },
  { key: "updated_to", label: FILTER_FIELD_LABELS.updated_to, input: "date", operator: "lte" },
  { key: "created_from", label: FILTER_FIELD_LABELS.created_from, input: "date", operator: "gte" },
  { key: "created_to", label: FILTER_FIELD_LABELS.created_to, input: "date", operator: "lte" },
] as const;

export function newFilterRuleId(): string {
  return `rule-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

export function parseTicketSortLevels(sort: string): TicketListSortLevel[] {
  const chunks = String(sort || "updated_at:desc")
    .split(",")
    .map((chunk) => chunk.trim())
    .filter(Boolean)
    .slice(0, 3);
  if (chunks.length === 0) return [{ field: "updated_at", direction: "desc" }];
  const levels: TicketListSortLevel[] = [];
  const seen = new Set<string>();
  for (const chunk of chunks) {
    const [fieldRaw, directionRaw] = chunk.split(":");
    const fieldCandidate = (fieldRaw || "updated_at").trim();
    if (!TICKET_LIST_SORTABLE_COLUMNS.includes(fieldCandidate as TicketListSortKey)) continue;
    const field = fieldCandidate as TicketListSortKey;
    const direction = directionRaw === "asc" ? "asc" : "desc";
    if (seen.has(field)) continue;
    seen.add(field);
    levels.push({ field, direction });
  }
  return levels.length > 0 ? levels : [{ field: "updated_at", direction: "desc" }];
}

export function formatTicketSortLevels(levels: TicketListSortLevel[]): string {
  const cleaned = levels
    .filter((level) => Boolean(level.field))
    .slice(0, 3)
    .map((level) => `${level.field}:${level.direction === "asc" ? "asc" : "desc"}`);
  return cleaned.length > 0 ? cleaned.join(",") : "updated_at:desc";
}

/** Flattens AND rules from the builder into the flat URL filters (OR groups not serialized). */
export function ticketListFiltersFromFilterGroup(
  group: TicketListFilterGroup,
  base: TicketListFilters,
): TicketListFilters {
  const next: TicketListFilters = {
    ...base,
    q: "",
    status: "",
    urgency_id: "",
    category_id: "",
    updated_from: "",
    updated_to: "",
    created_from: "",
    created_to: "",
    page: 1,
  };
  const applyRule = (rule: TicketListFilterRule) => {
    const value = rule.value.trim();
    if (!value) return;
    switch (rule.field) {
      case "q":
        next.q = value;
        break;
      case "status":
        next.status = value;
        break;
      case "urgency_id":
        next.urgency_id = value;
        break;
      case "category_id":
        next.category_id = value;
        break;
      case "updated_from":
        next.updated_from = value;
        break;
      case "updated_to":
        next.updated_to = value;
        break;
      case "created_from":
        next.created_from = value;
        break;
      case "created_to":
        next.created_to = value;
        break;
      default:
        break;
    }
  };
  for (const rule of group.rules) applyRule(rule);
  for (const nested of group.groups) {
    if (nested.combinator !== "and") continue;
    for (const rule of nested.rules) applyRule(rule);
  }
  return next;
}

export function preferencesFromVisibility(
  visibility: Record<string, boolean>,
  order: string[],
): TicketListColumnPreference[] {
  const solicitante = TICKET_LIST_COLUMN_CATALOG.filter((column) => column.solicitante);
  const orderIndex = new Map(order.map((key, index) => [key, index]));
  return solicitante.map((column, index) => ({
    key: column.key,
    visible: column.fixed ? true : visibility[column.key] !== false,
    order: orderIndex.get(column.key) ?? index,
  }));
}
