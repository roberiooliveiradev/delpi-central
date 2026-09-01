export type SettingsAdminTab = "overview" | "catalog" | "goals" | "system";

export type CatalogAdminView = "structure" | "validation";

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
} {
  if (typeof window === "undefined") {
    return { tab: "overview", catalogView: "structure" };
  }

  const params = new URLSearchParams(window.location.search);
  return {
    tab: parseSettingsAdminTab(params.get("tab")),
    catalogView: parseCatalogAdminView(params.get("view") ?? params.get("sub")),
  };
}

export function writeSettingsAdminRoute(
  tab: SettingsAdminTab,
  catalogView: CatalogAdminView = "structure",
): void {
  if (typeof window === "undefined") return;

  const params = new URLSearchParams();
  if (tab !== "overview") {
    params.set("tab", tab);
  }
  if (tab === "catalog" && catalogView !== "structure") {
    params.set("view", catalogView);
  }

  const query = params.toString();
  const nextUrl = query
    ? `${window.location.pathname}?${query}`
    : window.location.pathname;

  if (nextUrl !== `${window.location.pathname}${window.location.search}`) {
    window.history.replaceState(null, "", nextUrl);
  }
}
