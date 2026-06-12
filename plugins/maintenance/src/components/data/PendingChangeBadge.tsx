type PendingChangeBadgeProps = {
  visible: boolean;
};

export function PendingChangeBadge({ visible }: PendingChangeBadgeProps) {
  if (!visible) return null;
  return <span className="dm-badge dm-badge--warning">Alterado — salvar</span>;
}
