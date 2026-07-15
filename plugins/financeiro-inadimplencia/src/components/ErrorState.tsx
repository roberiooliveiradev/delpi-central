type ErrorStateProps = {
  message: string;
  onRetry?: () => void;
};

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="fi-state fi-state--error" role="alert">
      <p>{message}</p>
      {onRetry ? (
        <button type="button" className="fi-btn fi-btn--secondary" onClick={onRetry}>
          Tentar novamente
        </button>
      ) : null}
    </div>
  );
}
