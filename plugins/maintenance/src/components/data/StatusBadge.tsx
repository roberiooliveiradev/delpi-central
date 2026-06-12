type StatusBadgeProps = {
  status: string;
  onClick?: () => void;
};

function statusClass(status: string): string {
  if (status === "CRÍTICO") return "dm-badge dm-badge--danger";
  if (status === "ATENÇÃO") return "dm-badge dm-badge--warning";
  if (status === "OK") return "dm-badge dm-badge--success";
  return "dm-badge";
}

export function StatusBadge({ status, onClick }: StatusBadgeProps) {
  if (onClick) {
    return (
      <button type="button" className={statusClass(status)} onClick={onClick}>
        {status}
      </button>
    );
  }

  return <span className={statusClass(status)}>{status}</span>;
}
