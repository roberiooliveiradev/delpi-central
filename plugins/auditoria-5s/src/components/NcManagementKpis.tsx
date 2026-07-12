import { AlertTriangle, CheckCircle2, ClipboardList, ListChecks } from "lucide-react";

import type { NcBoardSummary } from "../types/ncManagement";
import { KpiCard } from "./KpiCard";

type Props = {
  summary: NcBoardSummary;
};

export function NcManagementKpis({ summary }: Props) {
  const activeCount = summary.nc_open + summary.nc_in_progress;
  const pendingCount = summary.nc_pending ?? 0;
  const closedPct =
    summary.nc_total > 0
      ? Math.round((summary.nc_closed / summary.nc_total) * 100)
      : null;

  return (
    <div className="a5s-nc-board-kpis">
      <KpiCard
        title="Total de NCs"
        value={String(summary.nc_total)}
        icon={<ClipboardList size={22} />}
      />
      <KpiCard
        title="Em aberto"
        value={String(activeCount)}
        subtitle={
          pendingCount > 0
            ? `${pendingCount} aguardando registro · ${summary.nc_in_progress} em tratamento`
            : `${summary.nc_open} aguardando plano · ${summary.nc_in_progress} em tratamento`
        }
        icon={<ListChecks size={22} />}
      />
      <KpiCard
        title="Finalizadas"
        value={String(summary.nc_closed)}
        subtitle={closedPct != null ? `${closedPct}% do total` : undefined}
        variant="success"
        icon={<CheckCircle2 size={22} />}
      />
      <KpiCard
        title="Em atraso"
        value={String(summary.nc_overdue)}
        subtitle={summary.nc_overdue > 0 ? "Requer atenção imediata" : "Nenhuma em atraso"}
        variant="danger"
        icon={<AlertTriangle size={22} />}
      />
    </div>
  );
}
