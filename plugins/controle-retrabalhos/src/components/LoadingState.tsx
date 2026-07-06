type LoadingStateProps = { message?: string };

export function LoadingState({ message = "Carregando…" }: LoadingStateProps) {
  return (
    <div className="cr-card cr-state-box" role="status" aria-live="polite">
      <p>{message}</p>
    </div>
  );
}
