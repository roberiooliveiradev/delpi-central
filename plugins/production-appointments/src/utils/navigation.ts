import type { BranchRouteCode } from "../constants/branches";
import { branchHomePath } from "../constants/routes";

let navStackDepth = 0;
let suppressPopstateDepthChange = false;

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    if (suppressPopstateDepthChange) return;
    navStackDepth = Math.max(0, navStackDepth - 1);
  });
}

export function navigateAppointments(path: string) {
  if (typeof window === "undefined") return;
  const questionIndex = path.indexOf("?");
  const basePath = questionIndex >= 0 ? path.slice(0, questionIndex) : path;
  const query = questionIndex >= 0 ? path.slice(questionIndex) : "";

  if (window.location.pathname === basePath && window.location.search === query) {
    return;
  }

  window.history.pushState(null, "", path);
  navStackDepth += 1;
  suppressPopstateDepthChange = true;
  window.dispatchEvent(new PopStateEvent("popstate"));
  suppressPopstateDepthChange = false;
}

export function navigateAppointmentsBack(branchRoute: BranchRouteCode) {
  if (typeof window === "undefined") return;
  if (navStackDepth > 0) {
    window.history.back();
    return;
  }
  navigateAppointments(branchHomePath(branchRoute));
}
