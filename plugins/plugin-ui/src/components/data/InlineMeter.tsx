import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type InlineMeterTone = "neutral" | "success" | "warning" | "danger";

export type InlineMeterSegment = {
  id: string;
  /** Fração 0–1 do total (ou valor absoluto se `max` for passado no root). */
  value: number;
  tone?: InlineMeterTone;
};

export type InlineMeterClassNames = {
  root: string;
  track: string;
  fill: string;
  label: string;
};

export type InlineMeterProps = {
  classNames: InlineMeterClassNames;
  /** Valor preenchido (0–max). Ignorado se `segments` for passado. */
  value?: number;
  max?: number;
  segments?: InlineMeterSegment[];
  tone?: InlineMeterTone;
  label?: ReactNode;
  size?: "sm" | "md";
  className?: string;
  "aria-label"?: string;
};

export function inlineMeterBemClasses(prefix: string): InlineMeterClassNames {
  return {
    root: delpiUiClass(`${prefix}-inline-meter`, "delpi-ui-inline-meter"),
    track: delpiUiClass(`${prefix}-inline-meter__track`, "delpi-ui-inline-meter__track"),
    fill: delpiUiClass(`${prefix}-inline-meter__fill`, "delpi-ui-inline-meter__fill"),
    label: delpiUiClass(`${prefix}-inline-meter__label`, "delpi-ui-inline-meter__label"),
  };
}

function clampRatio(n: number): number {
  if (!Number.isFinite(n) || n <= 0) return 0;
  if (n >= 1) return 1;
  return n;
}

export function InlineMeter({
  classNames,
  value = 0,
  max = 1,
  segments,
  tone = "neutral",
  label,
  size = "sm",
  className,
  "aria-label": ariaLabel,
}: InlineMeterProps) {
  const resolvedSegments: InlineMeterSegment[] =
    segments && segments.length > 0
      ? segments
      : [
          {
            id: "primary",
            value: max > 0 ? value / max : 0,
            tone,
          },
        ];

  const ratios = resolvedSegments.map((seg) => ({
    ...seg,
    ratio: clampRatio(seg.value),
  }));
  const totalRatio = clampRatio(ratios.reduce((sum, s) => sum + s.ratio, 0));

  const rootClass = [
    classNames.root,
    size === "md" ? "delpi-ui-inline-meter--md" : "delpi-ui-inline-meter--sm",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClass}
      role="meter"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(totalRatio * 100)}
      aria-label={ariaLabel}
    >
      <div className={classNames.track}>
        {ratios.map((seg) =>
          seg.ratio > 0 ? (
            <span
              key={seg.id}
              className={[
                classNames.fill,
                `delpi-ui-inline-meter__fill--${seg.tone ?? tone}`,
              ].join(" ")}
              style={{ width: `${seg.ratio * 100}%` }}
            />
          ) : null,
        )}
      </div>
      {label != null ? <div className={classNames.label}>{label}</div> : null}
    </div>
  );
}

export type DashboardInlineMeterProps = Omit<InlineMeterProps, "classNames">;

export function createDashboardInlineMeter(config: { prefix: string }) {
  const classNames = inlineMeterBemClasses(config.prefix);
  return function DashboardInlineMeter(props: DashboardInlineMeterProps) {
    return <InlineMeter classNames={classNames} {...props} />;
  };
}
