import { useSeriesChartClasses } from "../seriesChartClasses";

export type ChartTitleProps = {
  title?: string;
  visible?: boolean;
};

export function ChartTitle({ title, visible = true }: ChartTitleProps) {
  const cn = useSeriesChartClasses();
  if (!visible || !title?.trim()) return null;
  return <div className={cn.title}>{title.trim()}</div>;
}
