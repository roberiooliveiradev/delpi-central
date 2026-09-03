import type { PortalTourCatalogResponse, PortalTourProgressResponse } from "../data/coreApi";
import {
  hasPendingNewPortalTourQuests,
  isPortalTourDismissed,
  isPortalTourFullyCompleted,
} from "./portalTourPersistence";

export type PortalTourHomeEntryState = {
  ready: boolean;
  visible: boolean;
  requiredDone: number;
  requiredTotal: number;
  progressPercent: number;
  explorerLevel: string;
  newQuestCount: number;
};

export function resolvePortalTourHomeEntryState(
  userId: string | undefined,
  progress: PortalTourProgressResponse | null,
  catalog: PortalTourCatalogResponse | null,
): PortalTourHomeEntryState {
  const empty: PortalTourHomeEntryState = {
    ready: Boolean(catalog),
    visible: false,
    requiredDone: 0,
    requiredTotal: 0,
    progressPercent: 0,
    explorerLevel: "Explorador",
    newQuestCount: 0,
  };

  if (!userId) {
    return empty;
  }

  const pendingNew = hasPendingNewPortalTourQuests(progress, catalog);
  const tourCompleted = isPortalTourFullyCompleted(userId, progress, catalog);
  const dismissed = isPortalTourDismissed(progress, catalog);

  // Agora não: esconde card até bump com novidades ou retomada no perfil.
  if (dismissed) {
    return { ...empty, ready: true };
  }

  // Tour 100% na versão atual e sem novidades → esconde o card.
  if (tourCompleted && !pendingNew) {
    return { ...empty, ready: true };
  }

  if (!catalog?.requiredQuestIds.length) {
    return {
      ready: true,
      visible: true,
      requiredDone: progress?.completedQuestIds?.length ?? 0,
      requiredTotal: 0,
      progressPercent: 0,
      explorerLevel: "Explorador",
      newQuestCount: catalog?.newQuestIds?.length ?? 0,
    };
  }

  const completedIds = new Set(progress?.completedQuestIds ?? []);

  const requiredTotal = catalog.requiredQuestIds.length;
  const requiredDone = catalog.requiredQuestIds.filter((id) =>
    completedIds.has(id),
  ).length;
  const progressPercent =
    requiredTotal > 0 ? Math.round((requiredDone / requiredTotal) * 100) : 0;

  const newQuestCount = (catalog.newQuestIds ?? []).filter(
    (id) => catalog.requiredQuestIds.includes(id) && !completedIds.has(id),
  ).length;

  // Card na home enquanto houver desafio obrigatório pendente (inclui novidades pós-conclusão).
  const visible = requiredTotal > 0 && (progressPercent < 100 || pendingNew);

  return {
    ready: true,
    visible,
    requiredDone,
    requiredTotal,
    progressPercent: catalog.progressPercent ?? progressPercent,
    explorerLevel: catalog.explorerLevel ?? "Explorador",
    newQuestCount,
  };
}

/**
 * Visibilidade na home antes/depois do GET de progresso.
 * «Agora não» só existe no remoto — não usar localStorage de “não concluído”
 * como preview, senão o card pisca e some no F5.
 */
export function resolvePortalTourHomeVisible(input: {
  hasUser: boolean;
  coreLoaded: boolean;
  sessionDismissed: boolean;
  sessionCompleted: boolean;
  dataReady: boolean;
  entryVisible: boolean;
  cachedVisible: boolean | null;
}): boolean {
  if (!input.hasUser || !input.coreLoaded) return false;
  if (input.sessionDismissed || input.sessionCompleted) return false;
  if (input.dataReady) return input.entryVisible;
  return input.cachedVisible === true;
}
