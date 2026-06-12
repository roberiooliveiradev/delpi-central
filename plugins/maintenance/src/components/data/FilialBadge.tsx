type FilialBadgeProps = {
  filial: string;
  label?: string;
};

export function FilialBadge({ filial, label = "Filial operacional" }: FilialBadgeProps) {
  return (
    <p className="dm-filial-badge">
      {label}: {filial}
    </p>
  );
}
