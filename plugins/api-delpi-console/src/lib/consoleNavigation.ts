import { CONSOLE_BASE } from "../constants/routes";

function resolveConsoleBase(basePath?: string): string {
  const normalized = (basePath ?? CONSOLE_BASE).replace(/\/+$/, "") || CONSOLE_BASE;
  return normalized.startsWith("/") ? normalized : `/${normalized}`;
}

export function buildConsoleHref(segment: string, basePath?: string): string {
  const base = resolveConsoleBase(basePath);
  const trimmed = segment.replace(/^\/+/, "");
  return trimmed ? `${base}/${trimmed}` : base;
}

/** Navegação client-side dentro do portal (mesmo contrato dos demais MFEs). */
export function navigateConsole(segment: string, basePath?: string): void {
  if (typeof window === "undefined") return;

  const target = buildConsoleHref(segment, basePath);
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;

  if (current === target) return;

  window.history.pushState(window.history.state, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
