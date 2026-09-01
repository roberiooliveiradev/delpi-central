export type SettingsAdminTab = "overview" | "catalog" | "goals" | "system";

export type CatalogAdminView = "structure" | "validation";

export type CatalogAdminAction = "new-indicator" | "new-department";

export type GoalsAdminAction = "new-year";

const TAB_ALIASES: Record<string, SettingsAdminTab> = {
  overview: "overview",
  inicio: "overview",
  painel: "overview",
  catalog: "catalog",
  catalogo: "catalog",
  departments: "catalog",
  goals: "goals",
  metas: "goals",
  system: "system",
  sistema: "system",
  global: "system",
  audit: "system",
};

const VIEW_ALIASES: Record<string, CatalogAdminView> = {
  structure: "structure",
  estrutura: "structure",
  validation: "validation",
  validacao: "validation",
};

const CATALOG_ACTION_ALIASES: Record<string, CatalogAdminAction> = {
  "new-indicator": "new-indicator",
  "novo-indicador": "new-indicator",
  "new-department": "new-department",
  "novo-departamento": "new-department",
};

const GOALS_ACTION_ALIASES: Record<string, GoalsAdminAction> = {
  "new-year": "new-year",
  "novo-ano": "new-year",
};

export function parseCatalogAdminAction(
  raw: string | null | undefined,
): CatalogAdminAction | null {
  const key = (raw ?? "").trim().toLowerCase();
  if (!key) return null;
  return CATALOG_ACTION_ALIASES[key] ?? null;
}

export function parseGoalsAdminAction(
  raw: string | null | undefined,
): GoalsAdminAction | null {
  const key = (raw ?? "").trim().toLowerCase();
  if (!key) return null;
  return GOALS_ACTION_ALIASES[key] ?? null;
}

export function parseSettingsAdminTab(raw: string | null | undefined): SettingsAdminTab {
  const key = (raw ?? "").trim().toLowerCase();
  if (!key) return "overview";
  return TAB_ALIASES[key] ?? "overview";
}

export function parseCatalogAdminView(raw: string | null | undefined): CatalogAdminView {
  const key = (raw ?? "").trim().toLowerCase();
  if (!key) return "structure";
  return VIEW_ALIASES[key] ?? "structure";
}

export function readSettingsAdminRoute(): {
  tab: SettingsAdminTab;
  catalogView: CatalogAdminView;
  catalogAction: CatalogAdminAction | null;
  goalsAction: GoalsAdminAction | null;
} {
  if (typeof window === "undefined") {
    return {
      tab: "overview",
      catalogView: "structure",
      catalogAction: null,
      goalsAction: null,
    };
  }

  const params = new URLSearchParams(window.location.search);
  const tab = parseSettingsAdminTab(params.get("tab"));
  const actionRaw = params.get("action");

  return {
    tab,
    catalogView: parseCatalogAdminView(params.get("view") ?? params.get("sub")),
    catalogAction: tab === "catalog" ? parseCatalogAdminAction(actionRaw) : null,
    goalsAction: tab === "goals" ? parseGoalsAdminAction(actionRaw) : null,
  };
}

export type SettingsAdminRouteOptions = {
  catalogAction?: CatalogAdminAction | null;
  goalsAction?: GoalsAdminAction | null;
};

export function writeSettingsAdminRoute(
  tab: SettingsAdminTab,
  catalogView: CatalogAdminView = "structure",
  options: SettingsAdminRouteOptions = {},
): void {
  if (typeof window === "undefined") return;

  const params = new URLSearchParams();
  if (tab !== "overview") {
    params.set("tab", tab);
  }
  if (tab === "catalog" && catalogView !== "structure") {
    params.set("view", catalogView);
  }

  const action =
    tab === "catalog"
      ? options.catalogAction ?? null
      : tab === "goals"
        ? options.goalsAction ?? null
        : null;
  if (action) {
    params.set("action", action);
  }

  const query = params.toString();
  const nextUrl = query
    ? `${window.location.pathname}?${query}`
    : window.location.pathname;

  if (nextUrl !== `${window.location.pathname}${window.location.search}`) {
    window.history.replaceState(null, "", nextUrl);
  }
}
