import { CONSOLE_BASE } from "../constants/routes";

function resolveConsoleBase(basePath?: string): string {
  const normalized = (basePath ?? CONSOLE_BASE).replace(/\/+$/, "") || CONSOLE_BASE;
  return normalized.startsWith("/") ? normalized : `/${normalized}`;
}

export function buildConsoleHref(
  segment: string,
  basePath?: string,
  searchParams?: Record<string, string | null | undefined>,
): string {
  const base = resolveConsoleBase(basePath);
  const trimmed = segment.replace(/^\/+/, "").split("?")[0];
  const path = trimmed ? `${base}/${trimmed}` : base;

  if (!searchParams) return path;

  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(searchParams)) {
    if (value != null && value !== "") {
      query.set(key, value);
    }
  }
  const serialized = query.toString();
  return serialized ? `${path}?${serialized}` : path;
}

/** Navegação client-side dentro do portal (mesmo contrato dos demais MFEs). */
export function navigateConsole(
  segment: string,
  basePath?: string,
  searchParams?: Record<string, string | null | undefined>,
): void {
  if (typeof window === "undefined") return;

  const target = buildConsoleHref(segment, basePath, searchParams);
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;

  if (current === target) return;

  window.history.pushState(window.history.state, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
