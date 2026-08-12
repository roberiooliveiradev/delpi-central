/** Deep link `?q=` do hub Início. */

export function readHomeSearchQuery(search: string = window.location.search): string {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  return (params.get("q") ?? "").trim();
}

export function writeHomeSearchQuery(query: string, pathname?: string): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (pathname) url.pathname = pathname;
  const trimmed = query.trim();
  if (trimmed) {
    url.searchParams.set("q", trimmed);
  } else {
    url.searchParams.delete("q");
  }
  window.history.replaceState(window.history.state, "", `${url.pathname}${url.search}${url.hash}`);
}
