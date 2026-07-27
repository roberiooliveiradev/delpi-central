import { LMPS_BASE_PATH, LMPS_ROUTES } from "../constants/routes";

export type LmpsView =
  | "dashboard"
  | "nonconformities"
  | "nonconformity-detail"
  | "nonconformity-new"
  | "ov-detail";

export type ParsedLmpsRoute = {
  view: LmpsView;
  saleNumber?: string;
  ncId?: string;
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
  const base = LMPS_BASE_PATH.replace(/\//g, "\\/");

  const ovMatch = path.match(new RegExp(`^${base}/ov/([^/]+)$`, "i"));
  if (ovMatch) {
    return {
      view: "ov-detail",
      saleNumber: decodeURIComponent(ovMatch[1]),
    };
  }

  if (path === LMPS_ROUTES.nonconformityNew) {
    return { view: "nonconformity-new" };
  }

  const ncDetailMatch = path.match(
    new RegExp(`^${base}/nonconformities/([^/]+)$`, "i"),
  );
  if (ncDetailMatch) {
    return {
      view: "nonconformity-detail",
      ncId: decodeURIComponent(ncDetailMatch[1]),
    };
  }

  if (path === LMPS_ROUTES.nonconformities) {
    return { view: "nonconformities" };
  }

  return { view: "dashboard" };
}

export function readOvBranchFromUrl(
  search = typeof window !== "undefined" ? window.location.search : ""
): string | undefined {
  const value = new URLSearchParams(search).get("branch")?.trim();
  return value || undefined;
}
