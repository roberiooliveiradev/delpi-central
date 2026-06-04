import type { AdminSecuritySummary } from "../../../../data/api/adminTypes";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { buildSecuritySummaryView } from "./securitySummary";

type SecuritySummaryStripProps = {
  summary: AdminSecuritySummary | null | undefined;
  isLoading?: boolean;
};

export function SecuritySummaryStrip({
  summary,
  isLoading = false,
}: SecuritySummaryStripProps) {
  const view = buildSecuritySummaryView(summary);
  const windowLabel = summary?.windowHours ?? 24;

  return (
    <AdminSummaryStrip
      ariaLabel="Resumo de segurança operacional"
      isLoading={isLoading}
    >
      <AdminKpiCard
        title={`Bloqueios (${windowLabel}h)`}
        value={view.blocked}
        hint="Mensagens barradas no chat."
      />
      <AdminKpiCard
        title={`Sinalizados (${windowLabel}h)`}
        value={view.flagged}
        hint="Registrados na auditoria."
      />
      <AdminKpiCard
        title={`Scans admin (${windowLabel}h)`}
        value={view.scanned}
        hint="Testes pelo painel."
      />
      <AdminKpiCard title="Total eventos" value={view.totalEvents} hint="Na janela selecionada." />
    </AdminSummaryStrip>
  );
}
