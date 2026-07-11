import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartLegendPosition } from "../seriesChartOptions";
import {
  chartPartDomProps,
  isChartPartRefEqual,
  type SeriesChartInteraction,
} from "../seriesChartParts";

export type ChartLegendProps = {
  seriesName: string;
  seriesColor: string;
  position: SeriesChartLegendPosition;
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
};

export function ChartLegend({
  seriesName,
  seriesColor,
  position,
  visible = true,
  interaction,
}: ChartLegendProps) {
  const cn = useSeriesChartClasses();
  if (!visible || position === "hidden") return null;

  const positionClass =
    position === "top" ? cn.legendTop : position === "right" ? cn.legendRight : cn.legendBottom;

  const ref = { kind: "legend" as const };
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown);

  return (
    <ul
      className={[cn.legend, positionClass, selected ? `${cn.root}__part--selected` : ""]
        .filter(Boolean)
        .join(" ")}
      aria-label="Legenda"
      {...chartPartDomProps(ref, interaction?.selectedPart)}
      onPointerDown={
        interactive
          ? (event) => {
              event.stopPropagation();
              interaction?.onPartPointerDown?.(ref, event);
            }
          : undefined
      }
    >
      <li className={cn.legendItem}>
        <span className={cn.legendSwatch} style={{ background: seriesColor }} aria-hidden />
        <span>{seriesName}</span>
      </li>
    </ul>
  );
}
