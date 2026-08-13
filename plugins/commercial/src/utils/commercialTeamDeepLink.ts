export const COMMERCIAL_TEAM_VIEW_VALUES = ["list", "org"] as const;

export type CommercialTeamView = (typeof COMMERCIAL_TEAM_VIEW_VALUES)[number];

const VIEW_VALUES = new Set<string>(COMMERCIAL_TEAM_VIEW_VALUES);

export function normalizeCommercialTeamView(
  value: string | null | undefined,
): CommercialTeamView {
  const normalized = (value ?? "").trim().toLowerCase();
  return VIEW_VALUES.has(normalized) ? (normalized as CommercialTeamView) : "list";
}

export function parseCommercialTeamView(
  search: string | undefined = typeof window !== "undefined" ? window.location.search : "",
): CommercialTeamView {
  const params = new URLSearchParams(
    search?.startsWith("?") ? search.slice(1) : search ?? "",
  );
  return normalizeCommercialTeamView(params.get("view"));
}

/** Atualiza `view` na URL atual sem navegar fora da página. */
export function replaceCommercialTeamViewInUrl(view: CommercialTeamView): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (view === "list") url.searchParams.delete("view");
  else url.searchParams.set("view", view);
  window.history.replaceState(window.history.state, "", `${url.pathname}${url.search}${url.hash}`);
}
