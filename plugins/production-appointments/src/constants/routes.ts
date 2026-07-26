import { PRODUCTION_APPOINTMENTS_BASE_PATH, type BranchRouteCode } from "./branches";

export type AppointmentsView = "dashboard" | "op-detail" | "ct-detail";

export type ParsedAppointmentsRoute = {
  view: AppointmentsView;
  branchRoute: BranchRouteCode;
  productionOrder?: string;
  workCenter?: string;
};

export function branchHomePath(branchRoute: BranchRouteCode): string {
  return `${PRODUCTION_APPOINTMENTS_BASE_PATH}/${branchRoute.toLowerCase()}`;
}

function buildDetailPathWithPeriod(
  base: string,
  period?: { dateStart: string; dateEnd: string },
): string {
  if (!period?.dateStart || !period?.dateEnd) return base;
  const params = new URLSearchParams({
    start_date: period.dateStart,
    end_date: period.dateEnd,
  });
  return `${base}?${params.toString()}`;
}

export function buildOpDetailPath(
  branchRoute: BranchRouteCode,
  productionOrder: string,
  period?: { dateStart: string; dateEnd: string },
): string {
  const encoded = encodeURIComponent(String(productionOrder).trim());
  return buildDetailPathWithPeriod(`${branchHomePath(branchRoute)}/op/${encoded}`, period);
}

export function buildCtDetailPath(
  branchRoute: BranchRouteCode,
  workCenter: string,
  period?: { dateStart: string; dateEnd: string },
): string {
  const encoded = encodeURIComponent(String(workCenter).trim());
  return buildDetailPathWithPeriod(`${branchHomePath(branchRoute)}/ct/${encoded}`, period);
}

export function parseAppointmentsPath(pathname: string): ParsedAppointmentsRoute {
  const normalized =
    pathname.length > 1 && pathname.endsWith("/") ? pathname.slice(0, -1) : pathname || "";
  const base = PRODUCTION_APPOINTMENTS_BASE_PATH.replace(/\//g, "\\/");

  const ctMatch = normalized.match(new RegExp(`^${base}/(sc|es)/ct/([^/?#]+)$`, "i"));
  if (ctMatch) {
    const branchRoute = ctMatch[1].toUpperCase() === "ES" ? "ES" : "SC";
    return {
      view: "ct-detail",
      branchRoute,
      workCenter: decodeURIComponent(ctMatch[2]),
    };
  }

  const opMatch = normalized.match(new RegExp(`^${base}/(sc|es)/op/([^/?#]+)$`, "i"));
  if (opMatch) {
    const branchRoute = opMatch[1].toUpperCase() === "ES" ? "ES" : "SC";
    return {
      view: "op-detail",
      branchRoute,
      productionOrder: decodeURIComponent(opMatch[2]),
    };
  }

  const branchRoute = /\/es(\/|$)/i.test(normalized) ? "ES" : "SC";
  return { view: "dashboard", branchRoute };
}

export function readDetailPeriodFromUrl(): { dateStart: string; dateEnd: string } | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  const dateStart = (params.get("start_date") ?? params.get("date_start"))?.trim() ?? "";
  const dateEnd = (params.get("end_date") ?? params.get("date_end"))?.trim() ?? "";
  if (!dateStart || !dateEnd) return null;
  return { dateStart, dateEnd };
}

/** Atualiza só a query de período sem empilhar histórico. */
export function withDetailPeriodParams(
  pathname: string,
  currentSearch: string,
  dateStart: string,
  dateEnd: string,
): string {
  const raw = currentSearch.startsWith("?") ? currentSearch.slice(1) : currentSearch;
  const params = new URLSearchParams(raw);
  params.delete("date_start");
  params.delete("date_end");
  params.set("start_date", dateStart);
  params.set("end_date", dateEnd);
  return `${pathname}?${params.toString()}`;
}

export function replaceDetailPeriodInUrl(dateStart: string, dateEnd: string): void {
  if (typeof window === "undefined") return;
  const next = withDetailPeriodParams(
    window.location.pathname,
    window.location.search,
    dateStart,
    dateEnd,
  );
  const current = `${window.location.pathname}${window.location.search}`;
  if (next === current) return;
  window.history.replaceState(window.history.state, "", next);
}
