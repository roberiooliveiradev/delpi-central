import type { CoreApi, PortalTourProgressResponse, PortalTourStatus } from "../data/coreApi";
import {
  PORTAL_TOUR_VERSION,
  markPortalTourCompleted,
  resetPortalTour,
  shouldShowPortalTour,
} from "./portalTourStorage";
import { publishPortalTourSyncStatus } from "./portalTourSyncStatus";

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
      .then(() => {
        publishPortalTourSyncStatus(false);
        return undefined;
      })
      .catch(() => {
        publishPortalTourSyncStatus(true);
        return undefined;
      });
  }, 650);
}

export function isPortalTourFullyCompleted(
  userId: string | undefined,
  remote: PortalTourProgressResponse | null,
): boolean {
  if (!userId) return true;

  if (
    remote?.tourVersion === PORTAL_TOUR_VERSION &&
    remote.status === "completed"
  ) {
    return true;
  }

  return !shouldShowPortalTour(userId);
}

export function resolveShouldShowPortalTour(
  userId: string | undefined,
  remote: PortalTourProgressResponse | null,
): boolean {
  return !isPortalTourFullyCompleted(userId, remote);
}

export function isResumablePortalTourProgress(
  remote: PortalTourProgressResponse | null,
): boolean {
  if (!remote?.tourVersion || remote.tourVersion !== PORTAL_TOUR_VERSION) {
    return false;
  }
  if (remote.status === "completed") return false;
  return (
    remote.status === "exploring" ||
    remote.status === "dismissed" ||
    remote.completedQuestIds.length > 0 ||
    Boolean(remote.startedAt)
  );
}

export function shouldAutoOpenPortalTourPanel(
  remote: PortalTourProgressResponse | null,
): boolean {
  return !isResumablePortalTourProgress(remote);
}

export function normalizePortalTourProgressResponse(
  remote: PortalTourProgressResponse | null,
): PortalTourProgressResponse | null {
  if (!remote?.tourVersion || remote.tourVersion !== PORTAL_TOUR_VERSION) {
    return remote;
  }
  if (remote.status !== "dismissed") {
    return remote;
  }
  return {
    ...remote,
    status: "exploring",
  };
}

export async function repairLegacyDismissedPortalTour(
  api: CoreApi,
  remote: PortalTourProgressResponse | null,
): Promise<PortalTourProgressResponse | null> {
  const normalized = normalizePortalTourProgressResponse(remote);
  if (
    !remote ||
    remote.tourVersion !== PORTAL_TOUR_VERSION ||
    remote.status !== "dismissed"
  ) {
    return normalized;
  }

  try {
    await api.syncPortalTourProgress({
      tourVersion: PORTAL_TOUR_VERSION,
      status: "exploring",
      completedQuestIds: remote.completedQuestIds,
    });
  } catch {
    // Falha remota não bloqueia retomada local
  }

  return normalized;
}

export function hydrateCompletedQuestIds(
  remote: PortalTourProgressResponse | null,
): Set<string> {
  if (!remote?.completedQuestIds?.length) {
    return new Set();
  }
  if (remote.tourVersion !== PORTAL_TOUR_VERSION) {
    return new Set();
  }
  return new Set(remote.completedQuestIds);
}

/** Reabrir painel sem apagar progresso (explorando ou já concluído). */
export function canReopenPortalTourPanel(
  remote: PortalTourProgressResponse | null,
): boolean {
  if (!remote?.tourVersion || remote.tourVersion !== PORTAL_TOUR_VERSION) {
    return false;
  }
  return (
    remote.status === "exploring" ||
    remote.status === "dismissed" ||
    remote.status === "completed" ||
    remote.completedQuestIds.length > 0 ||
    Boolean(remote.startedAt)
  );
}

export function shouldSkipPortalTourSyncOnOpen(
  remote: PortalTourProgressResponse | null,
): boolean {
  return (
    remote?.tourVersion === PORTAL_TOUR_VERSION && remote.status === "completed"
  );
}

export function hydratePortalTourSessionFromRemote(
  remote: PortalTourProgressResponse | null,
): Set<string> {
  if (!canReopenPortalTourPanel(remote)) {
    return new Set();
  }
  return hydrateCompletedQuestIds(remote);
}

export function repairLocalCompletedWhenRemoteIncomplete(
  userId: string,
  remote: PortalTourProgressResponse | null,
): void {
  if (!userId || !remote?.tourVersion) return;
  if (remote.tourVersion !== PORTAL_TOUR_VERSION) return;
  if (remote.status === "completed") return;
  if (!shouldShowPortalTour(userId)) {
    resetPortalTour(userId);
  }
}

export async function loadPortalTourProgress(
  api: CoreApi,
  userId?: string,
): Promise<PortalTourProgressResponse | null> {
  try {
    const remote = await api.getPortalTourProgress();
    const repaired = await repairLegacyDismissedPortalTour(api, remote);
    if (userId) {
      repairLocalCompletedWhenRemoteIncomplete(userId, repaired);
    }
    return repaired;
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

export function syncPortalTourCompleted(
  api: CoreApi,
  completedQuestIds: string[],
) {
  if (syncTimer !== null) {
    window.clearTimeout(syncTimer);
    syncTimer = null;
  }
  pendingSync = null;

  syncChain = syncChain
    .then(() =>
      api.syncPortalTourProgress({
        tourVersion: PORTAL_TOUR_VERSION,
        status: "completed",
        completedQuestIds,
      }),
    )
    .then(() => {
      publishPortalTourSyncStatus(false);
      return undefined;
    })
    .catch(() => {
      publishPortalTourSyncStatus(true);
      return undefined;
    });
}

/** @deprecated Use syncPortalTourCompleted — «pular» não existe mais. */
export function syncPortalTourFinished(
  api: CoreApi,
  completed: boolean,
  completedQuestIds: string[],
) {
  if (completed) {
    syncPortalTourCompleted(api, completedQuestIds);
    return;
  }
  syncPortalTourStarted(api, completedQuestIds);
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
