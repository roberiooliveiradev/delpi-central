/** Navegação interna da feature via pushState + popstate — mesmo
 * mecanismo governado usado por navigateEngineeringView. */

export function navigatePrc(path: string, basePath: string): void {
  if (typeof window === "undefined") return;
  window.history.pushState(
    window.history.state,
    "",
    `${basePath}/${path}`,
  );
  window.dispatchEvent(
    new PopStateEvent("popstate", { state: window.history.state }),
  );
}
