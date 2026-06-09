import type { StatusBadgeDescriptor } from "../utils/statusBadges";

type StatusBadgeProps = {
  badge: StatusBadgeDescriptor;
};

export function StatusBadge({ badge }: StatusBadgeProps) {
  return <span className={`pva-badge pva-badge--${badge.tone}`}>{badge.label}</span>;
}
