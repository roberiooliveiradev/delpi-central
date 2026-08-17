import {
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { ResponsiveContainer } from "recharts";

import {
  shouldAcceptMeasuredSize,
  STABLE_CHART_MIN_SIZE_PX,
} from "./stableChartSize";

export type StableResponsiveContainerProps = {
  children: ReactNode;
  /** Largura CSS do host. Default `100%`. */
  width?: number | string;
  /** Altura CSS do host (número = px fixo do plot). Default `100%`. */
  height?: number | string;
  className?: string;
  style?: CSSProperties;
  /** Delta mínimo (px) para aceitar resize. Default 1. */
  sizeEpsilonPx?: number;
};

/**
 * Substitui `ResponsiveContainer` com `width="100%"` cru.
 *
 * Mede o host com RO + rAF + epsilon e passa **width/height numéricos** ao
 * Recharts — assim o `SizeDetectorContainer` interno (RO → setState →
 * `notifyNestedSubs`) não entra em loop quando o `.main-area` do portal
 * muda ao colapsar/expandir a sidebar.
 */
export function StableResponsiveContainer({
  children,
  width = "100%",
  height = "100%",
  className,
  style,
  sizeEpsilonPx = 1,
}: StableResponsiveContainerProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState<{ w: number; h: number } | null>(null);
  const fixedHeightPx = typeof height === "number" ? height : null;

  useLayoutEffect(() => {
    const node = hostRef.current;
    if (!node) return;

    let raf = 0;

    const apply = () => {
      const nextW = node.clientWidth;
      const nextH = fixedHeightPx ?? node.clientHeight;
      setSize((prev) => {
        const next = { w: nextW, h: nextH };
        return shouldAcceptMeasuredSize(prev, next, sizeEpsilonPx) ? next : prev;
      });
    };

    const schedule = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(apply);
    };

    apply();
    if (typeof ResizeObserver === "undefined") {
      return () => cancelAnimationFrame(raf);
    }
    const observer = new ResizeObserver(schedule);
    observer.observe(node);
    return () => {
      cancelAnimationFrame(raf);
      observer.disconnect();
    };
  }, [fixedHeightPx, sizeEpsilonPx]);

  const hostStyle: CSSProperties = {
    width,
    height: fixedHeightPx ?? height,
    minWidth: 0,
    /* Impede feedback scrollbar ↔ largura do plot (oscilação clássica do Recharts). */
    overflow: "hidden",
    ...style,
  };

  return (
    <div
      ref={hostRef}
      className={["delpi-ui-stable-responsive-container", className]
        .filter(Boolean)
        .join(" ")}
      style={hostStyle}
      data-stable-chart-host=""
    >
      {size &&
      size.w >= STABLE_CHART_MIN_SIZE_PX &&
      size.h >= STABLE_CHART_MIN_SIZE_PX ? (
        <ResponsiveContainer width={size.w} height={size.h}>
          {children}
        </ResponsiveContainer>
      ) : null}
    </div>
  );
}
