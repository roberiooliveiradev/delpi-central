import { isSafeNavigationHref } from "../components/layout/PagePath";

/** Portal shell listens and SPA-navigates (must stay in sync with portal/hostNavigation). */
export const DELPI_HOST_NAVIGATE_EVENT = "DELPI_HOST_NAVIGATE";

export const DELPI_HOST_NAVIGATE_HANDLED_EVENT = "DELPI_HOST_NAVIGATE_HANDLED";

/** Canonical Minha DELPI self-profile (Portal host). */
export const HOST_SELF_PROFILE_PATH = "/profile";

export type HostNavigateDetail = {
  path: string;
};

/**
 * Ask the Portal host to leave the federated app via React Router.
 * Falls back to location.assign when no Portal listener is present.
 */
export function navigateHostPath(path: string): void {
  if (typeof window === "undefined") return;
  const value = (path || "").trim();
  if (!isSafeNavigationHref(value)) {
    throw new Error("navigateHostPath exige path absoluto interno ao host.");
  }

  let handled = false;
  const onHandled = () => {
    handled = true;
  };
  window.addEventListener(DELPI_HOST_NAVIGATE_HANDLED_EVENT, onHandled, {
    once: true,
  });
  window.dispatchEvent(
    new CustomEvent<HostNavigateDetail>(DELPI_HOST_NAVIGATE_EVENT, {
      detail: { path: value },
    }),
  );
  window.removeEventListener(DELPI_HOST_NAVIGATE_HANDLED_EVENT, onHandled);

  if (!handled) {
    window.location.assign(value);
  }
}
