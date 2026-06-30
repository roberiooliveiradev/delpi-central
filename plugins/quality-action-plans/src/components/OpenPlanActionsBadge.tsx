import { ListTodo } from "lucide-react";

import { openPlanActionsCountLabel } from "../utils/planActionCompletion";

type Props = {
  count: number;
  title?: string;
  onClick?: () => void;
};

const DEFAULT_TITLE =
  "Há ações do plano ainda não concluídas. Revise antes de aprovar a eficácia.";

export function OpenPlanActionsBadge({ count, title, onClick }: Props) {
  if (!count || count < 1) {
    return null;
  }

  const label = openPlanActionsCountLabel(count);
  const tooltip = title ?? DEFAULT_TITLE;
  const className = "pac-badge pac-badge--open-actions";

  if (onClick) {
    return (
      <button
        type="button"
        className={`${className} pac-badge--interactive`}
        title={tooltip}
        onClick={onClick}
      >
        <ListTodo size={13} strokeWidth={2.25} aria-hidden />
        <span>{label}</span>
      </button>
    );
  }

  return (
    <span className={className} title={tooltip} role="status">
      <ListTodo size={13} strokeWidth={2.25} aria-hidden />
      <span>{label}</span>
    </span>
  );
}
