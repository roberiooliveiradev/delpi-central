import { delpiUiClass } from "../../utils/delpiUiClass";

import {
  resolveCompareSparklineTone,
  type CompareSparklineTone,
} from "./CompareSparkline";

export type TrendDeltaClassNames = {
  root: string;
};

export type TrendDeltaProps = {
  classNames: TrendDeltaClassNames;
  value: number | null | undefined;
  /** Tom forçado; default a partir do sinal de `value`. */
  tone?: CompareSparklineTone;
  className?: string;
};

export function trendDeltaBemClasses(prefix: string): TrendDeltaClassNames {
  const p = prefix.trim() || "delpi-ui";
  return {
    root: delpiUiClass(`${p}-trend-delta`, "delpi-ui-trend-delta"),
  };
}

export function formatTrendDeltaPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}

export function resolveTrendDeltaTone(
  value: number | null | undefined,
): CompareSparklineTone {
  if (value == null || Number.isNaN(value)) return "flat";
  return resolveCompareSparklineTone(0, value);
}

/**
 * Percentual de variação com tom up/down/flat para células de tabela.
 */
export function TrendDelta({
  classNames,
  value,
  tone: toneProp,
  className,
}: TrendDeltaProps) {
  const tone = toneProp ?? resolveTrendDeltaTone(value);
  const label = formatTrendDeltaPct(value);
  const rootClass = [
    classNames.root,
    `delpi-ui-trend-delta--${tone}`,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return <span className={rootClass}>{label}</span>;
}

export type DashboardTrendDeltaProps = Omit<TrendDeltaProps, "classNames">;

export function createDashboardTrendDelta(config: { prefix: string }) {
  const classNames = trendDeltaBemClasses(config.prefix);
  return function DashboardTrendDelta(props: DashboardTrendDeltaProps) {
    return <TrendDelta classNames={classNames} {...props} />;
  };
}
