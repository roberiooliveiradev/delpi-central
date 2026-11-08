export type InspecoesEntradaTab = "overview" | "historico" | "fornecedores";

export function tabFromSearch(search?: string): InspecoesEntradaTab {
  const query = search ?? (typeof window !== "undefined" ? window.location.search : "");
  const value = new URLSearchParams(query).get("tab");
  return value === "historico" || value === "fornecedores" ? value : "overview";
}

export function syncTabInUrl(tab: InspecoesEntradaTab): void {
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
