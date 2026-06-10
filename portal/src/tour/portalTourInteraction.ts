const PULSE_CLASS = "portal-tour-pulse-target";

export function pulseTourTarget(selector: string): () => void {
  const elements = document.querySelectorAll(selector);
  elements.forEach((element) => element.classList.add(PULSE_CLASS));
  return () => {
    elements.forEach((element) => element.classList.remove(PULSE_CLASS));
  };
}

export function watchTourInteraction(
  selector: string,
  onMatch: (element: Element) => void,
): () => void {
  const handler = (event: Event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;

    const match = target.closest(selector);
    if (!match) return;

    onMatch(match);
  };

  document.addEventListener("click", handler, true);

  return () => {
    document.removeEventListener("click", handler, true);
  };
}

export function watchTourQuests(
  quests: Array<{
    id: string;
    actionSelector: string;
    isAvailable?: () => boolean;
  }>,
  isCompleted: (questId: string) => boolean,
  onComplete: (questId: string) => void,
): () => void {
  const handler = (event: Event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;

    for (const quest of quests) {
      if (isCompleted(quest.id)) continue;
      if (quest.isAvailable && !quest.isAvailable()) continue;

      const match = target.closest(quest.actionSelector);
      if (!match) continue;

      onComplete(quest.id);
      return;
    }
  };

  document.addEventListener("click", handler, true);
  document.addEventListener("change", handler, true);

  return () => {
    document.removeEventListener("click", handler, true);
    document.removeEventListener("change", handler, true);
  };
}

export function clearTourPulseTargets() {
  document.querySelectorAll(`.${PULSE_CLASS}`).forEach((element) => {
    element.classList.remove(PULSE_CLASS);
  });
}

export function syncTourPulseElements(elements: HTMLElement[]): () => void {
  clearTourPulseTargets();
  elements.forEach((element) => element.classList.add(PULSE_CLASS));
  return () => {
    elements.forEach((element) => element.classList.remove(PULSE_CLASS));
    clearTourPulseTargets();
  };
}

export function syncTourPulseHighlights(selectors: string[]): () => void {
  clearTourPulseTargets();
  const cleanups = selectors.map((selector) => pulseTourTarget(selector));
  return () => {
    cleanups.forEach((cleanup) => cleanup());
    clearTourPulseTargets();
  };
}
