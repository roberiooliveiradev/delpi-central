import { ActionButton } from "@delpi/plugin-ui/index";

import type { AllowedAction } from "../types/requests";
import { MyRequestsEmptyState, MyRequestsFormActions } from "../ui/mrUi";

type ActionBarProps = {
  actions: AllowedAction[];
  busy?: boolean;
  onAction: (action: string) => void;
};

/** Render-only: actions come from API `allowed_actions` — no state machine in the MFE. */
export function ActionBar({ actions, busy = false, onAction }: ActionBarProps) {
  if (!actions.length) {
    return <MyRequestsEmptyState message="Nenhuma ação disponível neste status." />;
  }
  return (
    <MyRequestsFormActions>
      {actions.map((action) => (
        <ActionButton
          key={action}
          type="button"
          variant="primary"
          disabled={busy}
          onClick={() => onAction(action)}
        >
          {action}
        </ActionButton>
      ))}
    </MyRequestsFormActions>
  );
}
