import {
  KpiCard as BaseKpiCard,
  kpiCardBemClasses,
  type DashboardKpiCardProps,
  type KpiCardLabels,
} from "@delpi/plugin-ui/index";

const LABELS = {
  goalPrefix: "Meta",
  iddScorePrefix: "Nota",
  badgesStatus: "Metas e indicadores",
} satisfies KpiCardLabels;

const CLASS_NAMES = {
  ...kpiCardBemClasses("ds"),
  context: "ds-kpi-subtitle",
};

export function KpiCard(props: DashboardKpiCardProps) {
  return <BaseKpiCard classNames={CLASS_NAMES} labels={LABELS} {...props} />;
}

export type KpiCardProps = DashboardKpiCardProps;
