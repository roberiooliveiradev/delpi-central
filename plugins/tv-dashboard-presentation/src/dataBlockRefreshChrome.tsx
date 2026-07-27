/** Badge de refresh sobre conteúdo já renderizado (não só placeholder). */
export function DataBlockRefreshBadge({ loading }: { loading?: boolean }) {
  if (!loading) return null;
  return (
    <span className="tdp-data-block__refresh-badge" aria-live="polite">
      Atualizando…
    </span>
  );
}

export function withDataBlockLoadingClass(baseClass: string, loading?: boolean): string {
  return [baseClass, loading ? "tdp-data-block--refreshing" : null].filter(Boolean).join(" ");
}
