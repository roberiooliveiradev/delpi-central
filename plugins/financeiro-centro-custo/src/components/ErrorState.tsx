type ErrorStateProps = {
  message: string;
  onRetry?: () => void;
};

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="fcc-state fcc-state--error" role="alert">
      <p>{message}</p>
      {onRetry ? (
        <button type="button" className="fcc-btn fcc-btn--secondary" onClick={onRetry}>
          Tentar novamente
        </button>
      ) : null}
    </div>
  );
}
