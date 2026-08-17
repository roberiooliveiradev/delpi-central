import type { PortalTourQuest } from "./portalTourQuestTypes";
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
