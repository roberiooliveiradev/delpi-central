import { type CSSProperties } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartAllowsResize,
  chartPartDomProps,
  getChartPartState,
  isChartPartRefEqual,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import { ChartPartResizeHandles } from "./ChartPartResizeHandles";
import type { SeriesChartLayout } from "./layout";

export type ChartPlotAreaChromeProps = {
  layout: SeriesChartLayout;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
};

/**
 * Overlay HTML dos handles de resize do plotArea (SVG não hospeda botões).
 * `pointer-events: none` no host — só handles capturam — para não bloquear série/marcadores.
 */
export function ChartPlotAreaChrome({ layout, interaction, chartParts }: ChartPlotAreaChromeProps) {
  const cn = useSeriesChartClasses();
  const ref = { kind: "plotArea" as const };
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const frame = getChartPartState(chartParts, ref)?.frame;
  const showResize = Boolean(selected && chartPartAllowsResize(ref) && interaction?.onPartResizePointerDown);
  const dom = chartPartDomProps(ref, interaction?.selectedPart);
  /*
   * Overlay usa layout atual sem persistir frame no select — gravar no select
   * alimentava `plotFrame` e reescrevia margens (gráfico “encolhia”).
   */

  if (!showResize) return null;

  const style: CSSProperties = {
    position: "absolute",
    left: frame?.w != null ? `${frame.x}%` : `${(layout.margin.left / layout.viewW) * 100}%`,
    top: frame?.h != null ? `${frame.y}%` : `${(layout.margin.top / layout.viewH) * 100}%`,
    width: frame?.w != null ? `${frame.w}%` : `${(layout.plotW / layout.viewW) * 100}%`,
    height: frame?.h != null ? `${frame.h}%` : `${(layout.plotH / layout.viewH) * 100}%`,
    boxSizing: "border-box",
    pointerEvents: "none",
    zIndex: 4,
  };

  return (
    <div
      className={[cn.plotAreaChrome, `${cn.root}__part--selected`, `${cn.root}__part--resizable`]
        .filter(Boolean)
        .join(" ")}
      style={style}
      {...dom}
      aria-hidden
    >
      <ChartPartResizeHandles
        visible
        onResizePointerDown={(handle, event) => {
          interaction?.onPartResizePointerDown?.(ref, event, handle);
        }}
      />
    </div>
  );
}
