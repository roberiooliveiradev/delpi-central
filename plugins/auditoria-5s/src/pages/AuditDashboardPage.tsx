import type { AuditArea, AuditListItem } from "../api/audit5sApi";
import type { AuditDashboardItem } from "../types/auditDashboard";
import { formatPeriodLabel } from "../utils/dates";
import { AuditDashboardCharts } from "../components/AuditDashboardCharts";
import { AuditDashboardFilters } from "../components/AuditDashboardFilters";
import { AuditDashboardKpis } from "../components/AuditDashboardKpis";
import { AuditDashboardTable } from "../components/AuditDashboardTable";
import { useAudit5sDashboard } from "../hooks/useAudit5sDashboard";
import { useAudit5sDashboardFilters } from "../hooks/useAudit5sDashboardFilters";

type Props = {
  branch: string;
  areas: AuditArea[];
  audits: AuditListItem[];
  onOpenItem: (item: AuditDashboardItem) => void;
};

export function AuditDashboardPage({ branch, areas, audits, onOpenItem }: Props) {
  const filters = useAudit5sDashboardFilters(branch, audits);
  const { data, loading, error, reload, isRefreshing } = useAudit5sDashboard(filters.apiParams);

  const periodLabel = formatPeriodLabel(filters.filters.dateStart, filters.filters.dateEnd);

  return (
    <div className="a5s-analytics">
      <div className="a5s-analytics__intro">
        <div>
          <h2 className="a5s-analytics__title">Dashboard gerencial</h2>
          <p className="a5s-analytics__subtitle">
            Evolução das auditorias 5S — fábrica {branch} · {periodLabel}
          </p>
        </div>
      </div>

      <AuditDashboardFilters
        areas={areas}
        dateStart={filters.filters.dateStart}
        dateEnd={filters.filters.dateEnd}
        areaId={filters.filters.areaId}
        shift={filters.filters.shift}
        auditStatus={filters.filters.auditStatus}
        sensoOrder={filters.filters.sensoOrder}
        granularity={filters.filters.granularity}
        loading={loading}
        onDateStartChange={filters.setDateStart}
        onDateEndChange={filters.setDateEnd}
        onAreaIdChange={filters.setAreaId}
        onShiftChange={filters.setShift}
        onAuditStatusChange={filters.setAuditStatus}
        onSensoOrderChange={filters.setSensoOrder}
        onGranularityChange={filters.setGranularity}
        onReload={reload}
      />

      {error ? <div className="a5s-alert a5s-alert--error">{error}</div> : null}

      {loading && !data ? (
        <p className="a5s-analytics-loading">Carregando dashboard…</p>
      ) : null}

      {data ? (
        <div className={isRefreshing ? "a5s-analytics__content a5s-analytics__content--refresh" : "a5s-analytics__content"}>
          <AuditDashboardKpis summary={data.summary} />

          {data.summary.audit_count === 0 ? (
            <div className="a5s-alert a5s-alert--success">
              Nenhuma auditoria encontrada no período com os filtros selecionados.
            </div>
          ) : (
            <>
              <AuditDashboardCharts
                charts={data.charts}
                filteredSensoOrder={data.summary.filtered_senso_order}
                filteredSensoName={data.summary.filtered_senso_name}
              />
              <AuditDashboardTable
                items={data.items}
                pagination={data.pagination}
                filteredSensoOrder={data.summary.filtered_senso_order}
                filteredSensoName={data.summary.filtered_senso_name}
                onPageChange={filters.setPage}
                onOpenItem={onOpenItem}
              />
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}
