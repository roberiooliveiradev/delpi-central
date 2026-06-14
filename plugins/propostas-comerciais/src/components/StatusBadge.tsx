import { formatStatusLabel } from "../utils/format";

type StatusBadgeProps = {
  status: string;
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = status.trim().toUpperCase();
  const label = formatStatusLabel(status);
  const tone = normalized === "A" ? "success" : "neutral";

  return <span className={`pc-badge pc-badge--${tone}`}>{label}</span>;
}
