import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type InlineLoadingProgressDensity = "default" | "compact";

export type InlineLoadingProgressClassNames = {
  root: string;
  rootDensity: (density: InlineLoadingProgressDensity) => string;
  label: string;
  track: string;
  fill: string;
  value: string;
};

export type InlineLoadingProgressProps = {
  /** Progresso determinado 0–100 (valor real da atualização). */
  percent: number;
  /** Texto ao lado da barra (ex.: «Carregando dados»). */
  label?: string;
  showLabel?: boolean;
  showPercent?: boolean;
  density?: InlineLoadingProgressDensity;
  className?: string;
  classNames?: InlineLoadingProgressClassNames;
};

export function clampInlineLoadingPercent(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(100, Math.max(0, Math.round(value)));
}

export function inlineLoadingProgressBemClasses(
  prefix = "delpi-ui",
): InlineLoadingProgressClassNames {
  const base = `${prefix}-inline-loading-progress`;
  const ui = "delpi-ui-inline-loading-progress";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    root: pair(base, ui),
    rootDensity: (density) => pair(`${base}--${density}`, `${ui}--${density}`),
    label: pair(`${base}__label`, `${ui}__label`),
    track: pair(`${base}__track`, `${ui}__track`),
    fill: pair(`${base}__fill`, `${ui}__fill`),
    value: pair(`${base}__value`, `${ui}__value`),
  };
}

const DEFAULT_CN = inlineLoadingProgressBemClasses();

/**
 * Progresso determinado compacto para status bar / toolbar.
 * CSS: `styles/inline-loading-progress.css`.
 */
export function InlineLoadingProgress({
  percent,
  label = "Carregando dados",
  showLabel = true,
  showPercent = true,
  density = "compact",
  className,
  classNames = DEFAULT_CN,
}: InlineLoadingProgressProps) {
  const clamped = clampInlineLoadingPercent(percent);
  const ariaLabel = showLabel
    ? `${label}: ${clamped}%`
    : `Carregamento: ${clamped}%`;

  return (
    <div
      className={[classNames.root, classNames.rootDensity(density), className]
        .filter(Boolean)
        .join(" ")}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={clamped}
      aria-label={ariaLabel}
    >
      {showLabel ? <span className={classNames.label}>{label}</span> : null}
      <span className={classNames.track} aria-hidden="true">
        <span className={classNames.fill} style={{ width: `${clamped}%` }} />
      </span>
      {showPercent ? <span className={classNames.value}>{clamped}%</span> : null}
    </div>
  );
}

export function createDashboardInlineLoadingProgress(config?: {
  prefix?: string;
  defaultDensity?: InlineLoadingProgressDensity;
  defaultLabel?: string;
}): (props: Omit<InlineLoadingProgressProps, "classNames">) => ReactNode {
  const classNames = inlineLoadingProgressBemClasses(config?.prefix ?? "delpi-ui");
  const defaultDensity = config?.defaultDensity ?? "compact";
  const defaultLabel = config?.defaultLabel ?? "Carregando dados";

  return function DashboardInlineLoadingProgress(props) {
    const { density, label, ...rest } = props;
    return (
      <InlineLoadingProgress
        classNames={classNames}
        density={density ?? defaultDensity}
        label={label ?? defaultLabel}
        {...rest}
      />
    );
  };
}
