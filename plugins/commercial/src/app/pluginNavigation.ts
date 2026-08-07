import {
  buildCustomerDetailPath,
  buildAnalyticsOpportunityDetailPath,
  buildAnalyticsOtdLinePath,
  buildPluginPath,
  buildProposalDetailPath,
  normalizePathname,
  type BuildablePluginView,
} from "./pluginRoutes";

export function navigatePluginPath(target: string): void {
  if (typeof window === "undefined") return;

  const current = `${normalizePathname(window.location.pathname)}${window.location.search || ""}`;
  if (current === target) return;

  window.history.pushState(null, "", target);
  const popState =
    typeof PopStateEvent === "function"
      ? new PopStateEvent("popstate")
      : new Event("popstate");
  window.dispatchEvent(popState);
}

export function navigatePluginView(
  view: BuildablePluginView,
  options?: { basePath?: string; search?: string },
): void {
  const target = buildPluginPath(view, options?.basePath, options?.search);
  navigatePluginPath(target);
}

export function navigateCustomerDetail(
  codigo: string,
  loja: string,
  options?: { basePath?: string },
): boolean {
  const path = buildCustomerDetailPath(options?.basePath, codigo, loja);
  if (!path) return false;
  navigatePluginPath(path);
  return true;
}

export function navigateProposalDetail(
  propostaId: string,
  options?: { basePath?: string },
): boolean {
  const path = buildProposalDetailPath(options?.basePath, propostaId);
  if (!path) return false;
  navigatePluginPath(path);
  return true;
}

export function navigateAnalyticsOpportunityDetail(
  proposalNumber: string,
  options?: { basePath?: string; search?: string },
): boolean {
  const path = buildAnalyticsOpportunityDetailPath(
    options?.basePath,
    proposalNumber,
    options?.search,
  );
  if (!path) return false;
  navigatePluginPath(path);
  return true;
}

export function navigateAnalyticsOtdLine(
  branch: string,
  orderNumber: string,
  lineItem: string,
  options?: { basePath?: string; search?: string },
): boolean {
  const path = buildAnalyticsOtdLinePath(
    options?.basePath,
    branch,
    orderNumber,
    lineItem,
    options?.search,
  );
  if (!path) return false;
  navigatePluginPath(path);
  return true;
}

export { buildCustomerDetailPath, buildProposalDetailPath };
