import { ActionButton } from "@delpi/plugin-ui/index";

import { actionButtonVariant, actionLabel } from "../content/presentationLabels";
import type { AllowedAction } from "../types/requests";
import { filterDetailBarActions } from "../utils/operationalActions";
import { MyRequestsEmptyState, MyRequestsFormActions } from "../ui/mrUi";

type ActionBarProps = {
  actions: AllowedAction[];
  busy?: boolean;
  onAction: (action: string) => void;
};

/** Render-only: actions come from API `allowed_actions` — no state machine in the MFE. */
export function ActionBar({ actions, busy = false, onAction }: ActionBarProps) {
  const visible = filterDetailBarActions(actions);
  if (!visible.length) {
    return <MyRequestsEmptyState message="Nenhuma ação disponível neste status." />;
  }
  return (
    <MyRequestsFormActions>
      {visible.map((action) => (
        <ActionButton
          key={action}
          type="button"
          variant={actionButtonVariant(action)}
          disabled={busy}
          onClick={() => onAction(action)}
        >
          {actionLabel(action)}
        </ActionButton>
      ))}
    </MyRequestsFormActions>
  );
}
