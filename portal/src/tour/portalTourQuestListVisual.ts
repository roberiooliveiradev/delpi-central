import type {
  PortalTourQuest,
  PortalTourQuestCategory,
} from "./portalTourQuestTypes";
import { isQuestAvailable } from "./portalTourQuests";
import { scopeMatchesRoute } from "./portalTourTargetVisibility";

export type PortalTourQuestListVisualState =
  | "done"
  | "near"
  | "pending"
  | "locked";

const SHELL_SCOPES = new Set<PortalTourQuest["scope"]>([
  "sidebar",
  "launcher",
  "home",
]);

/** Pendentes (near → pending → locked) antes dos concluídos. */
const LIST_STATE_ORDER: Record<PortalTourQuestListVisualState, number> = {
  near: 0,
  pending: 1,
  locked: 2,
  done: 3,
};

/** Está na página/área de referência do desafio (não exige alvo visível). */
export function isQuestOnReferencePage(quest: PortalTourQuest): boolean {
  return scopeMatchesRoute(quest.scope);
}

/**
 * Estado visual canônico da lista do companion.
 * - done: concluído (muted)
 * - near: pendente na página de referência (glow success)
 * - pending: pendente fora da página (legível, sem glow)
 * - locked: pendente de shell bloqueado fora da área (mais muted que pending)
 */
export function resolveQuestListVisualState(
  quest: PortalTourQuest,
  done: boolean,
): PortalTourQuestListVisualState {
  if (done) return "done";
  if (isQuestOnReferencePage(quest)) return "near";
  if (!isQuestAvailable(quest) && SHELL_SCOPES.has(quest.scope)) {
    return "locked";
  }
  return "pending";
}

/** Dentro da categoria: o que falta sobe; «Perto» primeiro. */
export function sortQuestsForCompanionList(
  quests: readonly PortalTourQuest[],
  completedIds: ReadonlySet<string>,
): PortalTourQuest[] {
  return [...quests].sort((left, right) => {
    const leftState = resolveQuestListVisualState(
      left,
      completedIds.has(left.id),
    );
    const rightState = resolveQuestListVisualState(
      right,
      completedIds.has(right.id),
    );
    return LIST_STATE_ORDER[leftState] - LIST_STATE_ORDER[rightState];
  });
}

/** Categorias com desafio pendente sobem; ordem canônica entre empates. */
export function orderCategoriesPendingFirst(
  categories: readonly PortalTourQuestCategory[],
  questsByCategory: Map<PortalTourQuestCategory, PortalTourQuest[]>,
  completedIds: ReadonlySet<string>,
): PortalTourQuestCategory[] {
  return [...categories].sort((left, right) => {
    const leftQuests = questsByCategory.get(left) ?? [];
    const rightQuests = questsByCategory.get(right) ?? [];
    const leftPending = leftQuests.some((quest) => !completedIds.has(quest.id));
    const rightPending = rightQuests.some(
      (quest) => !completedIds.has(quest.id),
    );
    if (leftPending !== rightPending) {
      return leftPending ? -1 : 1;
    }
    return categories.indexOf(left) - categories.indexOf(right);
  });
}

export function resolveQuestListHint(
  quest: PortalTourQuest,
  state: PortalTourQuestListVisualState,
  guideFirstStep: string | null,
): string {
  if (state === "done") return "Concluído — parabéns!";
  if (state === "near") return "Perto — conclua nesta tela";
  if (state === "pending" || state === "locked") {
    return quest.hint || guideFirstStep || "Disponível em breve.";
  }
  return quest.hint;
}

export function questListVisualClassName(
  state: PortalTourQuestListVisualState,
): string {
  switch (state) {
    case "done":
      return "is-done";
    case "near":
      return "is-near";
    case "pending":
      return "is-pending";
    case "locked":
      return "is-locked";
    default:
      return "is-pending";
  }
}
