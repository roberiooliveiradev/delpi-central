import { useEffect, useState } from "react";

export type PortalTourSessionSnapshot = {
  sessionActive: boolean;
  panelOpen: boolean;
  completed: boolean;
  dismissed: boolean;
  requiredDone: number;
  requiredTotal: number;
  progressPercent: number;
  explorerLevel: string;
};

export const DELPI_PORTAL_TOUR_SESSION_EVENT = "DELPI_PORTAL_TOUR_SESSION";
export const DELPI_PORTAL_TOUR_OPEN_PANEL_EVENT = "DELPI_PORTAL_TOUR_OPEN_PANEL";
export const DELPI_PORTAL_TOUR_RESUME_EVENT = "DELPI_PORTAL_TOUR_RESUME";
export const DELPI_PORTAL_TOUR_DISMISS_EVENT = "DELPI_PORTAL_TOUR_DISMISS";
export const DELPI_PORTAL_TOUR_HOME_REFRESH_EVENT = "DELPI_PORTAL_TOUR_HOME_REFRESH";

const DEFAULT_SNAPSHOT: PortalTourSessionSnapshot = {
  sessionActive: false,
  panelOpen: false,
  completed: false,
  dismissed: false,
  requiredDone: 0,
  requiredTotal: 0,
  progressPercent: 0,
  explorerLevel: "Explorador",
};

let snapshot: PortalTourSessionSnapshot = { ...DEFAULT_SNAPSHOT };

export function getPortalTourSessionSnapshot(): PortalTourSessionSnapshot {
  return snapshot;
}

export function publishPortalTourSession(
  partial: Partial<PortalTourSessionSnapshot>,
): void {
  const prevDismissed = snapshot.dismissed;
  const prevCompleted = snapshot.completed;
  snapshot = { ...snapshot, ...partial };
  window.dispatchEvent(
    new CustomEvent(DELPI_PORTAL_TOUR_SESSION_EVENT, {
      detail: snapshot,
    }),
  );
  if (
    snapshot.dismissed !== prevDismissed ||
    snapshot.completed !== prevCompleted ||
    (partial.sessionActive === true && prevDismissed)
  ) {
    window.dispatchEvent(new CustomEvent(DELPI_PORTAL_TOUR_HOME_REFRESH_EVENT));
  }
}

export function resetPortalTourSessionSnapshot(): void {
  snapshot = { ...DEFAULT_SNAPSHOT };
}

export function openPortalTourPanel(): void {
  window.dispatchEvent(new CustomEvent(DELPI_PORTAL_TOUR_OPEN_PANEL_EVENT));
}

export function resumePortalTour(): void {
  window.dispatchEvent(new CustomEvent(DELPI_PORTAL_TOUR_RESUME_EVENT));
}

export function dismissPortalTour(): void {
  window.dispatchEvent(new CustomEvent(DELPI_PORTAL_TOUR_DISMISS_EVENT));
}

export function usePortalTourSession(): PortalTourSessionSnapshot {
  const [state, setState] = useState(() => getPortalTourSessionSnapshot());

  useEffect(() => {
    const onChange = () => setState(getPortalTourSessionSnapshot());
    window.addEventListener(DELPI_PORTAL_TOUR_SESSION_EVENT, onChange);
    return () =>
      window.removeEventListener(DELPI_PORTAL_TOUR_SESSION_EVENT, onChange);
  }, []);

  return state;
}
