import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type JourneyProgressBarClassNames = {
  root: string;
  header: string;
  label: string;
  value: string;
  track: string;
  fill: string;
  summary: string;
};

export type JourneyProgressBarProps = {
  /** Completeness 0–100 (human journey, not system loading). */
  value: number;
  label?: string;
  summary?: string;
  ariaLabel?: string;
  className?: string;
  classNames?: JourneyProgressBarClassNames;
};

export function clampJourneyProgressValue(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(100, Math.max(0, Math.round(value)));
}

export function journeyProgressBarBemClasses(
  prefix = "delpi-ui",
): JourneyProgressBarClassNames {
  const base = `${prefix}-journey-progress`;
  const ui = "delpi-ui-journey-progress";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    header: pair(`${base}__header`, `${ui}__header`),
    label: pair(`${base}__label`, `${ui}__label`),
    value: pair(`${base}__value`, `${ui}__value`),
    track: pair(`${base}__track`, `${ui}__track`),
    fill: pair(`${base}__fill`, `${ui}__fill`),
    summary: pair(`${base}__summary`, `${ui}__summary`),
  };
}

const DEFAULT_CN = journeyProgressBarBemClasses();

/**
 * Human journey completeness bar — not loading.
 * Do not confuse with InlineLoadingProgress.
 * CSS: `styles/journey-progress-bar.css`.
 */
export function JourneyProgressBar({
  value,
  label = "Progresso da solicitação",
  summary,
  ariaLabel,
  className,
  classNames = DEFAULT_CN,
}: JourneyProgressBarProps) {
  const clamped = clampJourneyProgressValue(value);
  const resolvedAria =
    ariaLabel || (summary ? `${label}: ${clamped}%. ${summary}` : `${label}: ${clamped}%`);

  return (
    <div
      className={[classNames.root, className].filter(Boolean).join(" ")}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={clamped}
      aria-label={resolvedAria}
    >
      <div className={classNames.header}>
        <span className={classNames.label}>{label}</span>
        <span className={classNames.value}>{clamped}%</span>
      </div>
      <span className={classNames.track} aria-hidden="true">
        <span className={classNames.fill} style={{ width: `${clamped}%` }} />
      </span>
      {summary ? <p className={classNames.summary}>{summary}</p> : null}
    </div>
  );
}

/** Alias preferred in design docs. */
export const ProgressSummaryBar = JourneyProgressBar;

export function createDashboardJourneyProgressBar(config?: {
  prefix?: string;
  defaultLabel?: string;
}): (props: Omit<JourneyProgressBarProps, "classNames">) => ReactNode {
  const classNames = journeyProgressBarBemClasses(config?.prefix ?? "delpi-ui");
  const defaultLabel = config?.defaultLabel ?? "Progresso da solicitação";
  return function DashboardJourneyProgressBar(props) {
    const { label, ...rest } = props;
    return (
      <JourneyProgressBar
        classNames={classNames}
        label={label ?? defaultLabel}
        {...rest}
      />
    );
  };
}

export const createDashboardProgressSummaryBar = createDashboardJourneyProgressBar;
