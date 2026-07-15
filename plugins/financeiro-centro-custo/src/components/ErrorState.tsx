import { delpiUiClass } from "@delpi/plugin-ui/index";

type ErrorStateProps = {
  message: string;
  onRetry?: () => void;
};

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div
      className={delpiUiClass(
        "fcc-card fcc-state-box fcc-state-box--error",
        "delpi-ui-card delpi-ui-state-box delpi-ui-state-box--error",
      )}
      role="alert"
    >
      <p>{message}</p>
      {onRetry ? (
        <button type="button" className="fcc-btn fcc-btn--secondary" onClick={onRetry}>
          Tentar novamente
        </button>
      ) : null}
    </div>
  );
}
