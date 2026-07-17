import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type StatusBadgeVariant = "neutral" | "info" | "success" | "warning" | "danger";

export type StatusBadgeClassNames = {
  badge: string;
};

export type StatusBadgeProps = {
  label: string;
  variant?: StatusBadgeVariant;
  classNames: StatusBadgeClassNames;
  className?: string;
};

export function statusBadgeBemClasses(prefix: string): StatusBadgeClassNames {
  return {
    badge: delpiUiClass(`${prefix}-status-badge`, "delpi-ui-status-badge"),
  };
}

export function StatusBadge({
  label,
  variant = "neutral",
  classNames,
  className,
}: StatusBadgeProps) {
  const rootClass = [
    withBemModifier(classNames.badge, variant),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return <span className={rootClass}>{label}</span>;
}

export type DashboardStatusBadgeProps = Omit<StatusBadgeProps, "classNames">;

export function createDashboardStatusBadge(config: { prefix: string }) {
  const classNames = statusBadgeBemClasses(config.prefix);

  return function DashboardStatusBadge(props: DashboardStatusBadgeProps) {
    return <StatusBadge classNames={classNames} {...props} />;
  };
}
