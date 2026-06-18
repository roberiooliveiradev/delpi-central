import type { ResultBadgeDescriptor } from "../utils/resultBadge";

type ResultBadgeProps = {
  badge: ResultBadgeDescriptor;
};

export function ResultBadge({ badge }: ResultBadgeProps) {
  return <span className={`ie-badge ie-badge--${badge.tone}`}>{badge.label}</span>;
}
