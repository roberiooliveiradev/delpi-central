type FilialBadgeProps = {
  /** Código da filial (fallback se displayName não vier). */
  filial: string;
  /** Nome exibido ao usuário (catálogo /options). */
  displayName?: string;
  label?: string;
};

export function FilialBadge({
  filial,
  displayName,
  label = "Filial operacional",
}: FilialBadgeProps) {
  const text = displayName?.trim() || filial;

  return (
    <p className="dm-filial-badge">
      {label}: {text}
    </p>
  );
}
