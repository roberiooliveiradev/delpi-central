import type { CoreApi, PortalTourProgressResponse, PortalTourStatus } from "../data/coreApi";
import {
  PORTAL_TOUR_VERSION,
  markPortalTourCompleted,
  resetPortalTour,
  shouldShowPortalTour,
} from "./portalTourStorage";

type PortalTourSyncPayload = {
  tourVersion: string;
  status: PortalTourStatus;
  completedQuestIds?: string[];
  completedQuestId?: string;
};

let syncTimer: number | null = null;
let pendingSync: PortalTourSyncPayload | null = null;
let syncChain: Promise<void> = Promise.resolve();

function enqueueSync(api: CoreApi, payload: PortalTourSyncPayload) {
  pendingSync = payload;
  if (syncTimer !== null) {
    window.clearTimeout(syncTimer);
  }
  syncTimer = window.setTimeout(() => {
    syncTimer = null;
    const next = pendingSync;
    pendingSync = null;
    if (!next) return;
    syncChain = syncChain
      .then(() => api.syncPortalTourProgress(next))
      .then(() => undefined)
      .catch(() => undefined);
  }, 650);
}

export function resolveShouldShowPortalTour(
  userId: string | undefined,
  remote: PortalTourProgressResponse | null,
): boolean {
  if (!userId) return false;

  if (
    remote?.tourVersion === PORTAL_TOUR_VERSION &&
    remote.status === "completed"
  ) {
    return false;
  }

  return shouldShowPortalTour(userId);
}

export function hydrateCompletedQuestIds(
  remote: PortalTourProgressResponse | null,
): Set<string> {
  if (
    !remote?.completedQuestIds?.length ||
    remote.tourVersion !== PORTAL_TOUR_VERSION
  ) {
    return new Set();
  }
  return new Set(remote.completedQuestIds);
}

export async function loadPortalTourProgress(
  api: CoreApi,
): Promise<PortalTourProgressResponse | null> {
  try {
    return await api.getPortalTourProgress();
  } catch {
    return null;
  }
}

export function syncPortalTourStarted(api: CoreApi, completedQuestIds: string[]) {
  enqueueSync(api, {
    tourVersion: PORTAL_TOUR_VERSION,
    status: "exploring",
    completedQuestIds,
  });
}

export function syncPortalTourQuestCompleted(
  api: CoreApi,
  completedQuestIds: string[],
  questId: string,
) {
  enqueueSync(api, {
    tourVersion: PORTAL_TOUR_VERSION,
    status: "exploring",
    completedQuestIds,
    completedQuestId: questId,
  });
}

export function syncPortalTourFinished(
  api: CoreApi,
  completed: boolean,
  completedQuestIds: string[],
) {
  if (syncTimer !== null) {
    window.clearTimeout(syncTimer);
    syncTimer = null;
  }
  pendingSync = null;

  const status: PortalTourStatus = completed ? "completed" : "dismissed";
  syncChain = syncChain
    .then(() =>
      api.syncPortalTourProgress({
        tourVersion: PORTAL_TOUR_VERSION,
        status,
        completedQuestIds,
      }),
    )
    .then(() => undefined)
    .catch(() => undefined);
}

export async function restartPortalTourRemote(
  api: CoreApi,
  userId: string,
): Promise<void> {
  if (syncTimer !== null) {
    window.clearTimeout(syncTimer);
    syncTimer = null;
  }
  pendingSync = null;
  resetPortalTour(userId);
  try {
    await api.resetPortalTourProgress();
  } catch {
    // localStorage já limpo; falha remota não bloqueia reinício
  }
}

export function markPortalTourCompletedEverywhere(userId: string) {
  markPortalTourCompleted(userId);
}
