import type { PortalTourCatalogResponse, PortalTourProgressResponse } from "../data/coreApi";
import {
  hasPendingNewPortalTourQuests,
  isPortalTourFullyCompleted,
} from "./portalTourPersistence";

export type PortalTourHomeEntryState = {
  ready: boolean;
  visible: boolean;
  requiredDone: number;
  requiredTotal: number;
  progressPercent: number;
  explorerLevel: string;
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
  };

  if (!userId) {
    return empty;
  }

  const pendingNew = hasPendingNewPortalTourQuests(progress, catalog);
  const tourCompleted = isPortalTourFullyCompleted(userId, progress, catalog);

  // Tour 100% na versão atual e sem novidades → esconde o card.
  if (tourCompleted && !pendingNew) {
    return { ...empty, ready: true };
  }

  const normalizedProgress =
    progress?.status === "dismissed"
      ? { ...progress, status: "exploring" as const }
      : progress;

  if (!catalog?.requiredQuestIds.length) {
    return {
      ready: true,
      visible: true,
      requiredDone: normalizedProgress?.completedQuestIds?.length ?? 0,
      requiredTotal: 0,
      progressPercent: 0,
      explorerLevel: "Explorador",
    };
  }

  const completedIds = new Set(normalizedProgress?.completedQuestIds ?? []);

  const requiredTotal = catalog.requiredQuestIds.length;
  const requiredDone = catalog.requiredQuestIds.filter((id) =>
    completedIds.has(id),
  ).length;
  const progressPercent =
    requiredTotal > 0 ? Math.round((requiredDone / requiredTotal) * 100) : 0;

  // Card na home enquanto houver desafio obrigatório pendente (inclui novidades pós-conclusão).
  const visible = requiredTotal > 0 && (progressPercent < 100 || pendingNew);

  return {
    ready: true,
    visible,
    requiredDone,
    requiredTotal,
    progressPercent: catalog.progressPercent ?? progressPercent,
    explorerLevel: catalog.explorerLevel ?? "Explorador",
  };
}
