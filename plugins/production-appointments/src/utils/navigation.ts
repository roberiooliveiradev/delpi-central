import { PRODUCTION_APPOINTMENTS_BASE_PATH } from "../constants/branches";

export const APPOINTMENTS_ROUTE_CHANGE_EVENT = "delpi:production-appointments:route";

let navStackDepth = 0;
let suppressPopstateDepthChange = false;

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    if (suppressPopstateDepthChange) return;
    navStackDepth = Math.max(0, navStackDepth - 1);
  });
}

function notifyRouteChange(pathname: string) {
  window.dispatchEvent(
    new CustomEvent(APPOINTMENTS_ROUTE_CHANGE_EVENT, { detail: { pathname } }),
  );
}

export function navigateAppointments(path: string) {
  if (typeof window === "undefined") return;
  const questionIndex = path.indexOf("?");
  const basePath = questionIndex >= 0 ? path.slice(0, questionIndex) : path;
  const query = questionIndex >= 0 ? path.slice(questionIndex) : "";

  if (window.location.pathname === basePath && window.location.search === query) {
    notifyRouteChange(basePath);
    return;
  }

  window.history.pushState(null, "", path);
  navStackDepth += 1;
  suppressPopstateDepthChange = true;
  notifyRouteChange(basePath);
  window.dispatchEvent(new PopStateEvent("popstate"));
  suppressPopstateDepthChange = false;
}

export function navigateAppointmentsBack(branchRoute: "SC" | "ES") {
  if (typeof window === "undefined") return;
  if (navStackDepth > 0) {
    window.history.back();
    return;
  }
  navigateAppointments(`${PRODUCTION_APPOINTMENTS_BASE_PATH}/${branchRoute.toLowerCase()}`);
}
