import { Download } from "lucide-react";

import {
  PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
  PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
  isOeeAppointmentOutlier,
} from "../constants/businessRules";
import type { ProductionOeeAppointmentItem } from "../types/production";
import { formatDisplayDate, formatDisplayTime } from "../utils/dates";
import { formatNumber } from "../utils/format";

type OeeAppointmentsTableProps = {
  items: ProductionOeeAppointmentItem[];
  total: number;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onRowClick?: (row: ProductionOeeAppointmentItem) => void;
  onExportCsv?: () => void;
  exporting?: boolean;
  disabled?: boolean;
  loading?: boolean;
};

function formatOeePercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}

export function OeeAppointmentsTable({
  items,
  total,
  page,
  totalPages,
  onPageChange,
  onRowClick,
  onExportCsv,
  exporting = false,
  disabled = false,
  loading = false,
}: OeeAppointmentsTableProps) {
  const safeTotalPages = Math.max(totalPages, 1);

  return (
    <section className="dp-appointments-table-card" aria-label="Apontamentos">
      <header className="dp-appointments-table-card__header">
        <div>
          <h2 className="dp-section-title">Apontamentos</h2>
          <p>{total.toLocaleString("pt-BR")} registro(s) no período</p>
        </div>
        <div className="dp-appointments-table-card__actions">
          {onExportCsv ? (
            <button
              type="button"
              className="dp-ghost-btn"
              disabled={disabled || exporting || total <= 0}
              onClick={onExportCsv}
              aria-busy={exporting}
            >
              <Download size={16} aria-hidden />
              {exporting ? "Exportando…" : "Exportar CSV"}
            </button>
          ) : null}
          <div className="dp-appointments-pagination">
            <button
              type="button"
              className="dp-ghost-btn"
              disabled={disabled || page <= 1}
              onClick={() => onPageChange(page - 1)}
            >
              Anterior
            </button>
            <span>
              Página {page} de {safeTotalPages}
            </span>
            <button
              type="button"
              className="dp-ghost-btn"
              disabled={disabled || page >= safeTotalPages}
              onClick={() => onPageChange(page + 1)}
            >
              Próxima
            </button>
          </div>
        </div>
      </header>

      <p className="dp-efficiency-legend dp-efficiency-legend--warning">
        Atenção: apontamentos com eficiência fora da faixa {PRODUCTION_EFFICIENCY_VALID_MIN_PCT}–
        {PRODUCTION_EFFICIENCY_VALID_MAX_PCT}% são desconsiderados no indicador de OEE (KPIs e gráficos)
        e aparecem na tabela como &quot;Verificar&quot;. Clique em uma linha para abrir roteiro,
        estrutura e análise de tempos.
      </p>

      <div className="dp-appointments-table-wrap">
        <table
          className={
            onRowClick ? "dp-appointments-table dp-appointments-table--clickable" : "dp-appointments-table"
          }
        >
          <thead>
            <tr>
              <th>Data</th>
              <th>Início</th>
              <th>Fim</th>
              <th>Qtd. apontada</th>
              <th>Filial</th>
              <th>OP</th>
              <th>Descrição produto</th>
              <th>CT</th>
              <th>Operador</th>
              <th>Eficiência</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={11} className="dp-appointments-table__empty">
                  Carregando apontamentos…
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={11} className="dp-appointments-table__empty">
                  Nenhum apontamento para os filtros selecionados.
                </td>
              </tr>
            ) : (
              items.map((item) => {
                const isOutlier = isOeeAppointmentOutlier(item.status, item.oee_pct);
                const rowClass = [
                  isOutlier ? "dp-row dp-row--verify" : "dp-row",
                  onRowClick ? "is-clickable" : "",
                ]
                  .filter(Boolean)
                  .join(" ");

                return (
                  <tr
                    key={String(item.appointment_id)}
                    className={rowClass}
                    onClick={onRowClick ? () => onRowClick(item) : undefined}
                    onKeyDown={
                      onRowClick
                        ? (event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              onRowClick(item);
                            }
                          }
                        : undefined
                    }
                    tabIndex={onRowClick ? 0 : undefined}
                    role={onRowClick ? "button" : undefined}
                  >
                    <td data-label="Data">{formatDisplayDate(item.production_date)}</td>
                    <td data-label="Início">{formatDisplayTime(item.start_time)}</td>
                    <td data-label="Fim">{formatDisplayTime(item.end_time)}</td>
                    <td data-label="Qtd. apontada">{formatNumber(item.produced_qty, 3)}</td>
                    <td data-label="Filial">{item.branch ?? "—"}</td>
                    <td data-label="OP">{item.production_order ?? "—"}</td>
                    <td data-label="Descrição produto">
                      {item.product_description?.trim() || item.product_code || "—"}
                    </td>
                    <td data-label="CT">{item.work_center ?? "—"}</td>
                    <td data-label="Operador">{item.operator_code ?? "—"}</td>
                    <td data-label="Eficiência">{formatOeePercent(item.oee_pct)}</td>
                    <td data-label="Status">
                      {isOutlier ? (
                        <span className="dp-appointment-badge dp-appointment-badge--danger">
                          Verificar
                        </span>
                      ) : (
                        <span className="dp-appointment-badge">OK</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
