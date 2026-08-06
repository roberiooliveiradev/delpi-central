import type { ReactNode } from "react";

import {
  createHostContainedModalShell,
  createMetricKpiCard,
  createDashboardStatusBadge,
  emptyStateCardBemClasses,
  EmptyState as KitEmptyState,
  type DashboardMetricKpiCardProps,
  type MetricKpiCardTone,
  type StatusBadgeVariant,
} from "@delpi/plugin-ui/index";

export const PVA_ROOT_CLASS = "dashboard-pedidos-venda-abertos";

const MetricKpiBase = createMetricKpiCard("pva");
const StatusBadgeBase = createDashboardStatusBadge({ prefix: "pva" });

export const PvaHostModal = createHostContainedModalShell({
  prefix: "pva",
  portalScopeClassName: PVA_ROOT_CLASS,
  containedLayout: "dialog",
});

const emptyClassNames = {
  ...emptyStateCardBemClasses("pva"),
  withTitle: true as const,
};

type MetricCardProps = {
  label: string;
  value: string;
  /** Subtítulo sob o valor (texto ou slot). */
  hint?: ReactNode;
  /** Balão `?` ao lado do rótulo. */
  titleHint?: string;
  icon?: ReactNode;
  hero?: boolean;
  tone?: "default" | "danger";
  loading?: boolean;
};

function mapTone(tone: MetricCardProps["tone"]): MetricKpiCardTone {
  return tone === "danger" ? "negative" : "default";
}

/**
 * KPI da carteira — thin wrapper sobre `createMetricKpiCard("pva")`.
 */
export function MetricCard({
  label,
  value,
  hint,
  titleHint,
  icon,
  hero = false,
  tone = "default",
  loading = false,
}: MetricCardProps) {
  const props: DashboardMetricKpiCardProps = {
    label,
    value: loading ? "…" : value,
    hint,
    titleHint,
    icon,
    tone: mapTone(tone),
    fitValue: hero,
    className: hero ? "pva-kpi-card--wide delpi-ui-kpi-card--wide" : undefined,
  };
  return <MetricKpiBase {...props} />;
}

type EmptyStateProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  role?: "status" | "alert";
};

export function EmptyState({ title, description, action, role = "status" }: EmptyStateProps) {
  return (
    <KitEmptyState
      classNames={emptyClassNames}
      title={title}
      message={description}
      defaultMessage=""
      role={role}
    >
      {action}
    </KitEmptyState>
  );
}

export type StatusBadgeTone = StatusBadgeVariant;

type UiStatusBadgeProps = {
  tone?: StatusBadgeTone;
  children: ReactNode;
  className?: string;
};

/** Badge com children (texto) — status em tabelas e painéis. */
export function StatusBadge({ tone = "neutral", children, className }: UiStatusBadgeProps) {
  const label = typeof children === "string" ? children : String(children ?? "");
  return <StatusBadgeBase label={label} variant={tone} className={className} />;
}

export { StatusBadgeBase as PvaStatusBadge };
