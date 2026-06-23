import { COMMERCIAL_BASE_PATH } from "../constants/routes";

export type CommercialView = "dashboard" | "ov-detail";

export type ParsedCommercialRoute = {
  view: CommercialView;
  proposalNumber?: string;
};

export function normalizeCommercialPath(pathname: string): string {
  if (!pathname) return COMMERCIAL_BASE_PATH;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function parseCommercialPath(pathname: string): ParsedCommercialRoute {
  const path = normalizeCommercialPath(pathname);
  const ovMatch = path.match(
    new RegExp(`^${COMMERCIAL_BASE_PATH.replace(/\//g, "\\/")}/ov/([^/]+)$`, "i")
  );

  if (ovMatch) {
    return {
      view: "ov-detail",
      proposalNumber: decodeURIComponent(ovMatch[1]),
    };
  }

  return { view: "dashboard" };
}

export function readProposalBranchFromUrl(
  search = typeof window !== "undefined" ? window.location.search : ""
): string | undefined {
  const value = new URLSearchParams(search).get("branch")?.trim();
  return value || undefined;
}

export function readProposalRevisionFromUrl(
  search = typeof window !== "undefined" ? window.location.search : ""
): string | undefined {
  const value = new URLSearchParams(search).get("revision")?.trim();
  return value || undefined;
}
