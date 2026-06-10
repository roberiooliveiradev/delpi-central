import type {
  PortalTourQuest,
  PortalTourQuestCategory,
} from "./portalTourQuestTypes";
import { PORTAL_TOUR_CATEGORY_LABELS } from "./portalTourQuestTypes";
import { countCompletedRequired, countRequiredQuests } from "./portalTourQuests";

export const QUEST_XP_REQUIRED = 10;
export const QUEST_XP_OPTIONAL = 5;

export type ExplorerLevel = {
  minPercent: number;
  label: string;
};

export const EXPLORER_LEVELS: ExplorerLevel[] = [
  { minPercent: 0, label: "Explorador" },
  { minPercent: 25, label: "Curioso" },
  { minPercent: 50, label: "Expert" },
  { minPercent: 75, label: "Embaixador DELPI" },
  { minPercent: 100, label: "Mestre DELPI" },
];

export const PROGRESS_MILESTONES = [25, 50, 75] as const;

export type QuestCelebrationToast = {
  id: string;
  title: string;
  xp: number;
  categoryLabel: string;
};

export function resolveQuestXp(quest: PortalTourQuest): number {
  if (typeof quest.xpReward === "number") return quest.xpReward;
  return quest.optional ? QUEST_XP_OPTIONAL : QUEST_XP_REQUIRED;
}

export function computeEarnedXp(
  quests: PortalTourQuest[],
  completedIds: ReadonlySet<string>,
): number {
  return quests.reduce((total, quest) => {
    if (!completedIds.has(quest.id)) return total;
    return total + resolveQuestXp(quest);
  }, 0);
}

export function computeProgressPercent(
  quests: PortalTourQuest[],
  completedIds: ReadonlySet<string>,
): number {
  const requiredTotal = countRequiredQuests(quests);
  if (requiredTotal <= 0) return 0;
  const requiredDone = countCompletedRequired(quests, completedIds);
  return Math.round((requiredDone / requiredTotal) * 100);
}

export function resolveExplorerLevel(progressPercent: number): ExplorerLevel {
  const clamped = Math.min(100, Math.max(0, progressPercent));
  let current = EXPLORER_LEVELS[0];
  for (const level of EXPLORER_LEVELS) {
    if (clamped >= level.minPercent) current = level;
  }
  return current;
}

export function isCategoryComplete(
  quests: PortalTourQuest[],
  category: PortalTourQuestCategory,
  completedIds: ReadonlySet<string>,
): boolean {
  const requiredInCategory = quests.filter(
    (quest) => quest.category === category && !quest.optional,
  );
  if (!requiredInCategory.length) return false;
  return requiredInCategory.every((quest) => completedIds.has(quest.id));
}

export function resolveCategoryJustCompleted(
  quests: PortalTourQuest[],
  before: ReadonlySet<string>,
  after: ReadonlySet<string>,
  category: PortalTourQuestCategory,
): string | null {
  if (!isCategoryComplete(quests, category, after)) return null;
  if (isCategoryComplete(quests, category, before)) return null;
  return PORTAL_TOUR_CATEGORY_LABELS[category];
}

export function resolveNewMilestone(
  previousPercent: number,
  nextPercent: number,
): number | null {
  for (const milestone of PROGRESS_MILESTONES) {
    if (previousPercent < milestone && nextPercent >= milestone) {
      return milestone;
    }
  }
  return null;
}

export function resolveExplorerLevelUp(
  previousPercent: number,
  nextPercent: number,
): ExplorerLevel | null {
  const before = resolveExplorerLevel(previousPercent);
  const after = resolveExplorerLevel(nextPercent);
  if (before.minPercent === after.minPercent) return null;
  if (after.minPercent <= 0) return null;
  return after;
}

export function levelUpMessage(level: ExplorerLevel): string {
  switch (level.minPercent) {
    case 25:
      return "Você subiu de nível — bem-vindo ao clube Curioso!";
    case 50:
      return "Nível Expert desbloqueado — você está arrasando!";
    case 75:
      return "Embaixador DELPI — quase no topo!";
    case 100:
      return "Mestre DELPI — você dominou o portal!";
    default:
      return `Parabéns! Novo nível: ${level.label}!`;
  }
}

export function milestoneMessage(milestone: number): string {
  switch (milestone) {
    case 25:
      return "Primeiro quarto concluído — continue explorando!";
    case 50:
      return "Metade do caminho — você está indo muito bem!";
    case 75:
      return "Quase lá — falta pouco para dominar o portal!";
    default:
      return `Marco de ${milestone}% alcançado!`;
  }
}
