import { useCallback, useEffect, useState } from "react";
import type { PortalTourQuest } from "./portalTourQuests";
import {
  resolveQuestHighlights,
  type TourHighlightRect,
} from "./portalTourTargetVisibility";

export type { TourHighlightRect };

/**
 * Anéis só sob demanda (botão Dica) — no máximo 1 alvo.
 * Sem painel aberto ou sem dica ativa → zero highlights.
 */
export function usePortalTourHighlights(
  panelOpen: boolean,
  hintQuestId: string | null,
  quests: PortalTourQuest[],
  completedIds: ReadonlySet<string>,
) {
  const [highlights, setHighlights] = useState<TourHighlightRect[]>([]);

  const remeasure = useCallback(() => {
    if (!panelOpen || !hintQuestId) {
      setHighlights([]);
      return;
    }

    const focused = quests.filter((quest) => quest.id === hintQuestId);
    if (!focused.length || completedIds.has(hintQuestId)) {
      setHighlights([]);
      return;
    }

    const next = resolveQuestHighlights(focused, completedIds).slice(0, 1);
    setHighlights(next);
  }, [panelOpen, hintQuestId, quests, completedIds]);

  useEffect(() => {
    remeasure();

    if (!panelOpen || !hintQuestId) {
      return;
    }

    const onChange = () => remeasure();
    window.addEventListener("scroll", onChange, true);
    window.addEventListener("resize", onChange);
    window.addEventListener("orientationchange", onChange);

    const interval = window.setInterval(remeasure, 700);

    return () => {
      window.removeEventListener("scroll", onChange, true);
      window.removeEventListener("resize", onChange);
      window.removeEventListener("orientationchange", onChange);
      window.clearInterval(interval);
    };
  }, [panelOpen, hintQuestId, remeasure]);

  return highlights;
}
