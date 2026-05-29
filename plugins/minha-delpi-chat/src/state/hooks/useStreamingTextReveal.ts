import { useEffect, useRef, useState } from "react";

import {
  advanceRevealIndex,
  computeRevealStep,
} from "./naturalTextReveal";

type UseStreamingTextRevealOptions = {
  /** Revela progressivamente enquanto a resposta está em streaming. */
  enabled: boolean;
  /** Caracteres adicionados por frame (~16 ms). */
  charsPerFrame?: number;
};

/**
 * Suaviza respostas que chegam em blocos (SSE token / direct response),
 * exibindo o texto de forma incremental com ritmo natural.
 */
export function useStreamingTextReveal(
  target: string,
  { enabled, charsPerFrame = 3 }: UseStreamingTextRevealOptions,
): string {
  const [visible, setVisible] = useState(target);
  const targetRef = useRef(target);
  targetRef.current = target;

  useEffect(() => {
    if (!enabled) {
      setVisible(targetRef.current);
      return;
    }

    let frameId = 0;
    let cancelled = false;

    const tick = () => {
      if (cancelled) {
        return;
      }

      setVisible((current) => {
        const full = targetRef.current;

        if (!full) {
          return "";
        }

        if (current.length >= full.length) {
          return full;
        }

        const step = computeRevealStep(current.length, full.length, charsPerFrame);
        const nextIndex = advanceRevealIndex(full, current.length, step);

        return full.slice(0, nextIndex);
      });

      frameId = requestAnimationFrame(tick);
    };

    frameId = requestAnimationFrame(tick);

    return () => {
      cancelled = true;
      cancelAnimationFrame(frameId);
    };
  }, [charsPerFrame, enabled]);

  useEffect(() => {
    if (!enabled) {
      setVisible(target);
    }
  }, [enabled, target]);

  return enabled ? visible : target;
}
