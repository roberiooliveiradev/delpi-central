import { LMPS_BASE_PATH } from "../constants/routes";

export type LmpsView = "dashboard" | "ov-detail";

export type ParsedLmpsRoute = {
  view: LmpsView;
  saleNumber?: string;
};

export function normalizeLmpsPath(pathname: string): string {
  if (!pathname) return LMPS_BASE_PATH;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function parseLmpsPath(pathname: string): ParsedLmpsRoute {
  const path = normalizeLmpsPath(pathname);
  const ovMatch = path.match(
    new RegExp(`^${LMPS_BASE_PATH.replace(/\//g, "\\/")}/ov/([^/]+)$`, "i")
  );

  if (ovMatch) {
    return {
      view: "ov-detail",
      saleNumber: decodeURIComponent(ovMatch[1]),
    };
  }

  return { view: "dashboard" };
}

export function readOvBranchFromUrl(
  search = typeof window !== "undefined" ? window.location.search : ""
): string | undefined {
  const value = new URLSearchParams(search).get("branch")?.trim();
  return value || undefined;
}
