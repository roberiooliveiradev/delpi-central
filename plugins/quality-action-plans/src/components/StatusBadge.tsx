import { severityLabel, statusLabel } from "../constants/actionPlans";

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
