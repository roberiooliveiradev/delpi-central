type OeeStatus = "valid" | "outlier" | string;

type OeeStatusBadgeProps = {
  status: OeeStatus;
};

function statusLabel(status: OeeStatus): string {
  if (status === "valid") return "Válido";
  if (status === "outlier") return "Fora da faixa";
  return status;
}

function statusClass(status: OeeStatus): string {
  if (status === "valid") return "dp-kpi-badge dp-kpi-badge--success";
  if (status === "outlier") return "dp-kpi-badge dp-kpi-badge--warning";
  return "dp-kpi-badge";
}

export function OeeStatusBadge({ status }: OeeStatusBadgeProps) {
  return <span className={statusClass(status)}>{statusLabel(status)}</span>;
}
