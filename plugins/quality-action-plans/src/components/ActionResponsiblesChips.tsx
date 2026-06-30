import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ActionResponsible, PlanAction } from "../types/actionPlan";
import { responsiblesFromAction } from "../utils/actionResponsibles";

type Props = {
  responsibles?: ActionResponsible[];
  action?: PlanAction;
  layout?: "inline" | "stack";
  showQueueBadge?: boolean;
  emptyLabel?: string;
};

export function ActionResponsiblesChips({
  responsibles,
  action,
  layout = "inline",
  showQueueBadge = true,
  emptyLabel = "—",
}: Props) {
  const items = responsibles ?? (action ? responsiblesFromAction(action) : []);
  if (!items.length) {
    return <span className="pac-muted">{emptyLabel}</span>;
  }

  return (
    <ul
      className={`pac-action-responsibles-chips pac-action-responsibles-chips--${layout}`}
      aria-label="Responsáveis"
    >
      {items.map((item) => {
        const linked = Boolean(item.user_id?.trim());
        const key = item.id ?? `${item.display_name}-${item.user_id ?? "free"}`;
        return (
          <li
            key={key}
            className={`pac-action-responsibles-chip${linked ? " pac-action-responsibles-chip--linked" : ""}`}
          >
            <span className="pac-action-responsibles-chip__name">{item.display_name}</span>
            {showQueueBadge && linked ? (
              <span
                className="pac-action-responsibles-chip__queue"
                title={PAC_HELP_TOOLTIPS.form.actionResponsibleLinked}
              >
                Fila
              </span>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}
