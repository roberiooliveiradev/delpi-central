import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { FitText } from "./FitText";
import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type MetricKpiCardTone = "default" | "positive" | "negative" | "warning";

export type MetricKpiCardClassNames = {
  article: string;
  articleTone: (tone: MetricKpiCardTone) => string;
  header: string;
  body: string;
  label: string;
  labelHelp?: string;
  value: string;
  hint?: string;
  icon?: string;
};

export type MetricKpiCardProps = {
  label?: string;
  titleHint?: string;
  value: string;
  hint?: string;
  icon?: ReactNode;
  tone?: MetricKpiCardTone;
  classNames: MetricKpiCardClassNames;
  className?: string;
  /** Valor com font-size adaptativo ao card (TV / blocos redimensionáveis). */
  fitValue?: boolean;
};

export function metricKpiCardBemClasses(prefix: string, block = "kpi-card"): MetricKpiCardClassNames {
  const card = `${prefix}-${block}`;
  const ui = "delpi-ui-kpi";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  const article = pair(`${prefix}-card ${card}`, `delpi-ui-card ${ui}-card`);

  return {
    article,
    articleTone: (tone) => (tone === "default" ? article : withBemModifier(article, tone)),
    header: pair(`${prefix}-kpi-header`, `${ui}-header`),
    body: pair(`${card}__body`, `${ui}-card__body`),
    label: pair(`${card}__label`, `${ui}-title`),
    labelHelp: pair(`${card}__label-help`, `${ui}-title__help`),
    value: pair(`${card}__value`, `${ui}-value`),
    hint: pair(`${card}__hint`, `${ui}-subtitle`),
    icon: pair(`${prefix}-kpi-icon`, `${ui}-icon`),
  };
}

export function MetricKpiCard({
  label,
  titleHint,
  value,
  hint,
  icon,
  tone = "default",
  classNames,
  className,
  fitValue = false,
}: MetricKpiCardProps) {
  const showLabel = Boolean(label?.trim());
  const articleClass = [
    classNames.articleTone(tone),
    className,
    !showLabel && !hint ? withBemModifier(classNames.article, "value-dominant") : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <article className={articleClass}>
      <div className={classNames.header}>
        <div className={classNames.body}>
          {showLabel ? (
            <p className={classNames.label}>
              {label}
              {titleHint && classNames.labelHelp ? (
                <HelpTooltip
                  content={titleHint}
                  ariaLabel={`Ajuda: ${label}`}
                  className={classNames.labelHelp}
                />
              ) : null}
            </p>
          ) : null}
          <strong className={classNames.value}>
            {fitValue ? <FitText>{value}</FitText> : value}
          </strong>
          {hint && classNames.hint ? <p className={classNames.hint}>{hint}</p> : null}
        </div>
        {icon && classNames.icon ? (
          <div className={classNames.icon} aria-hidden="true">
            {icon}
          </div>
        ) : null}
      </div>
    </article>
  );
}

export type DashboardMetricKpiCardProps = Omit<MetricKpiCardProps, "classNames">;

export function createMetricKpiCard(prefix: string) {
  const classNames = metricKpiCardBemClasses(prefix);

  return function DashboardMetricKpiCard(props: DashboardMetricKpiCardProps) {
    return <MetricKpiCard classNames={classNames} {...props} />;
  };
}
