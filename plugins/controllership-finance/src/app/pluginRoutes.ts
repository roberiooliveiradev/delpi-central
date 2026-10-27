/** Base path canônico do plugin (manifest / Portal). */
export const CONTROLLERSHIP_FINANCE_BASE_PATH = "/apps/controllership-finance";

/**
 * Rotas implementadas:
 * - `home` — hub da Central de Fechamento.
 * - `financial_settlements` — baixas financeiras R01/R02 (closing).
 * - `stock_inventory` — estoque histórico R03/P7 (closing).
 * - `pendencies` — fila de pendências e classificações (P4).
 * - `packages` — pacotes por destinatário, submissão e revisão (P5).
 * - `cockpit` — estado consolidado P2/P3/P4/P5 da competência.
 * - `monthly_closing` — workspace «Fechamento mensal» (3 abas, doc 112).
 * - `my_tasks` — projeção self-only de pendências/revisões (P4/P5).
 * - `profile` — dados corporativos do próprio usuário (Core).
 * - `catalogs_admin` — catálogos governados P6 (MANAGE).
 * Rotas futuras (Visão geral dedicada, Sala de interação, Ajuda)
 * entram aqui apenas quando implementadas.
 */
export type PluginView =
  | "home"
  | "financial_settlements"
  | "stock_inventory"
  | "checklist"
  | "checklist_admin"
  | "catalogs_admin"
  | "pendencies"
  | "packages"
  | "cockpit"
  | "monthly_closing"
  | "my_tasks"
  | "profile"
  | "clara_consent"
  | "not_found";

export type PluginNavId = "home" | "my_tasks";

export type PluginNavigationTarget =
  | "home"
  | "financial_settlements"
  | "stock_inventory"
  | "checklist"
  | "checklist_admin"
  | "catalogs_admin"
  | "pendencies"
  | "packages"
  | "cockpit"
  | "monthly_closing"
  | "my_tasks"
  | "profile";

/** Mapa rota relativa → view (paths técnicos em inglês, kebab-case). */
const RELATIVE_TO_VIEW: Record<string, PluginView> = {
  "closing/financial-settlements": "financial_settlements",
  "closing/stock-inventory": "stock_inventory",
  "closing/checklist": "checklist",
  "closing/admin": "checklist_admin",
  "closing/pendencies": "pendencies",
  "closing/packages": "packages",
  "closing/cockpit": "cockpit",
  "closing/monthly-closing": "monthly_closing",
  "closing/my-tasks": "my_tasks",
  "closing/admin/catalogs": "catalogs_admin",
  "closing/clara-consent": "clara_consent",
  "profile": "profile",
};

const VIEW_TO_RELATIVE: Record<Exclude<PluginNavigationTarget, "home">, string> = {
  financial_settlements: "closing/financial-settlements",
  stock_inventory: "closing/stock-inventory",
  checklist: "closing/checklist",
  checklist_admin: "closing/admin",
  pendencies: "closing/pendencies",
  packages: "closing/packages",
  cockpit: "closing/cockpit",
  monthly_closing: "closing/monthly-closing",
  my_tasks: "closing/my-tasks",
  catalogs_admin: "closing/admin/catalogs",
  profile: "profile",
};

const PERIOD_DEEP_ROUTE_PATTERN =
  /^closing\/(checklist|packages|cockpit|monthly-closing)\/(\d{4}-(0[1-9]|1[0-2]))$/;

const DEEP_ROUTE_VIEWS: Record<string, PluginView> = {
  checklist: "checklist",
  packages: "packages",
  cockpit: "cockpit",
  "monthly-closing": "monthly_closing",
};

/** Detalhe de documento da aba Documentos — deep route contextual (não é aba). */
const DOCUMENT_DETAIL_PATTERN =
  /^closing\/monthly-closing\/(\d{4}-(0[1-9]|1[0-2]))\/documents\/([A-Za-z0-9_.:%~-]+)$/;

/** Página contextual de relatório da aba Relatórios (UX-011) — deep route. */
const REPORT_DETAIL_PATTERN =
  /^closing\/monthly-closing\/(\d{4}-(0[1-9]|1[0-2]))\/reports\/([A-Za-z0-9-]+)$/;

export type ResolvedPluginRoute = {
  view: PluginView;
  pathname: string;
  relativePath: string;
  /** Competência YYYY-MM quando a deep route é `closing/{view}/{period}`. */
  checklistPeriod?: string;
  /** Referência do documento na rota de detalhe (UUID, `item:{key}` ou `new`). */
  documentRef?: string;
  /** Chave do relatório na rota contextual (`financial-settlements`, `stock-inventory`). */
  reportKey?: string;
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
  const documentMatch = DOCUMENT_DETAIL_PATTERN.exec(relativePath);
  if (documentMatch) {
    return {
      view: "monthly_closing",
      pathname: path,
      relativePath,
      checklistPeriod: documentMatch[1],
      documentRef: decodeURIComponent(documentMatch[3] ?? ""),
    };
  }
  const reportMatch = REPORT_DETAIL_PATTERN.exec(relativePath);
  if (reportMatch) {
    return {
      view: "monthly_closing",
      pathname: path,
      relativePath,
      checklistPeriod: reportMatch[1],
      reportKey: reportMatch[3],
    };
  }
  const periodMatch = PERIOD_DEEP_ROUTE_PATTERN.exec(relativePath);
  const view = periodMatch
    ? DEEP_ROUTE_VIEWS[periodMatch[1] ?? ""] ?? "not_found"
    : RELATIVE_TO_VIEW[relativePath] ?? "not_found";

  return {
    view,
    pathname: path,
    relativePath,
    checklistPeriod: periodMatch?.[2],
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
  if (view === "my_tasks") return "my_tasks";
  return null;
}
