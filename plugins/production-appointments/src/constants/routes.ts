import { PRODUCTION_APPOINTMENTS_BASE_PATH, type BranchRouteCode } from "./branches";

export type AppointmentsView = "dashboard" | "op-detail";

export type ParsedAppointmentsRoute = {
  view: AppointmentsView;
  branchRoute: BranchRouteCode;
  productionOrder?: string;
};

export function branchHomePath(branchRoute: BranchRouteCode): string {
  return `${PRODUCTION_APPOINTMENTS_BASE_PATH}/${branchRoute.toLowerCase()}`;
}

export function buildOpDetailPath(
  branchRoute: BranchRouteCode,
  productionOrder: string,
  period?: { dateStart: string; dateEnd: string },
): string {
  const encoded = encodeURIComponent(String(productionOrder).trim());
  const base = `${branchHomePath(branchRoute)}/op/${encoded}`;
  if (!period?.dateStart || !period?.dateEnd) return base;
  const params = new URLSearchParams({
    date_start: period.dateStart,
    date_end: period.dateEnd,
  });
  return `${base}?${params.toString()}`;
}

export function parseAppointmentsPath(pathname: string): ParsedAppointmentsRoute {
  const normalized =
    pathname.length > 1 && pathname.endsWith("/") ? pathname.slice(0, -1) : pathname || "";
  const base = PRODUCTION_APPOINTMENTS_BASE_PATH.replace(/\//g, "\\/");
  const detailMatch = normalized.match(
    new RegExp(`^${base}/(sc|es)/op/([^/?#]+)$`, "i"),
  );
  if (detailMatch) {
    const branchRoute = detailMatch[1].toUpperCase() === "ES" ? "ES" : "SC";
    return {
      view: "op-detail",
      branchRoute,
      productionOrder: decodeURIComponent(detailMatch[2]),
    };
  }

  const branchRoute = /\/es(\/|$)/i.test(normalized) ? "ES" : "SC";
  return { view: "dashboard", branchRoute };
}

export function readDetailPeriodFromUrl(): { dateStart: string; dateEnd: string } | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  const dateStart = params.get("date_start")?.trim() ?? "";
  const dateEnd = params.get("date_end")?.trim() ?? "";
  if (!dateStart || !dateEnd) return null;
  return { dateStart, dateEnd };
}
