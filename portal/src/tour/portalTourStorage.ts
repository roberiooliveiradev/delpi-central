const STORAGE_KEY = "delpi.portal.tourState.v1";

/** Incrementar quando houver novidades que exijam reexibir o tour. */
export const PORTAL_TOUR_VERSION = "2026-06-portal-v6-explore";

type TourState = {
  completedVersion: string | null;
};

function readState(): Record<string, TourState> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Record<string, TourState>;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function writeState(state: Record<string, TourState>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function shouldShowPortalTour(userId: string | undefined): boolean {
  if (!userId) return false;
  const state = readState()[userId];
  return state?.completedVersion !== PORTAL_TOUR_VERSION;
}

export function markPortalTourCompleted(userId: string) {
  const all = readState();
  all[userId] = { completedVersion: PORTAL_TOUR_VERSION };
  writeState(all);
}

export function resetPortalTour(userId: string) {
  const all = readState();
  delete all[userId];
  writeState(all);
}
