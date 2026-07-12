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

/**
 * Ajusta `font-size` para o texto preencher o container pai (largura e altura),
 * ou aplica `fixedPx` quando a tipografia foi configurada explicitamente.
 */
export function FitText({ children, className, minPx = 14, maxPx = 240, fixedPx }: Props) {
  const measureRef = useRef<HTMLSpanElement>(null);
  const [fontSize, setFontSize] = useState(minPx);
  const useFixed =
    fixedPx != null && Number.isFinite(fixedPx) && fixedPx > 0 ? Math.round(fixedPx) : null;

  useLayoutEffect(() => {
    if (useFixed != null) return;

    const el = measureRef.current;
    const parent = el?.parentElement;
    if (!el || !parent) return;

    const fit = () => {
      const maxW = parent.clientWidth;
      const maxH = parent.clientHeight;
      if (maxW <= 0 || maxH <= 0) return;

      let lo = minPx;
      let hi = Math.min(maxPx, Math.max(minPx, Math.floor(Math.min(maxW, maxH) * 1.2)));
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
      setFontSize(best);
    };

    fit();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(fit);
    observer.observe(parent);
    return () => observer.disconnect();
  }, [children, maxPx, minPx, useFixed]);

  return (
    <span
      ref={measureRef}
      className={["delpi-ui-fit-text", className].filter(Boolean).join(" ")}
      style={{
        fontSize: useFixed ?? fontSize,
        lineHeight: 1.05,
        whiteSpace: "nowrap",
        display: "inline-block",
        maxWidth: "100%",
      }}
    >
      {children}
    </span>
  );
}
