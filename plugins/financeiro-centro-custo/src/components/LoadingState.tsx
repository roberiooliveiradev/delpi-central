type LoadingStateProps = {
  message?: string;
};

export function LoadingState({ message = "Carregando…" }: LoadingStateProps) {
  return (
    <div className="fcc-state fcc-state--loading" role="status" aria-live="polite">
      <span className="fcc-spinner" aria-hidden="true" />
      <p>{message}</p>
    </div>
  );
}
