export const REPORTS_BASE = "/apps/reports";
export const REPORTS_LIST_PATH = `${REPORTS_BASE}/relatorios`;
export const REPORTS_NEW_PATH = `${REPORTS_BASE}/new`;

export const DELPI_LOGO_URL =
  typeof window !== "undefined"
    ? `${window.location.origin}/logoDelpi.svg`
    : "/logoDelpi.svg";

export type ReportsNavSection = "overview" | "reports";

export type ReportsRoute =
  | { kind: "overview"; nav: "overview" }
  | { kind: "list"; nav: "reports" }
  | { kind: "create"; nav: "reports" }
  | { kind: "detail"; nav: "reports"; definitionId: string };

function resolvePathname(pathname?: string): string {
  if (pathname && pathname.trim()) {
    return pathname.replace(/\/+$/, "") || "/";
  }
  if (typeof window !== "undefined" && window.location.pathname) {
    return window.location.pathname.replace(/\/+$/, "") || "/";
  }
  return "/";
}

export function resolveReportsRoute(pathname?: string): ReportsRoute {
  const path = resolvePathname(pathname);
  if (!path.startsWith(REPORTS_BASE)) {
    return { kind: "overview", nav: "overview" };
  }
  if (path === REPORTS_BASE) {
    return { kind: "overview", nav: "overview" };
  }

  const rest = path.slice(REPORTS_BASE.length + 1);
  if (rest === "relatorios") {
    return { kind: "list", nav: "reports" };
  }
  if (rest === "new") {
    return { kind: "create", nav: "reports" };
  }
  if (!rest || rest.includes("/")) {
    return { kind: "overview", nav: "overview" };
  }
  return {
    kind: "detail",
    nav: "reports",
    definitionId: decodeURIComponent(rest),
  };
}

export function definitionPath(definitionId: string): string {
  return `${REPORTS_BASE}/${encodeURIComponent(definitionId)}`;
}
