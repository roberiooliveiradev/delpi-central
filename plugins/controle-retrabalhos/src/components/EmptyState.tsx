type EmptyStateProps = { message?: string };

export function EmptyState({ message = "Nenhum registro encontrado para o período." }: EmptyStateProps) {
  return (
    <div className="cr-card cr-state-box cr-state-box--empty">
      <p>{message}</p>
    </div>
  );
}
