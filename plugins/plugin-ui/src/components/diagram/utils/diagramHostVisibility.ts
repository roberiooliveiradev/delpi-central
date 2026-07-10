/** Painel do workspace Transformômetro (ou equivalente) que envolve o editor. */
export function findDiagramWorkspaceHost(element: Element): Element | null {
  return (
    element.closest(".tm-processo-workspace-section") ??
    element.closest("[data-section]")
  );
}

/** Seção/painel visível — evita fitView enquanto `aria-hidden` ou inativa. */
export function isDiagramWorkspaceHostVisible(element: Element): boolean {
  const host = findDiagramWorkspaceHost(element);
  if (!host) return true;
  if (host.classList.contains("tm-processo-workspace-section--active")) return true;
  return host.getAttribute("aria-hidden") !== "true";
}
