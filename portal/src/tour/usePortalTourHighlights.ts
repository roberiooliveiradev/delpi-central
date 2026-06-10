import { useCallback, useEffect, useState } from "react";
import type { PortalTourQuest } from "./portalTourQuests";
import {
  resolveQuestHighlights,
  type TourHighlightRect,
} from "./portalTourTargetVisibility";

export type { TourHighlightRect };

export function usePortalTourHighlights(
  active: boolean,
  quests: PortalTourQuest[],
  completedIds: ReadonlySet<string>,
) {
  const [highlights, setHighlights] = useState<TourHighlightRect[]>([]);

  const remeasure = useCallback(() => {
    const next = resolveQuestHighlights(quests, completedIds);

    setHighlights((current) => {
      if (
        current.length === next.length &&
        current.every((item, index) => {
          const other = next[index];
          return (
            other &&
            item.questId === other.questId &&
            Math.abs(item.top - other.top) < 1 &&
            Math.abs(item.left - other.left) < 1 &&
            Math.abs(item.width - other.width) < 1 &&
            Math.abs(item.height - other.height) < 1
          );
        })
      )
        return current;
      return next;
    });
  }, [quests, completedIds]);

  useEffect(() => {
    if (!active) {
      setHighlights([]);
      return;
    }

    remeasure();

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
  }, [active, remeasure]);

  return highlights;
}
