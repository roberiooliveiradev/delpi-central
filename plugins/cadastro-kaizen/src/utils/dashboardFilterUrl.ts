import {
  applyCompetenceChange,
  applyDateRangeChange,
  isValidCompetence,
} from "./competence";

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const SESSION_STORAGE_KEY = "delpi.cadastro-kaizen.dashboard-filters";

export type DashboardFilterState = {
  unit: string;
  dateStart: string;
  dateEnd: string;
  competence: string;
};

const EMPTY: DashboardFilterState = {
  unit: "",
  dateStart: "",
  dateEnd: "",
  competence: "",
};

function isIso(value: string): boolean {
  return ISO_DATE_RE.test(value);
}

function resolveLinked(
  competence: string,
  dateStart: string,
  dateEnd: string,
): Pick<DashboardFilterState, "dateStart" | "dateEnd" | "competence"> {
  if (isValidCompetence(competence)) {
    return applyCompetenceChange(competence);
  }
  return applyDateRangeChange(isIso(dateStart) ? dateStart : "", isIso(dateEnd) ? dateEnd : "");
}

function parseParams(params: URLSearchParams): DashboardFilterState | null {
  const unit = params.get("unit") ?? "";
  const competence = params.get("competence") ?? "";
  const dateStart = params.get("date_start") ?? "";
  const dateEnd = params.get("date_end") ?? "";

  const hasAny =
    unit.length > 0 ||
    isValidCompetence(competence) ||
    isIso(dateStart) ||
    isIso(dateEnd);
  if (!hasAny) return null;

  return { unit, ...resolveLinked(competence, dateStart, dateEnd) };
}

function readFromSession(): DashboardFilterState | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as Record<string, unknown>;
    const unit = typeof data.unit === "string" ? data.unit : "";
    const competence = typeof data.competence === "string" ? data.competence : "";
    const dateStart = typeof data.dateStart === "string" ? data.dateStart : "";
    const dateEnd = typeof data.dateEnd === "string" ? data.dateEnd : "";
    const state = { unit, ...resolveLinked(competence, dateStart, dateEnd) };
    const empty =
      !state.unit && !state.dateStart && !state.dateEnd && !state.competence;
    return empty ? null : state;
  } catch {
    return null;
  }
}

/** URL tem prioridade; sessionStorage mantém os filtros ao trocar de aba no portal. */
export function readDashboardFilters(
  search = typeof window !== "undefined" ? window.location.search : "",
): DashboardFilterState {
  const fromUrl = parseParams(new URLSearchParams(search));
  if (fromUrl) return fromUrl;
  return readFromSession() ?? EMPTY;
}

function buildSearch(state: DashboardFilterState): string {
  const params = new URLSearchParams();
  if (state.unit) params.set("unit", state.unit);
  if (state.competence) params.set("competence", state.competence);
  if (state.dateStart) params.set("date_start", state.dateStart);
  if (state.dateEnd) params.set("date_end", state.dateEnd);
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function writeDashboardFilters(state: DashboardFilterState): void {
  if (typeof window === "undefined") return;

  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // quota ou modo privado — ignora
  }

  const nextUrl = `${window.location.pathname}${buildSearch(state)}${window.location.hash}`;
  const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (currentUrl === nextUrl) return;

  window.history.replaceState(window.history.state, "", nextUrl);
}

export function subscribeDashboardFilterSync(onSync: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("popstate", onSync);
  return () => window.removeEventListener("popstate", onSync);
}
