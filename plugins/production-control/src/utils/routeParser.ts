import { BRANCH_STORAGE_KEY, DEFAULT_BRANCH, DEFAULT_SUBPLUGIN, PPC_BASE_PATH } from "../constants/routes";
import type { PpcBranch } from "../types";

export type PpcRoute = {
  subpluginId: string;
  detectorId: string | null;
  workCenter: string | null;
  startDate: string | null;
  endDate: string | null;
  locateQuery: string | null;
  branch: PpcBranch;
  pathname: string;
};

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

function isBranch(value: string | null): value is PpcBranch {
  return value === "01" || value === "02";
}

export function readStoredBranch(): PpcBranch {
  if (typeof window === "undefined") return DEFAULT_BRANCH;
  const stored = window.sessionStorage.getItem(BRANCH_STORAGE_KEY);
  return isBranch(stored) ? stored : DEFAULT_BRANCH;
}

export function storeBranch(branch: PpcBranch) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(BRANCH_STORAGE_KEY, branch);
}

function isoDateOrNull(value: string | null): string | null {
  const text = value?.trim() ?? "";
  return ISO_DATE.test(text) ? text : null;
}

function parseSearch(search: string): {
  detectorId: string | null;
  workCenter: string | null;
  startDate: string | null;
  endDate: string | null;
  locateQuery: string | null;
  branch: PpcBranch | null;
} {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const branchRaw = params.get("branch");
  return {
    detectorId: params.get("detector")?.trim() || null,
    workCenter: params.get("ct")?.trim() || null,
    startDate: isoDateOrNull(params.get("startDate")),
    endDate: isoDateOrNull(params.get("endDate")),
    locateQuery: params.get("locate")?.trim() || null,
    branch: isBranch(branchRaw) ? branchRaw : null,
  };
}

export function parsePpcPath(pathname: string, search = "", storedBranch: PpcBranch = DEFAULT_BRANCH): PpcRoute {
  const path = pathname.replace(/\/+$/, "") || "/";
  const query = parseSearch(search);
  const rest = path.startsWith(PPC_BASE_PATH)
    ? path.slice(PPC_BASE_PATH.length)
    : path;
  const segment = rest.replace(/^\/+/, "").split("/")[0] || DEFAULT_SUBPLUGIN;
  const subpluginId = segment === "" ? DEFAULT_SUBPLUGIN : segment;
  return {
    subpluginId,
    detectorId: query.detectorId,
    workCenter: query.workCenter,
    startDate: query.startDate,
    endDate: query.endDate,
    locateQuery: query.locateQuery,
    branch: query.branch ?? storedBranch,
    pathname: path || PPC_BASE_PATH,
  };
}

export function buildPpcHref(input: {
  subpluginId: string;
  branch: PpcBranch;
  detectorId?: string | null;
  workCenter?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  locateQuery?: string | null;
}): string {
  const path =
    input.subpluginId === DEFAULT_SUBPLUGIN
      ? PPC_BASE_PATH
      : `${PPC_BASE_PATH}/${input.subpluginId}`;
  const params = new URLSearchParams();
  params.set("branch", input.branch);
  if (input.detectorId) params.set("detector", input.detectorId);
  if (input.workCenter) params.set("ct", input.workCenter);
  if (input.startDate) params.set("startDate", input.startDate);
  if (input.endDate) params.set("endDate", input.endDate);
  if (input.locateQuery) params.set("locate", input.locateQuery);
  return `${path}?${params.toString()}`;
}

export function navigatePpc(href: string) {
  if (typeof window === "undefined") return;
  const url = new URL(href, window.location.origin);
  const current = `${window.location.pathname}${window.location.search}`;
  const next = `${url.pathname}${url.search}`;
  if (current === next) return;
  window.history.pushState(null, "", next);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
