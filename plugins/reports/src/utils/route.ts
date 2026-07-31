export const REPORTS_BASE = "/apps/reports";
export const REPORTS_LIST_PATH = `${REPORTS_BASE}/relatorios`;
export const REPORTS_NEW_PATH = `${REPORTS_BASE}/new`;
export const REPORTS_FOLLOW_UP_LIST_PATH = `${REPORTS_BASE}/acompanhamentos`;

export const DELPI_LOGO_URL =
  typeof window !== "undefined"
    ? `${window.location.origin}/logoDelpi.svg`
    : "/logoDelpi.svg";

export type ReportsNavSection = "overview" | "reports" | "followUp";

export type ReportsRoute =
  | { kind: "overview"; nav: "overview" }
  | { kind: "list"; nav: "reports" }
  | { kind: "create"; nav: "reports" }
  | { kind: "detail"; nav: "reports"; definitionId: string }
  | { kind: "followUpList"; nav: "followUp" }
  | {
      kind: "followUp";
      nav: "followUp";
      definitionId: string;
      productCode: string | null;
    };

function resolvePathname(pathname?: string): string {
  if (pathname && pathname.trim()) {
    return pathname.replace(/\/+$/, "") || "/";
  }
  if (typeof window !== "undefined" && window.location.pathname) {
    return window.location.pathname.replace(/\/+$/, "") || "/";
  }
  return "/";
}

function readProductQuery(): string | null {
  if (typeof window === "undefined") return null;
  const value = new URLSearchParams(window.location.search).get("product");
  const code = String(value || "").trim();
  return code || null;
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
  if (rest === "acompanhamentos") {
    return { kind: "followUpList", nav: "followUp" };
  }
  if (rest.startsWith("acompanhamentos/")) {
    const definitionId = decodeURIComponent(rest.slice("acompanhamentos/".length));
    if (!definitionId || definitionId.includes("/")) {
      return { kind: "followUpList", nav: "followUp" };
    }
    return {
      kind: "followUp",
      nav: "followUp",
      definitionId,
      productCode: readProductQuery(),
    };
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

export function followUpPath(
  definitionId: string,
  productCode?: string | null,
): string {
  const base = `${REPORTS_FOLLOW_UP_LIST_PATH}/${encodeURIComponent(definitionId)}`;
  const code = String(productCode || "").trim();
  if (!code) return base;
  return `${base}?product=${encodeURIComponent(code)}`;
}
