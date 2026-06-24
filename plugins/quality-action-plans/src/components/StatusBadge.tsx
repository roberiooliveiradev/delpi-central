import { nonconformityScopeLabel, severityLabel, statusLabel } from "../constants/actionPlans";

type StatusBadgeProps = {
  status: string;
};

export function StatusBadge({ status }: StatusBadgeProps) {
  return <span className={`pac-badge pac-badge--status pac-badge--status-${status}`}>{statusLabel(status)}</span>;
}

type SeverityBadgeProps = {
  severity: string;
};

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  return (
    <span className={`pac-badge pac-badge--severity pac-badge--severity-${severity}`}>
      {severityLabel(severity)}
    </span>
  );
}

type ScopeBadgeProps = {
  scope?: string | null;
};

export function ScopeBadge({ scope }: ScopeBadgeProps) {
  if (!scope) return <span className="pac-muted">—</span>;
  return (
    <span className={`pac-badge pac-badge--scope pac-badge--scope-${scope}`}>
      {nonconformityScopeLabel(scope)}
    </span>
  );
}
