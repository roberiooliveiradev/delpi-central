import { useCallback, useEffect, useState } from "react";

import { BASE_PATH, type BranchCode, type DelpiMesArea } from "../constants/routes";

export type RegistrationPage = "downtime-reasons";

export type DowntimesRouteParams = {
  /** Preset de período exibido na UI; "custom" usa as chaves de dia from/to. */
  period: "today" | "7d" | "30d" | "custom";
  /** Chave de dia YYYY-MM-DD (somente período personalizado). */
  from: string | null;
  to: string | null;
  workCenter: string | null;
  reasonCode: string | null;
  source: string | null;
  classification: "pending" | "confirmed" | null;
  /** Estado temporal da parada: em andamento (open) ou encerrada (closed). */
  status: "open" | "closed" | null;
  sort: "recent" | "oldest";
  /** Seleção/detalhe — não filtra a lista. */
  downtimeId: string | null;
  page: number;
  pageSize: number;
};

export type DelpiMesRoute = {
  area: DelpiMesArea;
  /** True quando a URL nomeia explicitamente a área (ex.: /downtimes).
   * Na raiz (sem segmento) é false — o App pode então redirecionar para a
   * primeira área permitida sem transformar ausência de área em recusa. */
  areaExplicit: boolean;
  branch: BranchCode;
  workCenter: string | null;
  registrationPage: RegistrationPage | null;
  downtimes: DowntimesRouteParams;
};

export const DOWNTIMES_DEFAULT_PAGE_SIZE = 50;

const DEFAULT_DOWNTIMES: DowntimesRouteParams = {
  period: "7d",
  from: null,
  to: null,
  workCenter: null,
  reasonCode: null,
  source: null,
  classification: null,
  status: null,
  sort: "recent",
  downtimeId: null,
  page: 1,
  pageSize: DOWNTIMES_DEFAULT_PAGE_SIZE,
};

const AREA_SEGMENTS: ReadonlySet<string> = new Set(["monitoring", "downtimes", "history", "registrations"]);
const REGISTRATION_PAGES: ReadonlySet<string> = new Set(["downtime-reasons"]);
const PERIODS: ReadonlySet<string> = new Set(["today", "7d", "30d", "custom"]);
const CLASSIFICATIONS: ReadonlySet<string> = new Set(["pending", "confirmed"]);
const STATUSES: ReadonlySet<string> = new Set(["open", "closed"]);
const DAY_KEY = /^\d{4}-\d{2}-\d{2}$/;

function positiveInt(value: string | null, fallback: number, max = 100): number {
  const parsed = Number.parseInt(value ?? "", 10);
  return Number.isFinite(parsed) && parsed >= 1 && parsed <= max ? parsed : fallback;
}

function parseDowntimesParams(params: URLSearchParams): DowntimesRouteParams {
  const period = params.get("period");
  const classification = params.get("classification");
  const status = params.get("status");
  const from = params.get("from");
  const to = params.get("to");
  return {
    period: period && PERIODS.has(period) ? (period as DowntimesRouteParams["period"]) : "7d",
    from: from && DAY_KEY.test(from) ? from : null,
    to: to && DAY_KEY.test(to) ? to : null,
    workCenter: params.get("workCenter")?.trim() || null,
    reasonCode: params.get("reasonCode")?.trim() || null,
    source: params.get("source")?.trim() || null,
    classification:
      classification && CLASSIFICATIONS.has(classification)
        ? (classification as DowntimesRouteParams["classification"])
        : null,
    status:
      status && STATUSES.has(status)
        ? (status as DowntimesRouteParams["status"])
        : null,
    sort: params.get("sort") === "oldest" ? "oldest" : "recent",
    downtimeId: params.get("downtimeId")?.trim() || null,
    page: positiveInt(params.get("page"), 1, Number.MAX_SAFE_INTEGER),
    pageSize: positiveInt(params.get("pageSize"), DOWNTIMES_DEFAULT_PAGE_SIZE, 100),
  };
}

export function parseDelpiMesRoute(pathname: string, search: string): DelpiMesRoute {
  const suffix = pathname.startsWith(BASE_PATH) ? pathname.slice(BASE_PATH.length) : "";
  const segments = suffix.split("/").filter(Boolean);
  const segment = segments[0];
  const areaExplicit = segment !== undefined && AREA_SEGMENTS.has(segment);
  const area: DelpiMesArea = areaExplicit ? (segment as DelpiMesArea) : "monitoring";
  const registrationPage: RegistrationPage | null =
    area === "registrations" && segments[1] && REGISTRATION_PAGES.has(segments[1])
      ? (segments[1] as RegistrationPage)
      : null;
  const params = new URLSearchParams(search);
  const requestedBranch = params.get("branch");
  const workCenter = area === "monitoring" ? params.get("workCenter") : null;
  const downtimes = area === "downtimes" ? parseDowntimesParams(params) : DEFAULT_DOWNTIMES;
  return { area, areaExplicit, branch: requestedBranch === "02" ? "02" : "01", workCenter, registrationPage, downtimes };
}

export function buildDelpiMesHref(area: DelpiMesArea, branch: BranchCode, workCenter?: string): string {
  if (area === "registrations") return BASE_PATH + "/registrations";
  const href = BASE_PATH + "/" + area + "?branch=" + branch;
  return workCenter ? href + "&workCenter=" + encodeURIComponent(workCenter) : href;
}

/** Serialização determinística dos filtros de Paradas — a canonicalização
 * do App depende de idempotência (parse(build(x)) === x). */
export function buildDowntimesHref(branch: BranchCode, params: DowntimesRouteParams): string {
  const search = new URLSearchParams({ branch });
  if (params.period !== "7d") search.set("period", params.period);
  if (params.from) search.set("from", params.from);
  if (params.to) search.set("to", params.to);
  if (params.workCenter) search.set("workCenter", params.workCenter);
  if (params.reasonCode) search.set("reasonCode", params.reasonCode);
  if (params.source) search.set("source", params.source);
  if (params.classification) search.set("classification", params.classification);
  if (params.status) search.set("status", params.status);
  if (params.sort === "oldest") search.set("sort", "oldest");
  if (params.downtimeId) search.set("downtimeId", params.downtimeId);
  if (params.page > 1) search.set("page", String(params.page));
  if (params.pageSize !== DOWNTIMES_DEFAULT_PAGE_SIZE) search.set("pageSize", String(params.pageSize));
  return BASE_PATH + "/downtimes?" + search.toString();
}

export function buildRegistrationHref(page: RegistrationPage): string {
  return BASE_PATH + "/registrations/" + page;
}

export function useDelpiMesRoute(pathnameFromHost?: string) {
  const [browserLocation, setBrowserLocation] = useState(() => ({
    pathname: window.location.pathname,
    search: window.location.search,
  }));

  useEffect(() => {
    const sync = () => setBrowserLocation({
      pathname: window.location.pathname,
      search: window.location.search,
    });
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  const navigate = useCallback((href: string) => {
    window.history.pushState({}, "", href);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, []);

  return {
    route: parseDelpiMesRoute(pathnameFromHost ?? browserLocation.pathname, browserLocation.search),
    navigate,
  };
}
