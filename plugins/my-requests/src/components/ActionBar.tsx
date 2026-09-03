import type { AllowedAction } from "../types/requests";

type ActionBarProps = {
  actions: AllowedAction[];
  busy?: boolean;
  onAction: (action: string) => void;
};

/** Render-only: actions come from API `allowed_actions` — no state machine in the MFE. */
export function ActionBar({ actions, busy = false, onAction }: ActionBarProps) {
  if (!actions.length) {
    return (
      <p className="dashboard-my-requests__muted">Nenhuma ação disponível neste status.</p>
    );
  }
  return (
    <div className="dashboard-my-requests__action-bar" role="group" aria-label="Ações permitidas">
      {actions.map((action) => (
        <button
          key={action}
          type="button"
          className="dashboard-my-requests__btn"
          disabled={busy}
          onClick={() => onAction(action)}
        >
          {action}
        </button>
      ))}
    </div>
  );
}
