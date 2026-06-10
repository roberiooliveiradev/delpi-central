import type { PortalTourCatalogResponse, PortalTourProgressResponse } from "../data/coreApi";
import {
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
  panelOpen: boolean,
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

  const tourCompleted = isPortalTourFullyCompleted(userId, progress);

  if (tourCompleted || panelOpen) {
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

  const completedIds = new Set(
    normalizedProgress?.tourVersion === catalog.tourVersion
      ? normalizedProgress.completedQuestIds
      : [],
  );

  const requiredTotal = catalog.requiredQuestIds.length;
  const requiredDone = catalog.requiredQuestIds.filter((id) =>
    completedIds.has(id),
  ).length;
  const progressPercent =
    requiredTotal > 0 ? Math.round((requiredDone / requiredTotal) * 100) : 0;

  const visible =
    !tourCompleted && progressPercent < 100 && !panelOpen && requiredTotal > 0;

  return {
    ready: true,
    visible,
    requiredDone,
    requiredTotal,
    progressPercent: catalog.progressPercent ?? progressPercent,
    explorerLevel: catalog.explorerLevel ?? "Explorador",
  };
}
