import type { PortalTourCatalogResponse } from "../data/coreApi";
import type {
  PortalTourQuest,
  PortalTourQuestCategory,
} from "./portalTourQuestTypes";
import { countCompletedRequired, countRequiredQuests } from "./portalTourQuests";

export function alignQuestsWithCatalog(
  localQuests: PortalTourQuest[],
  catalog: PortalTourCatalogResponse | null,
): PortalTourQuest[] {
  if (!catalog?.quests.length) return localQuests;

  const metaById = new Map(catalog.quests.map((quest) => [quest.id, quest]));
  const availableIds = new Set(catalog.quests.map((quest) => quest.id));

  return localQuests
    .filter((quest) => availableIds.has(quest.id))
    .map((quest) => {
      const meta = metaById.get(quest.id);
      if (!meta) return quest;

      return {
        ...quest,
        title: meta.title,
        hint: meta.hint,
        category: meta.category as PortalTourQuestCategory,
        optional: meta.optional,
      };
    });
}

export function resolveRequiredQuestTotal(
  catalog: PortalTourCatalogResponse | null,
  quests: PortalTourQuest[],
): number {
  if (catalog?.requiredQuestIds.length) {
    return catalog.requiredQuestIds.length;
  }
  return countRequiredQuests(quests);
}

export function resolveCompletedRequiredCount(
  catalog: PortalTourCatalogResponse | null,
  quests: PortalTourQuest[],
  completedIds: ReadonlySet<string>,
): number {
  if (catalog?.requiredQuestIds.length) {
    return catalog.requiredQuestIds.filter((id) => completedIds.has(id)).length;
  }
  return countCompletedRequired(quests, completedIds);
}

export function resolveProgressPercentFromCatalog(
  catalog: PortalTourCatalogResponse | null,
  quests: PortalTourQuest[],
  completedIds: ReadonlySet<string>,
): number {
  const requiredTotal = resolveRequiredQuestTotal(catalog, quests);
  if (requiredTotal <= 0) return 0;
  const requiredDone = resolveCompletedRequiredCount(catalog, quests, completedIds);
  return Math.round((requiredDone / requiredTotal) * 100);
}

export function isQuestMarkedNew(
  catalog: PortalTourCatalogResponse | null,
  questId: string,
): boolean {
  if (!catalog) return false;
  return catalog.newQuestIds.includes(questId);
}

export function resolveNewQuestsBannerMessage(
  catalog: PortalTourCatalogResponse | null,
): string | null {
  if (!catalog?.newQuestIds.length) return null;
  const count = catalog.newQuestIds.length;
  if (count === 1) {
    return "1 novidade nesta versão — explore o desafio marcado!";
  }
  return `${count} novidades nesta versão — explore os desafios marcados!`;
}
