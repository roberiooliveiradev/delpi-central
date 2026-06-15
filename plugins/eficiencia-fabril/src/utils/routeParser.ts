import type { BranchRouteCode } from "../constants/branches";
import { branchRouteFromPathname } from "../constants/branches";
import { EFICIENCIA_FABRIL_BASE_PATH } from "../constants/routes";

export type EficienciaFabrilView = "dashboard" | "appointment-detail";

export type ParsedEficienciaFabrilRoute = {
  view: EficienciaFabrilView;
  branchRoute: BranchRouteCode | null;
  appointmentId?: string;
};

export function normalizeEficienciaFabrilPath(pathname: string): string {
  if (!pathname) return EFICIENCIA_FABRIL_BASE_PATH;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function parseEficienciaFabrilPath(pathname: string): ParsedEficienciaFabrilRoute {
  const path = normalizeEficienciaFabrilPath(pathname);
  const branchRoute = branchRouteFromPathname(path);

  const appointmentMatch = path.match(
    new RegExp(
      `^${EFICIENCIA_FABRIL_BASE_PATH.replace(/\//g, "\\/")}/(sc|es)/appointment/([^/]+)$`,
      "i"
    )
  );

  if (appointmentMatch) {
    const routeCode = appointmentMatch[1].toUpperCase() as BranchRouteCode;
    return {
      view: "appointment-detail",
      branchRoute: routeCode,
      appointmentId: decodeURIComponent(appointmentMatch[2]),
    };
  }

  return {
    view: "dashboard",
    branchRoute,
  };
}

export function readAppointmentBranchFromUrl(
  search = typeof window !== "undefined" ? window.location.search : ""
): string | undefined {
  const value = new URLSearchParams(search).get("branch")?.trim();
  return value || undefined;
}
