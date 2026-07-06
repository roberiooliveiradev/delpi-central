type ErrorStateProps = {
  message: string;
  onRetry?: () => void;
};

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="cr-card cr-state-box cr-state-box--error" role="alert">
      <p>{message}</p>
      {onRetry ? (
        <button type="button" className="cr-btn cr-btn--primary" onClick={onRetry}>
          Tentar novamente
        </button>
      ) : null}
    </div>
  );
}
