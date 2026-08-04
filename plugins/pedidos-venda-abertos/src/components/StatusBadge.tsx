import type { StatusBadgeDescriptor } from "../utils/statusBadges";
import { PvaStatusBadge } from "../ui/pvaKit";

type StatusBadgeProps = {
  badge: Pick<StatusBadgeDescriptor, "label" | "tone">;
};

export function StatusBadge({ badge }: StatusBadgeProps) {
  return <PvaStatusBadge label={badge.label} variant={badge.tone} />;
}
