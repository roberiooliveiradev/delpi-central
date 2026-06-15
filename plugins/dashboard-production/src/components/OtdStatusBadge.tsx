type OtdStatus = "on_time" | "late" | string;

type OtdStatusBadgeProps = {
  status: OtdStatus;
};

function statusLabel(status: OtdStatus): string {
  if (status === "on_time") return "No prazo";
  if (status === "late") return "Atrasado";
  return status;
}

function statusClass(status: OtdStatus): string {
  if (status === "on_time") return "dp-kpi-badge dp-kpi-badge--success";
  if (status === "late") return "dp-kpi-badge dp-kpi-badge--danger";
  return "dp-kpi-badge";
}

export function OtdStatusBadge({ status }: OtdStatusBadgeProps) {
  return <span className={statusClass(status)}>{statusLabel(status)}</span>;
}
