import { ActionButton, HintAction } from "@delpi/plugin-ui/index";

import { resolveActionPresentation } from "../content/resolveActionPresentation";
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
      {visible.map((action) => {
        const presentation = resolveActionPresentation(action);
        const { Icon } = presentation;
        return (
          <HintAction
            key={action}
            hint={presentation.help}
            ariaLabel={`Ajuda: ${presentation.label}`}
            placement="top"
          >
            <ActionButton
              type="button"
              variant={presentation.variant}
              disabled={busy}
              onClick={() => onAction(action)}
            >
              <Icon aria-hidden size={16} strokeWidth={2} />
              {presentation.label}
            </ActionButton>
          </HintAction>
        );
      })}
    </MyRequestsFormActions>
  );
}
