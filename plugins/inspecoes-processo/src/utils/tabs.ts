export type InspecoesProcessoTab = "overview" | "historico" | "auditoria";

export function tabFromSearch(search?: string): InspecoesProcessoTab {
  const query = search ?? (typeof window !== "undefined" ? window.location.search : "");
  const value = new URLSearchParams(query).get("tab");
  if (value === "historico") return "historico";
  if (value === "auditoria") return "auditoria";
  return "overview";
}

export function syncTabInUrl(tab: InspecoesProcessoTab): void {
  if (typeof window === "undefined") return;

  const url = new URL(window.location.href);
  if (tab === "overview") {
    url.searchParams.delete("tab");
  } else {
    url.searchParams.set("tab", tab);
  }

  const next = `${url.pathname}${url.search}${url.hash}`;
  window.history.replaceState(null, "", next);
}
