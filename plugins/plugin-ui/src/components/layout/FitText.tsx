import { useLayoutEffect, useRef, useState, type ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
  /** Tamanho mínimo em px (modo auto-fit). */
  minPx?: number;
  /** Teto em px (o limite real é o container). */
  maxPx?: number;
  /**
   * Tamanho explícito configurado pelo usuário.
   * Quando definido, não faz auto-fit — o tamanho persiste com ou sem seleção.
   */
  fixedPx?: number | null;
};

function readHostSize(parent: HTMLElement): { maxW: number; maxH: number } {
  const rect = parent.getBoundingClientRect();
  return {
    maxW: Math.max(parent.clientWidth, Math.floor(rect.width)),
    maxH: Math.max(parent.clientHeight, Math.floor(rect.height)),
  };
}

/**
 * Ajusta `font-size` para o texto preencher o container pai (largura e altura),
 * ou aplica `fixedPx` quando a tipografia foi configurada explicitamente.
 *
 * Mede o texto com largura intrínseca (`max-content`) — medir com width/height 100%
 * fazia scrollWidth≈clientWidth e o fit ficava preso no mínimo (layout flex do KPI).
 *
 * Não usa `height: 100%` no span: com host em `height: auto` (flex item) a % não
 * resolve e o fit colapsa em `minPx`. O limite vem de `parent.clientHeight` pós-layout.
 */
export function FitText({ children, className, minPx = 14, maxPx = 320, fixedPx }: Props) {
  const measureRef = useRef<HTMLSpanElement>(null);
  const [fontSize, setFontSize] = useState(minPx);
  const useFixed =
    fixedPx != null && Number.isFinite(fixedPx) && fixedPx > 0 ? Math.round(fixedPx) : null;

  useLayoutEffect(() => {
    if (useFixed != null) return;

    const el = measureRef.current;
    const parent = el?.parentElement;
    if (!el || !parent) return;

    let raf = 0;
    let attempts = 0;
    let fitting = false;

    const fit = () => {
      if (fitting) return;
      fitting = true;
      try {
        const { maxW, maxH } = readHostSize(parent);
        if (maxW <= 1 || maxH <= 1) {
          /* Flex ainda não resolveu altura — tenta de novo no próximo frame. */
          if (attempts < 8) {
            attempts += 1;
            raf = requestAnimationFrame(fit);
          }
          return;
        }
        attempts = 0;

        const prevWidth = el.style.width;
        const prevHeight = el.style.height;
        const prevMaxWidth = el.style.maxWidth;
        const prevMaxHeight = el.style.maxHeight;
        const prevWhiteSpace = el.style.whiteSpace;
        el.style.width = "max-content";
        el.style.height = "auto";
        el.style.maxWidth = "none";
        el.style.maxHeight = "none";
        el.style.whiteSpace = "nowrap";

        let lo = minPx;
        let hi = Math.min(maxPx, Math.max(minPx, Math.floor(Math.min(maxW, maxH) * 1.15)));
        let best = minPx;

        while (lo <= hi) {
          const mid = Math.floor((lo + hi) / 2);
          el.style.fontSize = `${mid}px`;
          const fits = el.scrollWidth <= maxW + 0.5 && el.scrollHeight <= maxH + 0.5;
          if (fits) {
            best = mid;
            lo = mid + 1;
          } else {
            hi = mid - 1;
          }
        }

        el.style.width = prevWidth;
        el.style.height = prevHeight;
        el.style.maxWidth = prevMaxWidth;
        el.style.maxHeight = prevMaxHeight;
        el.style.whiteSpace = prevWhiteSpace;
        /* Evita oscilação host↔fonte (RO → setState → React #185). */
        setFontSize((prev) => {
          if (Math.abs(prev - best) <= 1) return prev;
          /* Mudança grande ainda pode oscilar em 2–3 px — estabiliza. */
          if (Math.abs(prev - best) <= 3 && prev > minPx) return prev;
          return best;
        });
      } finally {
        fitting = false;
      }
    };

    fit();
    if (typeof ResizeObserver === "undefined") {
      return () => cancelAnimationFrame(raf);
    }
    let roRaf = 0;
    const observer = new ResizeObserver(() => {
      attempts = 0;
      /* Debounce: evita cascata síncrona de setState no mesmo frame de layout. */
      cancelAnimationFrame(roRaf);
      roRaf = requestAnimationFrame(fit);
    });
    observer.observe(parent);
    return () => {
      cancelAnimationFrame(raf);
      cancelAnimationFrame(roRaf);
      observer.disconnect();
    };
  }, [children, maxPx, minPx, useFixed]);

  return (
    <span
      ref={measureRef}
      className={["delpi-ui-fit-text", className].filter(Boolean).join(" ")}
      style={{
        fontSize: useFixed ?? fontSize,
        lineHeight: 1.05,
        whiteSpace: "nowrap",
        display: "block",
        boxSizing: "border-box",
        width: "max-content",
        maxWidth: "100%",
        maxHeight: "100%",
      }}
    >
      {children}
    </span>
  );
}
