export type NaturalTextRevealOptions = {
  fullText: string;
  onUpdate: (visible: string) => void;
  onComplete?: () => void;
  /** Velocidade base (~60 fps). */
  charsPerFrame?: number;
};

export function computeRevealStep(
  currentLength: number,
  totalLength: number,
  charsPerFrame = 3,
): number {
  const remaining = totalLength - currentLength;

  if (remaining <= 0) {
    return 0;
  }

  if (remaining > charsPerFrame * 24) {
    return Math.max(charsPerFrame * 2, Math.ceil(remaining / 18));
  }

  if (remaining > charsPerFrame * 8) {
    return Math.max(charsPerFrame, Math.ceil(remaining / 12));
  }

  return Math.min(remaining, Math.max(1, charsPerFrame));
}

export function advanceRevealIndex(text: string, index: number, step: number): number {
  if (step <= 0) {
    return index;
  }

  let next = Math.min(text.length, index + step);

  if (next >= text.length || step <= 2) {
    return next;
  }

  const slice = text.slice(index, next);

  if (/\s/.test(slice)) {
    return next;
  }

  const spaceIndex = text.indexOf(" ", next);

  if (spaceIndex !== -1 && spaceIndex - next <= 4) {
    return Math.min(text.length, spaceIndex + 1);
  }

  return next;
}

export function runNaturalTextReveal({
  fullText,
  onUpdate,
  onComplete,
  charsPerFrame = 3,
}: NaturalTextRevealOptions): () => void {
  let index = 0;
  let frameId = 0;
  let cancelled = false;

  onUpdate("");

  const tick = () => {
    if (cancelled) {
      return;
    }

    const step = computeRevealStep(index, fullText.length, charsPerFrame);
    index = advanceRevealIndex(fullText, index, step);
    onUpdate(fullText.slice(0, index));

    if (index < fullText.length) {
      frameId = requestAnimationFrame(tick);
      return;
    }

    onComplete?.();
  };

  frameId = requestAnimationFrame(tick);

  return () => {
    cancelled = true;
    cancelAnimationFrame(frameId);
  };
}
