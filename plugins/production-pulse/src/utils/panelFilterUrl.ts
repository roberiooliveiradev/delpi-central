import { PRODUCTION_PULSE_BASE_PATH } from "../constants/routes";

export type PanelViewMode = "list" | "grouped";
export type PanelGroupBy = "work_center" | "machine" | "equipment" | "area";
export type PanelStatusFilter = "" | "online" | "offline" | "no_binding" | "disabled";
export type PanelAnchorTypeFilter =
  | ""
  | "work_center"
  | "machine"
  | "equipment"
  | "area"
  | "standalone";

export type PanelFilters = {
  branch: string;
  anchorType: PanelAnchorTypeFilter;
  role: string;
  status: PanelStatusFilter;
  search: string;
  view: PanelViewMode;
  groupBy: PanelGroupBy;
  page: number;
};

export const DEFAULT_PANEL_FILTERS: PanelFilters = {
  branch: "01",
  anchorType: "",
  role: "",
  status: "",
  search: "",
  view: "list",
  groupBy: "work_center",
  page: 1,
};

const GROUP_BY_VALUES = new Set<PanelGroupBy>([
  "work_center",
  "machine",
  "equipment",
  "area",
]);

const ANCHOR_TYPE_VALUES = new Set<PanelAnchorTypeFilter>([
  "",
  "work_center",
  "machine",
  "equipment",
  "area",
  "standalone",
]);

const STATUS_VALUES = new Set<PanelStatusFilter>([
  "",
  "online",
  "offline",
  "no_binding",
  "disabled",
]);

function parseSearch(search: string): URLSearchParams {
  const raw = search.startsWith("?") ? search.slice(1) : search;
  return new URLSearchParams(raw);
}

export function readPanelFilters(search: string): PanelFilters {
  const query = parseSearch(search);
  const view = query.get("view") === "grouped" ? "grouped" : "list";
  const groupByRaw = query.get("groupBy") ?? DEFAULT_PANEL_FILTERS.groupBy;
  const groupBy = GROUP_BY_VALUES.has(groupByRaw as PanelGroupBy)
    ? (groupByRaw as PanelGroupBy)
    : DEFAULT_PANEL_FILTERS.groupBy;
  const anchorTypeRaw = query.get("anchorType") ?? "";
  const anchorType = ANCHOR_TYPE_VALUES.has(anchorTypeRaw as PanelAnchorTypeFilter)
    ? (anchorTypeRaw as PanelAnchorTypeFilter)
    : "";
  const statusRaw = query.get("status") ?? "";
  const status = STATUS_VALUES.has(statusRaw as PanelStatusFilter)
    ? (statusRaw as PanelStatusFilter)
    : "";
  const pageRaw = Number.parseInt(query.get("page") ?? "1", 10);

  return {
    branch: query.get("branch") ?? DEFAULT_PANEL_FILTERS.branch,
    anchorType,
    role: query.get("role") ?? "",
    status,
    search: query.get("search") ?? "",
    view,
    groupBy,
    page: Number.isFinite(pageRaw) && pageRaw > 0 ? pageRaw : 1,
  };
}

export function buildPanelSearchParams(filters: PanelFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.branch) params.set("branch", filters.branch);
  if (filters.anchorType) params.set("anchorType", filters.anchorType);
  if (filters.role) params.set("role", filters.role);
  if (filters.status) params.set("status", filters.status);
  if (filters.search.trim()) params.set("search", filters.search.trim());
  if (filters.view !== DEFAULT_PANEL_FILTERS.view) params.set("view", filters.view);
  if (filters.view === "grouped" && filters.groupBy !== DEFAULT_PANEL_FILTERS.groupBy) {
    params.set("groupBy", filters.groupBy);
  }
  if (filters.page > 1) params.set("page", String(filters.page));
  return params;
}

export function buildPanelPath(filters: PanelFilters): string {
  const params = buildPanelSearchParams(filters);
  const suffix = params.toString();
  return suffix ? `${PRODUCTION_PULSE_BASE_PATH}?${suffix}` : PRODUCTION_PULSE_BASE_PATH;
}

export function replacePanelFilters(filters: PanelFilters): void {
  if (typeof window === "undefined") return;
  const target = buildPanelPath(filters);
  const current = `${window.location.pathname}${window.location.search}`;
  if (current === target) return;
  window.history.replaceState({}, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
