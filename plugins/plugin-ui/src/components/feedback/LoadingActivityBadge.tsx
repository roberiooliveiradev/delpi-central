import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type LoadingActivityBadgeTone = "neutral" | "info";

export type LoadingActivityBadgeClassNames = {
  root: string;
  rootTone: (tone: LoadingActivityBadgeTone) => string;
  spinner: string;
  label: string;
  bar: string;
  barIndicator: string;
};

export type LoadingActivityBadgeProps = {
  label?: string;
  tone?: LoadingActivityBadgeTone;
  showBar?: boolean;
  className?: string;
  classNames?: LoadingActivityBadgeClassNames;
};

export function loadingActivityBadgeBemClasses(
  prefix = "delpi-ui",
): LoadingActivityBadgeClassNames {
  const base = `${prefix}-loading-activity-badge`;
  const ui = "delpi-ui-loading-activity-badge";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    root: pair(base, ui),
    rootTone: (tone) => pair(`${base}--${tone}`, `${ui}--${tone}`),
    spinner: pair(`${base}__spinner`, `${ui}__spinner`),
    label: pair(`${base}__label`, `${ui}__label`),
    bar: pair(`${base}__bar`, `${ui}__bar`),
    barIndicator: pair(`${base}__bar-indicator`, `${ui}__bar-indicator`),
  };
}

const DEFAULT_CN = loadingActivityBadgeBemClasses();

/**
 * Chip compacto de carregamento (header / sidebar).
 * CSS: `styles/loading-activity-badge.css`.
 */
export function LoadingActivityBadge({
  label = "Atualizando",
  tone = "neutral",
  showBar = false,
  className,
  classNames = DEFAULT_CN,
}: LoadingActivityBadgeProps) {
  return (
    <span
      className={[classNames.root, classNames.rootTone(tone), className].filter(Boolean).join(" ")}
      role="status"
      aria-live="polite"
    >
      <span className={classNames.spinner} aria-hidden="true" />
      <span className={classNames.label}>{label}</span>
      {showBar ? (
        <span className={classNames.bar} aria-hidden="true">
          <span className={classNames.barIndicator} />
        </span>
      ) : null}
    </span>
  );
}

export function createDashboardLoadingActivityBadge(config?: {
  prefix?: string;
  defaultTone?: LoadingActivityBadgeTone;
}): (props: Omit<LoadingActivityBadgeProps, "classNames">) => ReactNode {
  const classNames = loadingActivityBadgeBemClasses(config?.prefix ?? "delpi-ui");
  const defaultTone = config?.defaultTone ?? "neutral";

  return function DashboardLoadingActivityBadge(props) {
    const { tone, ...rest } = props;
    return (
      <LoadingActivityBadge
        classNames={classNames}
        tone={tone ?? defaultTone}
        {...rest}
      />
    );
  };
}
