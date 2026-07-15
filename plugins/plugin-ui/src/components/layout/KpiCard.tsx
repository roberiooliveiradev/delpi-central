import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type KpiPerformanceBadge = {
  tone: "success" | "warning";
  statusLabel: string;
  directionLabel: string;
};

export type KpiScopeBadge = {
  label: string;
};

export type KpiCardClassNames = {
  article: string;
  header: string;
  title: string;
  titleHelp?: string;
  value: string;
  valuePerUnit: string;
  goal: string;
  goalPerUnit: string;
  goalPrefix: string;
  goalIdd: string;
  badges: string;
  badge: string;
  badgeGroup: string;
  context: string;
  icon: string;
};

export type KpiCardLabels = {
  goalPrefix: string;
  iddScorePrefix: string;
  badgesStatus: string;
};

export type KpiCardProps = {
  title: string;
  titleHint?: string;
  value: string;
  valueVariant?: "default" | "per-unit";
  contextLabel?: string;
  goalLabel?: string | null;
  goalScopeBadge?: KpiScopeBadge | null;
  goalScopeHint?: string | null;
  goalPerformanceBadge?: KpiPerformanceBadge | null;
  goalPerformanceBadges?: KpiPerformanceBadge[];
  iddScoreLabel?: string | null;
  goalVariant?: "default" | "per-unit";
  subtitle?: string;
  icon: ReactNode;
  footer?: ReactNode;
  loading?: boolean;
  classNames: KpiCardClassNames;
  labels: KpiCardLabels;
  className?: string;
};

/** Monta classNames BEM `{prefix}-kpi-*` + `.delpi-ui-kpi-*`. */
export function kpiCardBemClasses(
  prefix: string,
  options?: { cardModifier?: string },
): KpiCardClassNames {
  const cardModifier = options?.cardModifier ?? "card";
  const card = `${prefix}-${cardModifier}`;
  const ui = "delpi-ui-kpi";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    article: pair(`${card} ${prefix}-kpi-card`, `delpi-ui-card ${ui}-card`),
    header: pair(`${prefix}-kpi-header`, `${ui}-header`),
    title: pair(`${prefix}-kpi-title`, `${ui}-title`),
    titleHelp: pair(`${prefix}-kpi-title__help`, `${ui}-title__help`),
    value: pair(`${prefix}-kpi-value`, `${ui}-value`),
    valuePerUnit: pair(
      `${prefix}-kpi-value ${prefix}-kpi-value--per-unit`,
      `${ui}-value ${ui}-value--per-unit`,
    ),
    goal: pair(`${prefix}-kpi-goal`, `${ui}-goal`),
    goalPerUnit: pair(
      `${prefix}-kpi-goal ${prefix}-kpi-goal--per-unit`,
      `${ui}-goal ${ui}-goal--per-unit`,
    ),
    goalPrefix: pair(`${prefix}-kpi-goal-prefix`, `${ui}-goal-prefix`),
    goalIdd: pair(`${prefix}-kpi-goal--idd`, `${ui}-goal--idd`),
    badges: pair(`${prefix}-kpi-badges`, `${ui}-badges`),
    badge: pair(`${prefix}-kpi-badge`, `${ui}-badge`),
    badgeGroup: pair(`${prefix}-kpi-badge-group`, `${ui}-badge-group`),
    context: pair(`${prefix}-kpi-context`, `${ui}-context`),
    icon: pair(`${prefix}-kpi-icon`, `${ui}-icon`),
  };
}

export function KpiCard({
  title,
  titleHint,
  value,
  valueVariant = "default",
  contextLabel,
  goalLabel = null,
  goalScopeBadge = null,
  goalScopeHint = null,
  goalPerformanceBadge = null,
  goalPerformanceBadges = [],
  iddScoreLabel = null,
  goalVariant = "default",
  subtitle,
  icon,
  footer = null,
  loading = false,
  classNames,
  labels,
  className,
}: KpiCardProps) {
  const showMeta = !loading;
  const resolvedGoal = showMeta ? goalLabel ?? null : null;
  const resolvedContext = subtitle ?? contextLabel ?? "";
  const resolvedScopeHint = showMeta ? goalScopeHint?.trim() || null : null;
  const resolvedScopeBadge = showMeta ? goalScopeBadge : null;
  const resolvedIddScore = showMeta ? iddScoreLabel ?? null : null;
  const performanceBadges = showMeta
    ? goalPerformanceBadges.length > 0
      ? goalPerformanceBadges
      : goalPerformanceBadge
        ? [goalPerformanceBadge]
        : []
    : [];
  const hasBadges = Boolean(
    resolvedScopeBadge || resolvedScopeHint || performanceBadges.length > 0,
  );
  const valueClassName =
    valueVariant === "per-unit" ? classNames.valuePerUnit : classNames.value;
  const goalClassName = goalVariant === "per-unit" ? classNames.goalPerUnit : classNames.goal;
  const articleClass = [classNames.article, className].filter(Boolean).join(" ");

  return (
    <article className={articleClass}>
      <div className={classNames.header}>
        <div>
          <p className={classNames.title}>
            {title}
            {titleHint ? (
              <HelpTooltip
                content={titleHint}
                ariaLabel={`Ajuda: ${title}`}
                className={classNames.titleHelp}
              />
            ) : null}
          </p>
          <h3 className={valueClassName}>{loading ? "…" : value}</h3>
          {resolvedGoal ? (
            <p className={goalClassName}>
              <span className={classNames.goalPrefix}>{labels.goalPrefix}</span> {resolvedGoal}
            </p>
          ) : null}
          {resolvedIddScore ? (
            <p className={`${goalClassName} ${classNames.goalIdd}`}>
              <span className={classNames.goalPrefix}>{labels.iddScorePrefix}</span>{" "}
              {resolvedIddScore}
            </p>
          ) : null}
          {hasBadges ? (
            <div className={classNames.badges} role="status" aria-label={labels.badgesStatus}>
              {resolvedScopeBadge ? (
                <span className={withBemModifier(classNames.badge, "scope")}>
                  {resolvedScopeBadge.label}
                </span>
              ) : null}
              {resolvedScopeHint ? (
                <span className={withBemModifier(classNames.badge, "info")}>
                  {resolvedScopeHint}
                </span>
              ) : null}
              {performanceBadges.map((badge, index) => (
                <span key={`${badge.statusLabel}-${index}`} className={classNames.badgeGroup}>
                  <span className={withBemModifier(classNames.badge, badge.tone)}>
                    {badge.statusLabel}
                  </span>
                  <span className={withBemModifier(classNames.badge, "direction")}>
                    {badge.directionLabel}
                  </span>
                </span>
              ))}
            </div>
          ) : null}
          <span className={classNames.context}>{resolvedContext}</span>
        </div>
        <div className={classNames.icon} aria-hidden="true">
          {icon}
        </div>
      </div>
      {footer}
    </article>
  );
}

export type DashboardKpiCardProps = Omit<KpiCardProps, "classNames" | "labels">;

export function createDashboardKpiCard(config: {
  prefix: string;
  labels: KpiCardLabels;
  cardModifier?: string;
}) {
  const classNames = kpiCardBemClasses(config.prefix, {
    cardModifier: config.cardModifier,
  });

  return function DashboardKpiCard(props: DashboardKpiCardProps) {
    return <KpiCard classNames={classNames} labels={config.labels} {...props} />;
  };
}
