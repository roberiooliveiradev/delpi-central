import { PROPOSTAS_COMERCIAIS_ROUTES, normalizePropostasComerciaisPath } from "./route";

export function navigatePropostasComerciais(path: string) {
  const target = normalizePropostasComerciaisPath(path);

  if (typeof window === "undefined") return;

  if (window.location.pathname === target) {
    return;
  }

  window.history.pushState(null, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export function navigatePropostaDetail(propostaInterna: string) {
  navigatePropostasComerciais(PROPOSTAS_COMERCIAIS_ROUTES.detail(propostaInterna));
}

export function navigatePropostasList() {
  navigatePropostasComerciais(PROPOSTAS_COMERCIAIS_ROUTES.home);
}
