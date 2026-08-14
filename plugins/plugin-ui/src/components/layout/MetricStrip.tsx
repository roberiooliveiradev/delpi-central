import type { ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
import type { PageHeroHighlight, PageHeroHighlightTone } from "./PageHero";

export type MetricStripClassNames = {
  root: string;
  item: string;
  itemTone: (tone: Exclude<PageHeroHighlightTone, "neutral">) => string;
  label: string;
  value: string;
};

export type MetricStripProps = {
  classNames: MetricStripClassNames;
  items: PageHeroHighlight[];
  /** Densidade — default compact para faixa abaixo do hero. */
  density?: "comfortable" | "compact";
  className?: string;
  "aria-label"?: string;
};

export function metricStripBemClasses(prefix: string): MetricStripClassNames {
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  const base = `${prefix}-metric-strip`;
  const ui = "delpi-ui-metric-strip";
  return {
    root: pair(base, ui),
    item: pair(`${base}__item`, `${ui}__item`),
    itemTone: (tone) =>
      pair(`${base}__item ${base}__item--${tone}`, `${ui}__item ${ui}__item--${tone}`),
    label: pair(`${base}__label`, `${ui}__label`),
    value: pair(`${base}__value`, `${ui}__value`),
  };
}

export function MetricStrip({
  classNames,
  items,
  density = "compact",
  className,
  "aria-label": ariaLabel,
}: MetricStripProps) {
  if (!items.length) return null;
  const rootClass = [
    density === "compact" ? withBemModifier(classNames.root, "compact") : classNames.root,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass} aria-label={ariaLabel} data-density={density} role="group">
      {items.map((item) => {
        const tone = item.tone && item.tone !== "neutral" ? item.tone : null;
        const tileClass = tone ? classNames.itemTone(tone) : classNames.item;
        return (
          <div key={item.id} className={tileClass} data-tone={item.tone ?? "neutral"}>
            <span className={classNames.label}>{item.label}</span>
            <span className={classNames.value}>{item.value}</span>
          </div>
        );
      })}
    </div>
  );
}

export type DashboardMetricStripProps = Omit<MetricStripProps, "classNames"> & {
  items: PageHeroHighlight[];
};

export function createDashboardMetricStrip(config: { prefix: string }) {
  const classNames = metricStripBemClasses(config.prefix);
  return function DashboardMetricStrip(props: DashboardMetricStripProps) {
    return <MetricStrip classNames={classNames} {...props} />;
  };
}
