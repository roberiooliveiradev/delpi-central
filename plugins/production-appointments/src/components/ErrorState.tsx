type ErrorStateProps = {
  message: string;
  onRetry?: () => void;
};

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="pa-card pa-state-box pa-state-box--error" role="alert">
      <p>{message}</p>
      {onRetry ? (
        <button type="button" className="pa-btn pa-btn--primary" onClick={onRetry}>
          Tentar novamente
        </button>
      ) : null}
    </div>
  );
}
