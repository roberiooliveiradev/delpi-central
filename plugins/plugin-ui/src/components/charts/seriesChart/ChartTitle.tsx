import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  isChartPartRefEqual,
  type SeriesChartInteraction,
} from "../seriesChartParts";

export type ChartTitleProps = {
  title?: string;
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
};

export function ChartTitle({ title, visible = true, interaction }: ChartTitleProps) {
  const cn = useSeriesChartClasses();
  if (!visible || !title?.trim()) return null;

  const ref = { kind: "title" as const };
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown);

  return (
    <div
      className={[cn.title, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
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
      {title.trim()}
    </div>
  );
}
