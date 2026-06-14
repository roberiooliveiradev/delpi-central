export const PROPOSTAS_COMERCIAIS_ROUTES = {
  home: "/apps/propostas-comerciais",
  detail: (propostaInterna: string) =>
    `/apps/propostas-comerciais/${encodeURIComponent(propostaInterna.trim())}`,
} as const;

export type PropostasComerciaisView = "list" | "detail";

export type ParsedPropostasComerciaisRoute = {
  view: PropostasComerciaisView;
  propostaInterna?: string;
};

export function normalizePropostasComerciaisPath(pathname: string): string {
  if (!pathname) return PROPOSTAS_COMERCIAIS_ROUTES.home;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function parsePropostasComerciaisPath(pathname: string): ParsedPropostasComerciaisRoute {
  const path = normalizePropostasComerciaisPath(pathname);

  if (path === PROPOSTAS_COMERCIAIS_ROUTES.home) {
    return { view: "list" };
  }

  const detailMatch = path.match(/^\/apps\/propostas-comerciais\/([^/]+)$/);
  if (detailMatch) {
    return {
      view: "detail",
      propostaInterna: decodeURIComponent(detailMatch[1]),
    };
  }

  return { view: "list" };
}

export function resolvePropostasComerciaisRouteKey(pathname?: string): string {
  const route = parsePropostasComerciaisPath(normalizePropostasComerciaisPath(pathname ?? ""));
  if (route.view === "detail") {
    return `detail:${route.propostaInterna ?? ""}`;
  }
  return "list";
}
