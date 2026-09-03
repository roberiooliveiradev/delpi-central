import type {
  CoreApi,
  PortalTourCatalogResponse,
  PortalTourProgressResponse,
  PortalTourStatus,
} from "../data/coreApi";
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

function hasPendingNewRequiredQuests(
  remote: PortalTourProgressResponse | null,
  catalog: PortalTourCatalogResponse | null | undefined,
): boolean {
  if (!catalog?.newQuestIds?.length || !catalog.requiredQuestIds?.length) {
    return false;
  }
  const done = new Set(remote?.completedQuestIds ?? []);
  const requiredNew = catalog.newQuestIds.filter((id) =>
    catalog.requiredQuestIds.includes(id),
  );
  return requiredNew.some((id) => !done.has(id));
}

/** Há desafio obrigatório do catálogo ainda sem conclusão (inclui novidades). */
function hasIncompleteRequiredQuests(
  remote: PortalTourProgressResponse | null,
  catalog: PortalTourCatalogResponse | null | undefined,
): boolean {
  if (!catalog?.requiredQuestIds?.length) {
    return false;
  }
  const done = new Set(remote?.completedQuestIds ?? []);
  return catalog.requiredQuestIds.some((id) => !done.has(id));
}

/** Exposto para home entry / login — novidades obrigatórias ainda pendentes. */
export function hasPendingNewPortalTourQuests(
  remote: PortalTourProgressResponse | null,
  catalog: PortalTourCatalogResponse | null | undefined,
): boolean {
  return hasPendingNewRequiredQuests(remote, catalog);
}

export function isPortalTourDismissed(
  remote: PortalTourProgressResponse | null,
  catalog?: PortalTourCatalogResponse | null,
): boolean {
  if (remote?.status !== "dismissed") return false;
  // Bump com novidades obrigatórias: «Agora não» da versão anterior não esconde o card.
  if (hasPendingNewRequiredQuests(remote, catalog)) return false;
  if (hasIncompleteRequiredQuests(remote, catalog) && remote.tourVersion !== PORTAL_TOUR_VERSION) {
    return false;
  }
  return true;
}

/**
 * Tour completo só quando todos os obrigatórios do catálogo estão feitos
 * e o status/localStorage batem com a versão atual.
 * Quem concluiu uma versão antiga (ou ficou com status completed desatualizado)
 * continua incompleto até fechar as quests novas.
 */
export function isPortalTourFullyCompleted(
  userId: string | undefined,
  remote: PortalTourProgressResponse | null,
  catalog?: PortalTourCatalogResponse | null,
): boolean {
  if (!userId) return true;

  if (hasIncompleteRequiredQuests(remote, catalog)) {
    return false;
  }

  if (
    remote?.tourVersion === PORTAL_TOUR_VERSION &&
    remote.status === "completed"
  ) {
    return true;
  }

  // Progresso antigo (outra versão) sem pendências no catálogo: trata como
  // concluído só se o localStorage também marcar a versão atual — senão reabre pelo bump.
  return !shouldShowPortalTour(userId);
}

export function resolveShouldShowPortalTour(
  userId: string | undefined,
  remote: PortalTourProgressResponse | null,
  catalog?: PortalTourCatalogResponse | null,
): boolean {
  if (isPortalTourDismissed(remote, catalog)) {
    return false;
  }
  return !isPortalTourFullyCompleted(userId, remote, catalog);
}

/**
 * Sessão em background (watch de cliques) só quando o usuário já aceitou explorar.
 * «Agora não» e 1º acesso sem clique explícito não ativam detecção.
 */
export function shouldActivatePortalTourSession(
  remote: PortalTourProgressResponse | null,
  catalog?: PortalTourCatalogResponse | null,
): boolean {
  if (isPortalTourDismissed(remote, catalog)) {
    return false;
  }
  if (remote?.status === "exploring") {
    return hasIncompleteRequiredQuests(remote, catalog) || remote.completedQuestIds.length > 0;
  }
  if (
    remote?.status === "completed" &&
    hasIncompleteRequiredQuests(remote, catalog)
  ) {
    return true;
  }
  return false;
}

export function isResumablePortalTourProgress(
  remote: PortalTourProgressResponse | null,
  catalog?: PortalTourCatalogResponse | null,
): boolean {
  if (!remote?.tourVersion) return false;
  if (isPortalTourDismissed(remote, catalog)) return false;

  if (remote.tourVersion !== PORTAL_TOUR_VERSION) {
    if (hasIncompleteRequiredQuests(remote, catalog)) return true;
    return (
      remote.completedQuestIds.length > 0 ||
      remote.status === "completed" ||
      remote.status === "exploring" ||
      Boolean(remote.startedAt)
    );
  }

  if (remote.status === "completed") {
    return hasIncompleteRequiredQuests(remote, catalog);
  }
  return (
    remote.status === "exploring" ||
    remote.completedQuestIds.length > 0 ||
    Boolean(remote.startedAt)
  );
}

/** Getting started opt-in: nunca abre o painel sozinho. */
export function shouldAutoOpenPortalTourPanel(
  _remote?: PortalTourProgressResponse | null,
  _catalog?: PortalTourCatalogResponse | null,
): boolean {
  return false;
}

export function hydrateCompletedQuestIds(
  remote: PortalTourProgressResponse | null,
): Set<string> {
  if (!remote?.completedQuestIds?.length) {
    return new Set();
  }
  // Preserva conclusões entre bumps de versão (só as quests novas ficam pendentes).
  return new Set(remote.completedQuestIds);
}

/** Reabrir painel sem apagar progresso (explorando ou já concluído). */
export function canReopenPortalTourPanel(
  remote: PortalTourProgressResponse | null,
  catalog?: PortalTourCatalogResponse | null,
): boolean {
  if (!remote?.tourVersion) return false;
  if (isPortalTourDismissed(remote, catalog)) {
    // Perfil «Continuar explorando» ainda pode reabrir após Agora não.
    return true;
  }
  if (remote.tourVersion !== PORTAL_TOUR_VERSION) {
    return (
      hasPendingNewRequiredQuests(remote, catalog) ||
      remote.status === "completed" ||
      remote.status === "exploring" ||
      remote.status === "dismissed" ||
      remote.completedQuestIds.length > 0 ||
      Boolean(remote.startedAt)
    );
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
  catalog?: PortalTourCatalogResponse | null,
): boolean {
  if (hasIncompleteRequiredQuests(remote, catalog)) {
    return false;
  }
  return (
    remote?.tourVersion === PORTAL_TOUR_VERSION && remote.status === "completed"
  );
}

export function hydratePortalTourSessionFromRemote(
  remote: PortalTourProgressResponse | null,
  catalog?: PortalTourCatalogResponse | null,
): Set<string> {
  if (!canReopenPortalTourPanel(remote, catalog)) {
    return new Set();
  }
  return hydrateCompletedQuestIds(remote);
}

export function repairLocalCompletedWhenRemoteIncomplete(
  userId: string,
  remote: PortalTourProgressResponse | null,
  catalog?: PortalTourCatalogResponse | null,
): void {
  if (!userId) return;
  // Novidades: limpa “concluído” local para o card da home e o login reabrirem.
  if (
    hasPendingNewRequiredQuests(remote, catalog) ||
    hasIncompleteRequiredQuests(remote, catalog)
  ) {
    resetPortalTour(userId);
    return;
  }
  if (!remote?.tourVersion) return;
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
    if (userId) {
      repairLocalCompletedWhenRemoteIncomplete(userId, remote);
    }
    return remote;
  } catch {
    return null;
  }
}

export function syncPortalTourStarted(api: CoreApi, completedQuestIds: string[]) {
  const payload: PortalTourSyncPayload = {
    tourVersion: PORTAL_TOUR_VERSION,
    status: "exploring",
  };
  // Lista vazia no PATCH substitui o progresso remoto — omitir evita zerar ao retomar.
  if (completedQuestIds.length > 0) {
    payload.completedQuestIds = completedQuestIds;
  }
  enqueueSync(api, payload);
}

export function syncPortalTourDismissed(
  api: CoreApi,
  completedQuestIds: string[],
) {
  if (syncTimer !== null) {
    window.clearTimeout(syncTimer);
    syncTimer = null;
  }
  pendingSync = null;

  const payload: PortalTourSyncPayload = {
    tourVersion: PORTAL_TOUR_VERSION,
    status: "dismissed",
  };
  if (completedQuestIds.length > 0) {
    payload.completedQuestIds = completedQuestIds;
  }

  syncChain = syncChain
    .then(() => api.syncPortalTourProgress(payload))
    .then(() => {
      publishPortalTourSyncStatus(false);
      return undefined;
    })
    .catch(() => {
      publishPortalTourSyncStatus(true);
      return undefined;
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

/** @deprecated Prefer syncPortalTourCompleted ou syncPortalTourDismissed. */
export function syncPortalTourFinished(
  api: CoreApi,
  completed: boolean,
  completedQuestIds: string[],
) {
  if (completed) {
    syncPortalTourCompleted(api, completedQuestIds);
    return;
  }
  syncPortalTourDismissed(api, completedQuestIds);
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
