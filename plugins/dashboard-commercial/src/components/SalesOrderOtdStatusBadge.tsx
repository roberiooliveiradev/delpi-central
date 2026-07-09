type SalesOrderOtdLineStatus = "on_time" | "late" | string;

type SalesOrderOtdStatusBadgeProps = {
  status: SalesOrderOtdLineStatus;
};

function statusLabel(status: SalesOrderOtdLineStatus): string {
  if (status === "on_time") return "No prazo";
  if (status === "late") return "Atrasado";
  return status;
}

function statusClass(status: SalesOrderOtdLineStatus): string {
  if (status === "on_time") return "dc-kpi-badge dc-kpi-badge--success";
  if (status === "late") return "dc-kpi-badge dc-kpi-badge--warning";
  return "dc-kpi-badge";
}

export function SalesOrderOtdStatusBadge({ status }: SalesOrderOtdStatusBadgeProps) {
  return <span className={statusClass(status)}>{statusLabel(status)}</span>;
}
