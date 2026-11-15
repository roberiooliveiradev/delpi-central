import { CfStatusBadge } from "../../app/controllershipFinanceUi";
import {
  displayValue,
  severityBadgeVariant,
  severityIcon,
} from "./entryAuditPresentation";

/** Severidade com ícone + rótulo + tom de status (G5 / §19). */
export function EntryAuditSeverityBadge({
  severity,
}: {
  severity: string | null | undefined;
}) {
  const label = displayValue(severity);
  if (label === "—") {
    return <span aria-label="Severidade indisponível">—</span>;
  }
  return (
    <span className="cf-severity-badge">
      {severityIcon(severity)}
      <CfStatusBadge label={label} variant={severityBadgeVariant(severity)} />
    </span>
  );
}
