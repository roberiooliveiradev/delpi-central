/** Navegação client-side dentro do portal (evita reload completo do MFE). */
export function navigateQuality(path: string) {
  const target = path.startsWith("/") ? path : `/${path}`;

  if (window.location.pathname === target) return;

  window.history.pushState(null, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
