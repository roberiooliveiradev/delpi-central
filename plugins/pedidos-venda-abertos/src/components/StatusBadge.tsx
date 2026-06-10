import type { StatusBadgeDescriptor } from "../utils/statusBadges";

type StatusBadgeProps = {
  badge: Pick<StatusBadgeDescriptor, "label" | "tone">;
};

export function StatusBadge({ badge }: StatusBadgeProps) {
  return <span className={`pva-badge pva-badge--${badge.tone}`}>{badge.label}</span>;
}
