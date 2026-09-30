import { useCallback, useEffect, useState } from "react";

import { BASE_PATH, type BranchCode, type DelpiMesArea } from "../constants/routes";

export type RegistrationPage = "downtime-reasons";

export type DelpiMesRoute = {
  area: DelpiMesArea;
  branch: BranchCode;
  workCenter: string | null;
  registrationPage: RegistrationPage | null;
};

const AREA_SEGMENTS: ReadonlySet<string> = new Set(["downtimes", "history", "registrations"]);
const REGISTRATION_PAGES: ReadonlySet<string> = new Set(["downtime-reasons"]);

export function parseDelpiMesRoute(pathname: string, search: string): DelpiMesRoute {
  const suffix = pathname.startsWith(BASE_PATH) ? pathname.slice(BASE_PATH.length) : "";
  const segments = suffix.split("/").filter(Boolean);
  const segment = segments[0];
  const area: DelpiMesArea = segment && AREA_SEGMENTS.has(segment) ? (segment as DelpiMesArea) : "monitoring";
  const registrationPage: RegistrationPage | null =
    area === "registrations" && segments[1] && REGISTRATION_PAGES.has(segments[1])
      ? (segments[1] as RegistrationPage)
      : null;
  const params = new URLSearchParams(search);
  const requestedBranch = params.get("branch");
  const workCenter = area === "monitoring" ? params.get("workCenter") : null;
  return { area, branch: requestedBranch === "02" ? "02" : "01", workCenter, registrationPage };
}

export function buildDelpiMesHref(area: DelpiMesArea, branch: BranchCode, workCenter?: string): string {
  if (area === "registrations") return `${BASE_PATH}/registrations`;
  const href = `${BASE_PATH}/${area}?branch=${branch}`;
  return workCenter ? `${href}&workCenter=${encodeURIComponent(workCenter)}` : href;
}

export function buildRegistrationHref(page: RegistrationPage): string {
  return `${BASE_PATH}/registrations/${page}`;
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
