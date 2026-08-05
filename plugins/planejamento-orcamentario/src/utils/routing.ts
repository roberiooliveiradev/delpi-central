export const BASE_PATH = "/apps/planejamento-orcamentario";

export type AppRoute =
  | "home"
  | "orientacoes"
  | "capex"
  | "capex-investment-new"
  | "capex-investment-edit"
  | "capex-approvals"
  | "capex-approval-detail"
  | "capex-consolidation"
  | "pessoal"
  | "pessoal-approvals"
  | "pessoal-approval-detail"
  | "admin"
  | "admin-exercicios"
  | "admin-orientacoes"
  | "admin-escopos"
  | "admin-responsaveis"
  | "admin-centros-de-custo"
  | "admin-categorias-capex"
  | "unknown";

function relativePath(pathname?: string): string {
  const raw = (pathname ?? (typeof window !== "undefined" ? window.location.pathname : ""))
    .replace(/\/+$/, "")
    .trim();
  if (raw.startsWith(BASE_PATH)) {
    return raw.slice(BASE_PATH.length) || "/";
  }
  return raw || "/";
}

export function resolveAppRoute(pathname?: string): AppRoute {
  const relative = relativePath(pathname);

  if (relative === "/capex/investimentos/novo") {
    return "capex-investment-new";
  }
  if (/^\/capex\/investimentos\/[^/]+$/.test(relative)) {
    return "capex-investment-edit";
  }
  if (/^\/capex\/aprovacoes\/[^/]+$/.test(relative)) {
    return "capex-approval-detail";
  }
  if (/^\/pessoal\/aprovacoes\/[^/]+$/.test(relative)) {
    return "pessoal-approval-detail";
  }

  switch (relative) {
    case "/":
      return "home";
    case "/orientacoes":
      return "orientacoes";
    case "/capex":
    case "/capex/meus-centros":
      return "capex";
    case "/capex/aprovacoes":
      return "capex-approvals";
    case "/capex/consolidacao":
      return "capex-consolidation";
    case "/pessoal":
      return "pessoal";
    case "/pessoal/aprovacoes":
      return "pessoal-approvals";
    case "/admin":
      return "admin";
    case "/admin/exercicios":
      return "admin-exercicios";
    case "/admin/orientacoes":
      return "admin-orientacoes";
    case "/admin/escopos":
      return "admin-escopos";
    case "/admin/responsaveis":
      return "admin-responsaveis";
    case "/admin/centros-de-custo":
      return "admin-centros-de-custo";
    case "/admin/categorias-capex":
      return "admin-categorias-capex";
    default:
      return "unknown";
  }
}

export function resolveCapexInvestmentId(pathname?: string): string | null {
  const relative = relativePath(pathname);
  const match = relative.match(/^\/capex\/investimentos\/([^/]+)$/);
  if (!match || match[1] === "novo") return null;
  return decodeURIComponent(match[1]);
}

export function resolveCapexPlanId(pathname?: string): string | null {
  const relative = relativePath(pathname);
  const match = relative.match(/^\/capex\/aprovacoes\/([^/]+)$/);
  if (!match) return null;
  return decodeURIComponent(match[1]);
}

export function routeHref(route: AppRoute): string {
  switch (route) {
    case "home":
      return BASE_PATH;
    case "orientacoes":
      return `${BASE_PATH}/orientacoes`;
    case "capex":
      return `${BASE_PATH}/capex`;
    case "capex-investment-new":
      return `${BASE_PATH}/capex/investimentos/novo`;
    case "capex-investment-edit":
      return `${BASE_PATH}/capex/investimentos`;
    case "capex-approvals":
      return `${BASE_PATH}/capex/aprovacoes`;
    case "capex-approval-detail":
      return `${BASE_PATH}/capex/aprovacoes`;
    case "capex-consolidation":
      return `${BASE_PATH}/capex/consolidacao`;
    case "pessoal":
      return `${BASE_PATH}/pessoal`;
    case "pessoal-approvals":
      return `${BASE_PATH}/pessoal/aprovacoes`;
    case "pessoal-approval-detail":
      return `${BASE_PATH}/pessoal/aprovacoes`;
    case "admin":
      return `${BASE_PATH}/admin`;
    case "admin-exercicios":
      return `${BASE_PATH}/admin/exercicios`;
    case "admin-orientacoes":
      return `${BASE_PATH}/admin/orientacoes`;
    case "admin-escopos":
      return `${BASE_PATH}/admin/escopos`;
    case "admin-responsaveis":
      return `${BASE_PATH}/admin/responsaveis`;
    case "admin-centros-de-custo":
      return `${BASE_PATH}/admin/centros-de-custo`;
    case "admin-categorias-capex":
      return `${BASE_PATH}/admin/categorias-capex`;
    default:
      return BASE_PATH;
  }
}

export function capexHref(params?: {
  costCenterId?: string;
  unitId?: string;
}): string {
  const base = routeHref("capex");
  if (!params?.costCenterId) return base;
  const qs = new URLSearchParams({ cost_center_id: params.costCenterId });
  if (params.unitId) qs.set("unit_id", params.unitId);
  return `${base}?${qs.toString()}`;
}

export function pessoalHref(params?: {
  costCenterId?: string;
  unitId?: string;
}): string {
  const base = routeHref("pessoal");
  if (!params?.costCenterId) return base;
  const qs = new URLSearchParams({ cost_center_id: params.costCenterId });
  if (params.unitId) qs.set("unit_id", params.unitId);
  return `${base}?${qs.toString()}`;
}

export function capexNewInvestmentHref(params?: {
  costCenterId?: string;
  unitId?: string;
}): string {
  const base = routeHref("capex-investment-new");
  if (!params?.costCenterId) return base;
  const qs = new URLSearchParams({ cost_center_id: params.costCenterId });
  if (params.unitId) qs.set("unit_id", params.unitId);
  return `${base}?${qs.toString()}`;
}

export function capexInvestmentHref(investmentId: string): string {
  return `${BASE_PATH}/capex/investimentos/${encodeURIComponent(investmentId)}`;
}

export function capexApprovalsHref(): string {
  return routeHref("capex-approvals");
}

export function capexConsolidationHref(): string {
  return routeHref("capex-consolidation");
}

export function capexReviewDetailHref(planId: string): string {
  return `${BASE_PATH}/capex/aprovacoes/${encodeURIComponent(planId)}`;
}

export function resolvePersonnelPlanId(pathname?: string): string | null {
  const relative = relativePath(pathname);
  const match = relative.match(/^\/pessoal\/aprovacoes\/([^/]+)$/);
  if (!match) return null;
  return decodeURIComponent(match[1]);
}

export function pessoalApprovalsHref(): string {
  return routeHref("pessoal-approvals");
}

export function pessoalReviewDetailHref(planId: string): string {
  return `${BASE_PATH}/pessoal/aprovacoes/${encodeURIComponent(planId)}`;
}

export function readQueryParam(name: string): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get(name)?.trim() ?? "";
}
