import { ChevronRight, Minus, TrendingDown, TrendingUp } from "lucide-react";
import type { KeyboardEvent, ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { FitText } from "./FitText";
import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type MetricKpiCardTone = "default" | "positive" | "negative" | "warning";

export type MetricKpiStatusTone = "positive" | "negative" | "warning" | "neutral";

export type MetricKpiStatus = {
  label: string;
  tone?: MetricKpiStatusTone;
  trend?: "up" | "down" | "flat";
};

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
  footer?: string;
  status?: string;
  statusTone?: (tone: MetricKpiStatusTone) => string;
  chevron?: string;
};

export type MetricKpiCardProps = {
  label?: string;
  /** Ajuda no hover do texto do label (HelpTooltip wrap — sem ícone ?). */
  titleHint?: string;
  value: string;
  /** Subtítulo ou slot (ex.: tendência) abaixo do valor. */
  hint?: ReactNode;
  icon?: ReactNode;
  tone?: MetricKpiCardTone;
  /** Pill de status no rodapé (o consumidor calcula label/tom a partir do dado). */
  status?: MetricKpiStatus;
  /** Torna o card acionável (role=button, Enter/Espaço) com chevron à direita. */
  onSelect?: () => void;
  "aria-label"?: string;
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
    footer: pair(`${card}__footer`, `${ui}-card__footer`),
    status: pair(`${card}__status`, `${ui}-status`),
    statusTone: (tone) =>
      pair(`${card}__status ${card}__status--${tone}`, `${ui}-status ${ui}-status--${tone}`),
    chevron: pair(`${card}__chevron`, `${ui}-card__chevron`),
  };
}

export function MetricKpiCard({
  label,
  titleHint,
  value,
  hint,
  icon,
  tone = "default",
  status,
  onSelect,
  "aria-label": ariaLabel,
  classNames,
  className,
  fitValue = false,
}: MetricKpiCardProps) {
  const showLabel = Boolean(label?.trim());
  const interactive = typeof onSelect === "function";
  const articleClass = [
    classNames.articleTone(tone),
    className,
    !showLabel && !hint ? withBemModifier(classNames.article, "value-dominant") : "",
    interactive ? withBemModifier(classNames.article, "interactive") : "",
  ]
    .filter(Boolean)
    .join(" ");
  const statusTone = status?.tone ?? "neutral";
  const TrendIcon =
    status?.trend === "up" ? TrendingUp : status?.trend === "down" ? TrendingDown : Minus;
  const onKeyDown = interactive
    ? (event: KeyboardEvent<HTMLElement>) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect();
        }
      }
    : undefined;

  return (
    <article
      className={articleClass}
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      aria-label={interactive ? ariaLabel : undefined}
      onClick={interactive ? () => onSelect() : undefined}
      onKeyDown={onKeyDown}
    >
      <div className={classNames.header}>
        <div className={classNames.body}>
          {showLabel ? (
            <p className={classNames.label}>
              {titleHint && classNames.labelHelp ? (
                <HelpTooltip
                  content={titleHint}
                  ariaLabel={`Ajuda: ${label}`}
                  wrap
                  placement="bottom"
                  className={classNames.labelHelp}
                >
                  <span className="delpi-ui-section-hint-label">{label}</span>
                </HelpTooltip>
              ) : (
                label
              )}
            </p>
          ) : null}
          <strong className={classNames.value}>
            {fitValue ? <FitText>{value}</FitText> : value}
          </strong>
          {hint && classNames.hint ? (
            typeof hint === "string" ? (
              <p className={classNames.hint}>{hint}</p>
            ) : (
              <div className={classNames.hint}>{hint}</div>
            )
          ) : null}
        </div>
        {icon && classNames.icon ? (
          <div className={classNames.icon} aria-hidden="true">
            {icon}
          </div>
        ) : null}
      </div>
      {status || interactive ? (
        <div className={classNames.footer}>
          {status ? (
            <span
              className={
                classNames.statusTone ? classNames.statusTone(statusTone) : classNames.status
              }
            >
              {status.trend ? <TrendIcon size={12} strokeWidth={2} aria-hidden="true" /> : null}
              {status.label}
            </span>
          ) : (
            <span />
          )}
          {interactive ? (
            <span className={classNames.chevron} aria-hidden="true">
              <ChevronRight size={16} strokeWidth={1.75} />
            </span>
          ) : null}
        </div>
      ) : null}
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
