import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { FitText } from "./FitText";

export type MetricKpiCardTone = "default" | "positive" | "negative" | "warning";

export type MetricKpiCardClassNames = {
  article: string;
  articleTone: (tone: MetricKpiCardTone) => string;
  header: string;
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

  return {
    article: card,
    articleTone: (tone) => `${card} ${card}--${tone}`,
    header: `${prefix}-kpi-header`,
    label: `${card}__label`,
    labelHelp: `${card}__label-help`,
    value: `${card}__value`,
    hint: `${card}__hint`,
    icon: `${prefix}-kpi-icon`,
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
    !showLabel && !hint ? `${classNames.article}--value-dominant` : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <article className={articleClass}>
      <div className={classNames.header}>
        <div className={`${classNames.article}__body`}>
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
