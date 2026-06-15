import {
  isOeeAppointmentOutlier,
  isProductionEfficiencyLow,
} from "../constants/businessRules";

type OeeStatus = "valid" | "outlier" | string;

type OeeStatusBadgeProps = {
  status: OeeStatus;
  oeePct?: number | null;
};

export function OeeStatusBadge({ status, oeePct }: OeeStatusBadgeProps) {
  if (isOeeAppointmentOutlier(status, oeePct)) {
    return <span className="dp-kpi-badge dp-kpi-badge--danger">Verificar</span>;
  }

  if (isProductionEfficiencyLow(oeePct)) {
    return <span className="dp-kpi-badge dp-kpi-badge--warning">Eficiência baixa</span>;
  }

  if (status === "valid") {
    return <span className="dp-kpi-badge dp-kpi-badge--success">OK</span>;
  }

  return <span className="dp-kpi-badge">OK</span>;
}
