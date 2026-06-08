import { ChevronLeft, ChevronRight, Eye } from "lucide-react";

import {
  auditStatusLabel,
  auditStatusVariant,
  canAccessNc,
  sensoName,
  shiftLabel,
} from "../constants/audit5s";
import type { AuditDashboardItem, AuditDashboardPagination } from "../types/auditDashboard";
import { formatPersonNamesList } from "../utils/formatPersonName";
import { formatDisplayDate, formatPercent } from "../utils/dates";

type Props = {
  items: AuditDashboardItem[];
  pagination: AuditDashboardPagination;
  filteredSensoOrder?: number | null;
  filteredSensoName?: string | null;
  onPageChange: (page: number) => void;
  onOpenItem: (item: AuditDashboardItem) => void;
};

export function AuditDashboardTable({
  items,
  pagination,
  filteredSensoOrder,
  filteredSensoName,
  onPageChange,
  onOpenItem,
}: Props) {
  const sensoColumnLabel =
    filteredSensoOrder != null
      ? sensoName(filteredSensoOrder, filteredSensoName ?? undefined)
      : null;
  const totalPages = pagination.total_pages || 1;
  const canPrev = pagination.page > 1;
  const canNext = pagination.page < totalPages;

  return (
    <section className="a5s-analytics-table-section">
      <header className="a5s-analytics-table-section__head">
        <h2>Auditorias detalhadas</h2>
        <span>
          {pagination.total} registro{pagination.total === 1 ? "" : "s"}
        </span>
      </header>

      <div className="a5s-table-wrap">
        <table className="a5s-table">
          <thead>
            <tr>
              <th>Código</th>
              <th>Data</th>
              <th>Área</th>
              <th>Turno</th>
              <th>Auditores</th>
              <th>{sensoColumnLabel ?? "Nota geral"}</th>
              <th>Status</th>
              <th>NCs</th>
              <th aria-label="Ações" />
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={9} className="a5s-table__empty">
                  Nenhuma auditoria encontrada com os filtros atuais.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id}>
                  <td data-label="Código">{item.audit_code}</td>
                  <td data-label="Data">{formatDisplayDate(item.audit_date)}</td>
                  <td data-label="Área">{item.area_name}</td>
                  <td data-label="Turno">{shiftLabel(item.shift)}</td>
                  <td data-label="Auditores">{formatPersonNamesList(item.auditor_names)}</td>
                  <td data-label={sensoColumnLabel ?? "Nota geral"}>
                    {formatPercent(
                      sensoColumnLabel ? item.senso_score_pct ?? null : item.overall_score_pct,
                    )}
                  </td>
                  <td data-label="Status">
                    <span
                      className={`a5s-status-badge a5s-status-badge--${auditStatusVariant(item.status)} a5s-status-badge--table`}
                    >
                      {auditStatusLabel(item.status)}
                    </span>
                  </td>
                  <td data-label="NCs">
                    {item.nc_open > 0
                      ? `${item.nc_open} aberta${item.nc_open === 1 ? "" : "s"} / ${item.nc_total}`
                      : item.nc_total > 0
                        ? `${item.nc_total} finalizada${item.nc_total === 1 ? "" : "s"}`
                        : "—"}
                  </td>
                  <td data-label="Ações">
                    <button
                      type="button"
                      className="a5s-btn a5s-btn--table-action"
                      title={canAccessNc(item.status) ? "Tratar NC" : "Ver auditoria"}
                      onClick={() => onOpenItem(item)}
                    >
                      <Eye size={18} aria-hidden />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pagination.total > pagination.page_size ? (
        <div className="a5s-table-pagination">
          <button
            type="button"
            className="a5s-btn a5s-btn--ghost a5s-btn--small"
            disabled={!canPrev}
            onClick={() => onPageChange(pagination.page - 1)}
          >
            <ChevronLeft size={16} aria-hidden />
            Anterior
          </button>
          <span>
            Página {pagination.page} de {totalPages}
          </span>
          <button
            type="button"
            className="a5s-btn a5s-btn--ghost a5s-btn--small"
            disabled={!canNext}
            onClick={() => onPageChange(pagination.page + 1)}
          >
            Próxima
            <ChevronRight size={16} aria-hidden />
          </button>
        </div>
      ) : null}
    </section>
  );
}
