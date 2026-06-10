import type { PortalTourQuest } from "./portalTourQuestTypes";
import { isQuestAvailable } from "./portalTourQuests";
import type { TourHighlightRect } from "./portalTourTargetVisibility";
import { isLauncherOpen } from "./portalTourTargetVisibility";
import { resolveTourContextLabel } from "./portalTourRoutes";

export type PortalTourQuestGuide = {
  questId: string;
  title: string;
  steps: string[];
  kind: "action" | "unlock";
};

function unlockHintForQuest(quest: PortalTourQuest): string {
  if (quest.unlockHint) return quest.unlockHint;

  switch (quest.scope) {
    case "launcher":
      return "Abra Apps na barra lateral para acessar o catálogo.";
    case "home":
      return "Acesse a página inicial pelo logo ou rota /.";
    case "profile":
      return "Menu de perfil → Meu Perfil.";
    case "notifications":
      return 'Use o sino na sidebar ou "Ver todas" na home.';
    case "privacy":
      return "Menu de perfil → Privacidade e Dados.";
    case "admin":
      return "Sidebar → Admin (requer permissão de gestão).";
    case "sidebar":
      return "Expanda a sidebar se estiver recolhida.";
    default:
      return "Explore o portal até o elemento ficar visível.";
  }
}

export function resolveQuestGuide(
  quest: PortalTourQuest,
  completed: boolean,
): PortalTourQuestGuide | null {
  if (completed) return null;

  if (isQuestAvailable(quest)) {
    return {
      questId: quest.id,
      title: quest.title,
      steps: quest.steps,
      kind: "action",
    };
  }

  return {
    questId: quest.id,
    title: quest.title,
    steps: [unlockHintForQuest(quest)],
    kind: "unlock",
  };
}

export function resolvePrimaryQuestGuide(
  quests: PortalTourQuest[],
  completedIds: ReadonlySet<string>,
  highlights: TourHighlightRect[],
): PortalTourQuestGuide | null {
  if (highlights.length > 0) {
    const quest = quests.find((item) => item.id === highlights[0].questId);
    if (quest) {
      return resolveQuestGuide(quest, completedIds.has(quest.id));
    }
  }

  const pending = quests.filter((quest) => !completedIds.has(quest.id));
  const available = pending.find((quest) => isQuestAvailable(quest));
  if (available) {
    return resolveQuestGuide(available, false);
  }

  const blocked = pending[0];
  if (blocked) {
    return resolveQuestGuide(blocked, false);
  }

  return null;
}

export type TourTipPlacement = "bottom" | "top" | "right" | "left";

export type TourTipLayout = {
  top: number;
  left: number;
  width: number;
  placement: TourTipPlacement;
  arrowOffsetX: number;
};

const TIP_WIDTH = 280;
const TIP_ESTIMATED_HEIGHT = 148;
const GAP = 12;
const VIEWPORT_PAD = 12;

export function computeTourTipLayout(
  highlight: TourHighlightRect | null,
): TourTipLayout | null {
  if (!highlight) return null;

  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const width = Math.min(TIP_WIDTH, vw - VIEWPORT_PAD * 2);
  const isCompact = vw <= 768;

  const targetCenterX = highlight.left + highlight.width / 2;
  const targetBottom = highlight.top + highlight.height;

  let top = targetBottom + GAP;
  let placement: TourTipPlacement = "bottom";

  const panelReserve = isCompact
    ? Math.min(220, vh * 0.36)
    : 280;

  if (top + TIP_ESTIMATED_HEIGHT > vh - panelReserve) {
    top = highlight.top - TIP_ESTIMATED_HEIGHT - GAP;
    placement = "top";
  }

  if (top < VIEWPORT_PAD) {
    top = VIEWPORT_PAD;
    placement = "bottom";
  }

  let left = clamp(
    targetCenterX - width / 2,
    VIEWPORT_PAD,
    vw - width - VIEWPORT_PAD,
  );

  if (isCompact && left + width > vw - VIEWPORT_PAD) {
    left = VIEWPORT_PAD;
  }

  const arrowOffsetX = clamp(targetCenterX - left, 20, width - 20);

  return { top, left, width, placement, arrowOffsetX };
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

export function getTourContextLabel() {
  if (isLauncherOpen()) return "Catálogo aberto";
  return resolveTourContextLabel() ?? "Portal";
}
