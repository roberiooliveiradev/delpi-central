/** Filtros da Visão geral — semântica oficial do dashboard de
 * Engenharia (referência funcional), implementada sobre os utilitários
 * de período do `@delpi/plugin-ui` (timezone America/Sao_Paulo).
 *
 * - Preset rápido resolve o intervalo oficial de datas;
 * - competência YYYY-MM está vinculada às datas (mudar o mês atualiza o
 *   intervalo; editar datas para dentro do mesmo mês mantém o vínculo,
 *   cruzar meses limpa a competência);
 * - unidade é filtro de escopo operacional — scores estratégicos
 *   consolidados permanecem consolidados (doc 18, G3.4);
 * - URL sync com os mesmos parâmetros do contrato `/v1/overview`
 *   (start_date, end_date, competence, branch) — nenhum token/dado
 *   sensível na URL. */

import {
  detectPeriodPreset,
  resolvePeriodPreset,
  type PeriodPresetId,
} from "@delpi/plugin-ui/index";

export type OverviewFilterState = {
  preset: PeriodPresetId;
  dateStart: string;
  dateEnd: string;
  competence: string;
  /** Código da unidade operacional ("" = consolidado). */
  branch: string;
};

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const COMPETENCE_RE = /^\d{4}-(0[1-9]|1[0-2])$/;

export function isValidIsoDate(value: string): boolean {
  return ISO_DATE_RE.test(value);
}

export function isValidCompetence(value: string): boolean {
  return COMPETENCE_RE.test(value);
}

function monthLastDayIso(competence: string): string {
  const [year, month] = competence.split("-").map(Number);
  const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate();
  return `${competence}-${String(lastDay).padStart(2, "0")}`;
}

/** Competência → intervalo do mês; mês corrente termina em hoje. */
export function competenceToDateRange(
  competence: string,
  todayIso: string,
): Pick<OverviewFilterState, "dateStart" | "dateEnd"> {
  if (!isValidCompetence(competence)) {
    return { dateStart: "", dateEnd: "" };
  }
  const dateEnd =
    competence === todayIso.slice(0, 7) ? todayIso : monthLastDayIso(competence);
  return { dateStart: `${competence}-01`, dateEnd };
}

/** Intervalo no mesmo mês → competência; cruza meses → "". */
export function dateRangeToCompetence(
  dateStart: string,
  dateEnd: string,
): string {
  if (!isValidIsoDate(dateStart) || !isValidIsoDate(dateEnd)) return "";
  const startMonth = dateStart.slice(0, 7);
  return startMonth === dateEnd.slice(0, 7) ? startMonth : "";
}

export function defaultFilters(now: Date = new Date()): OverviewFilterState {
  const range = resolvePeriodPreset("this_month", now);
  return {
    preset: "this_month",
    dateStart: range?.dateStart ?? "",
    dateEnd: range?.dateEnd ?? "",
    competence: range?.competence ?? "",
    branch: "",
  };
}

export function applyPreset(
  preset: PeriodPresetId,
  current: OverviewFilterState,
  now: Date = new Date(),
): OverviewFilterState {
  if (preset === "custom") return { ...current, preset };
  const range = resolvePeriodPreset(preset, now);
  if (!range) return { ...current, preset };
  return {
    ...current,
    preset,
    dateStart: range.dateStart,
    dateEnd: range.dateEnd,
    competence: range.competence || dateRangeToCompetence(range.dateStart, range.dateEnd),
  };
}

export function applyCompetence(
  competence: string,
  current: OverviewFilterState,
  now: Date = new Date(),
): OverviewFilterState {
  if (!competence) return { ...current, competence: "", preset: "custom" };
  const range = competenceToDateRange(competence, todayIso(now));
  const next: OverviewFilterState = {
    ...current,
    competence,
    dateStart: range.dateStart,
    dateEnd: range.dateEnd,
  };
  return { ...next, preset: detectPeriodPreset(next.dateStart, next.dateEnd, now) };
}

export function applyDateStart(
  dateStart: string,
  current: OverviewFilterState,
  now: Date = new Date(),
): OverviewFilterState {
  const dateEnd = current.dateEnd;
  const competence = dateRangeToCompetence(dateStart, dateEnd);
  const next = { ...current, dateStart, competence };
  return { ...next, preset: detectPeriodPreset(dateStart, dateEnd, now) };
}

export function applyDateEnd(
  dateEnd: string,
  current: OverviewFilterState,
  now: Date = new Date(),
): OverviewFilterState {
  const dateStart = current.dateStart;
  const competence = dateRangeToCompetence(dateStart, dateEnd);
  const next = { ...current, dateEnd, competence };
  return { ...next, preset: detectPeriodPreset(dateStart, dateEnd, now) };
}

export function applyBranch(
  branch: string,
  current: OverviewFilterState,
): OverviewFilterState {
  return { ...current, branch };
}

function todayIso(now: Date): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Sao_Paulo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const part = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  return `${part("year")}-${part("month")}-${part("day")}`;
}

/** Filtros válidos para serializar na API — datas ISO válidas e
 * intervalo coerente; campos inválidos não vão para o owner. */
export function toApiFilters(state: OverviewFilterState): {
  start_date?: string;
  end_date?: string;
  competence?: string;
  branch?: string;
} {
  const filters: {
    start_date?: string;
    end_date?: string;
    competence?: string;
    branch?: string;
  } = {};
  if (isValidIsoDate(state.dateStart)) filters.start_date = state.dateStart;
  if (isValidIsoDate(state.dateEnd)) filters.end_date = state.dateEnd;
  if (
    isValidIsoDate(state.dateStart) &&
    isValidIsoDate(state.dateEnd) &&
    state.dateStart > state.dateEnd
  ) {
    delete filters.start_date;
    delete filters.end_date;
  }
  if (isValidCompetence(state.competence)) {
    filters.competence = state.competence;
  }
  if (state.branch) filters.branch = state.branch;
  return filters;
}

// --- URL sync ---------------------------------------------------------

const VALID_BRANCHES = new Set(["01", "02"]);

export function readFiltersFromSearch(
  search: string,
  now: Date = new Date(),
): OverviewFilterState {
  const params = new URLSearchParams(search);
  const dateStart = params.get("start_date") ?? "";
  const dateEnd = params.get("end_date") ?? "";
  const competence = params.get("competence") ?? "";
  const branch = params.get("branch") ?? "";

  const hasAny =
    isValidIsoDate(dateStart) ||
    isValidIsoDate(dateEnd) ||
    isValidCompetence(competence) ||
    VALID_BRANCHES.has(branch);
  if (!hasAny) return defaultFilters(now);

  const defaults = defaultFilters(now);
  if (isValidCompetence(competence)) {
    const range = competenceToDateRange(competence, todayIso(now));
    return {
      preset: detectPeriodPreset(range.dateStart, range.dateEnd, now),
      dateStart: range.dateStart,
      dateEnd: range.dateEnd,
      competence,
      branch: VALID_BRANCHES.has(branch) ? branch : "",
    };
  }

  const next = {
    preset: "custom" as PeriodPresetId,
    dateStart: isValidIsoDate(dateStart) ? dateStart : defaults.dateStart,
    dateEnd: isValidIsoDate(dateEnd) ? dateEnd : defaults.dateEnd,
    competence: "",
    branch: VALID_BRANCHES.has(branch) ? branch : "",
  };
  return {
    ...next,
    competence: dateRangeToCompetence(next.dateStart, next.dateEnd),
    preset: detectPeriodPreset(next.dateStart, next.dateEnd, now),
  };
}

export function writeFiltersToUrl(state: OverviewFilterState): void {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams();
  if (isValidIsoDate(state.dateStart)) params.set("start_date", state.dateStart);
  if (isValidIsoDate(state.dateEnd)) params.set("end_date", state.dateEnd);
  if (isValidCompetence(state.competence)) {
    params.set("competence", state.competence);
  }
  if (VALID_BRANCHES.has(state.branch)) params.set("branch", state.branch);

  const query = params.toString();
  const nextUrl = `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (current === nextUrl) return;
  window.history.replaceState(window.history.state, "", nextUrl);
}
