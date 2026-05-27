import { useEffect, useRef, useState } from "react";

type UseStreamingTextRevealOptions = {
  /** Revela progressivamente enquanto a resposta está em streaming. */
  enabled: boolean;
  /** Caracteres adicionados por frame (~16 ms). */
  charsPerFrame?: number;
};

/**
 * Suaviza respostas que chegam em blocos (direct response / proxy buffering),
 * exibindo o texto de forma incremental mesmo quando vários tokens SSE chegam juntos.
 */
export function useStreamingTextReveal(
  target: string,
  { enabled, charsPerFrame = 5 }: UseStreamingTextRevealOptions,
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

        const remaining = full.length - current.length;
        const step =
          remaining > charsPerFrame * 6
            ? Math.max(charsPerFrame, Math.ceil(remaining / 12))
            : charsPerFrame;

        return full.slice(0, current.length + step);
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
