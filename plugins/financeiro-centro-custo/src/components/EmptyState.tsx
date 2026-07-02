type EmptyStateProps = {
  title?: string;
  message?: string;
};

export function EmptyState({
  title = "Nenhum dado encontrado",
  message = "Ajuste os filtros ou o período para visualizar resultados.",
}: EmptyStateProps) {
  return (
    <div className="fcc-state fcc-state--empty">
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}
