import { delpiUiClass } from "@delpi/plugin-ui/index";

type ErrorStateProps = {
  message: string;
  onRetry?: () => void;
};

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div
      className={delpiUiClass(
        "cr-card cr-state-box cr-state-box--error",
        "delpi-ui-card delpi-ui-state-box delpi-ui-state-box--error",
      )}
      role="alert"
    >
      <p>{message}</p>
      {onRetry ? (
        <button type="button" className="cr-btn cr-btn--primary" onClick={onRetry}>
          Tentar novamente
        </button>
      ) : null}
    </div>
  );
}
