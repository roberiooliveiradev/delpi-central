import type { ImpactEffortQuadrant } from "./impactEffortTypes";

export type ImpactEffortMatrixClassNames = {
  root: string;
  plot: string;
  quadrant: string;
  quadrantQuickWin: string;
  quadrantStrategic: string;
  quadrantFillIn: string;
  quadrantRethink: string;
  quadrantLabel: string;
  axisLine: string;
  thresholdLine: string;
  axisLabel: string;
  axisLabelImpact: string;
  axisLabelEffort: string;
  point: string;
  pointActive: string;
  pointMuted: string;
  pointLabel: string;
  activeCaption: string;
  tooltip: string;
  empty: string;
};

export function impactEffortMatrixBemClasses(prefix = "delpi-ui"): ImpactEffortMatrixClassNames {
  const base = `${prefix}-impact-effort-matrix`;
  return {
    root: base,
    plot: `${base}__plot`,
    quadrant: `${base}__quadrant`,
    quadrantQuickWin: `${base}__quadrant--quick-win`,
    quadrantStrategic: `${base}__quadrant--strategic`,
    quadrantFillIn: `${base}__quadrant--fill-in`,
    quadrantRethink: `${base}__quadrant--rethink`,
    quadrantLabel: `${base}__quadrant-label`,
    axisLine: `${base}__axis-line`,
    thresholdLine: `${base}__threshold-line`,
    axisLabel: `${base}__axis-label`,
    axisLabelImpact: `${base}__axis-label--impact`,
    axisLabelEffort: `${base}__axis-label--effort`,
    point: `${base}__point`,
    pointActive: `${base}__point--active`,
    pointMuted: `${base}__point--muted`,
    pointLabel: `${base}__point-label`,
    activeCaption: `${base}__active-caption`,
    tooltip: `${base}__tooltip`,
    empty: `${base}__empty`,
  };
}

/** Classes internas `delpi-ui-*` (CSS em plugin-ui) + alias `tm-impact-effort-matrix` no root para tokens do Transformômetro. */
export function impactEffortMatrixTransformometroClasses(): ImpactEffortMatrixClassNames {
  const base = impactEffortMatrixBemClasses("delpi-ui");
  return {
    ...base,
    root: `${base.root} tm-impact-effort-matrix`,
  };
}

export function quadrantClassName(
  classNames: ImpactEffortMatrixClassNames,
  quadrant: ImpactEffortQuadrant,
): string {
  const map: Record<ImpactEffortQuadrant, string> = {
    quick_win: classNames.quadrantQuickWin,
    strategic: classNames.quadrantStrategic,
    fill_in: classNames.quadrantFillIn,
    rethink: classNames.quadrantRethink,
  };
  return `${classNames.quadrant} ${map[quadrant]}`;
}
