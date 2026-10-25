/** Base path canônico do plugin (manifest / Portal). */
export const CONTROLLERSHIP_FINANCE_BASE_PATH = "/apps/controllership-finance";

/**
 * Rotas implementadas:
 * - `home` — hub da Central de Fechamento.
 * - `financial_settlements` — baixas financeiras R01/R02 (closing).
 * - `stock_inventory` — estoque histórico R03/P7 (closing).
 * - `pendencies` — fila de pendências e classificações (P4).
 * Rotas futuras (Visão geral, Sala de interação, Minhas tarefas,
 * Administração, Ajuda) entram aqui apenas quando implementadas.
 */
export type PluginView =
  | "home"
  | "financial_settlements"
  | "stock_inventory"
  | "checklist"
  | "checklist_admin"
  | "pendencies"
  | "not_found";

export type PluginNavId = "home";

export type PluginNavigationTarget =
  | "home"
  | "financial_settlements"
  | "stock_inventory"
  | "checklist"
  | "checklist_admin"
  | "pendencies";

/** Mapa rota relativa → view (paths técnicos em inglês, kebab-case). */
const RELATIVE_TO_VIEW: Record<string, PluginView> = {
  "closing/financial-settlements": "financial_settlements",
  "closing/stock-inventory": "stock_inventory",
  "closing/checklist": "checklist",
  "closing/admin": "checklist_admin",
  "closing/pendencies": "pendencies",
};

const VIEW_TO_RELATIVE: Record<Exclude<PluginNavigationTarget, "home">, string> = {
  financial_settlements: "closing/financial-settlements",
  stock_inventory: "closing/stock-inventory",
  checklist: "closing/checklist",
  checklist_admin: "closing/admin",
  pendencies: "closing/pendencies",
};

const CHECKLIST_PERIOD_PATTERN = /^closing\/checklist\/(\d{4}-(0[1-9]|1[0-2]))$/;

export type ResolvedPluginRoute = {
  view: PluginView;
  pathname: string;
  relativePath: string;
  /** Competência YYYY-MM quando a deep route é `closing/checklist/{period}`. */
  checklistPeriod?: string;
};

export function normalizePathname(pathname: string): string {
  const raw = (pathname || "").trim() || "/";
  const withoutQuery = raw.split("?")[0]?.split("#")[0] ?? raw;
  if (withoutQuery.length > 1 && withoutQuery.endsWith("/")) {
    return withoutQuery.slice(0, -1);
  }
  return withoutQuery || "/";
}

export function normalizeBasePath(basePath?: string): string {
  return normalizePathname(basePath?.trim() || CONTROLLERSHIP_FINANCE_BASE_PATH);
}

export function resolvePluginRoute(
  pathname: string | undefined,
  basePath?: string,
): ResolvedPluginRoute {
  const base = normalizeBasePath(basePath);
  const path = normalizePathname(pathname ?? base);

  if (path === base) {
    return { view: "home", pathname: path, relativePath: "" };
  }

  const relativePath = path.startsWith(`${base}/`)
    ? path.slice(base.length + 1)
    : path.slice(base.length);
  const periodMatch = CHECKLIST_PERIOD_PATTERN.exec(relativePath);
  const view = periodMatch
    ? "checklist"
    : RELATIVE_TO_VIEW[relativePath] ?? "not_found";

  return {
    view,
    pathname: path,
    relativePath,
    checklistPeriod: periodMatch?.[1],
  };
}

/** Path canônico da view (paths só via buildPluginPath — sem URL absoluta). */
export function buildPluginPath(
  view: PluginNavigationTarget,
  basePath?: string,
  search?: string,
): string {
  const base = normalizeBasePath(basePath);
  const suffix = view === "home" ? "" : `/${VIEW_TO_RELATIVE[view]}`;
  const normalizedSearch = search?.startsWith("?")
    ? search
    : search
      ? `?${search}`
      : "";
  return `${base}${suffix}${normalizedSearch}`;
}

export function resolveActiveNavId(view: PluginView): PluginNavId | null {
  if (view === "home") return "home";
  return null;
}
