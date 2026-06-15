import { ArrowDown, ArrowUp, ArrowUpDown, FileSpreadsheet } from "lucide-react";
import { useCallback, useState } from "react";

import { isProductionEfficiencyOutlier } from "../constants/businessRules";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";
import type { AppointmentsSortColumn, SortDirection } from "../utils/appointmentsTableSort";
import { formatDisplayDate } from "../utils/dates";
import { exportAppointmentsExcel } from "../utils/exportAppointmentsExcel";
import { formatCurrency, formatNumber, formatPercent } from "../utils/format";

type SortableColumn = {
  id: AppointmentsSortColumn;
  label: string;
};

const SORTABLE_COLUMNS: SortableColumn[] = [
  { id: "data_producao", label: "Data" },
  { id: "hora_inicio", label: "Início" },
  { id: "hora_final", label: "Fim" },
  { id: "qtd_apontada", label: "Qtd. apontada" },
  { id: "filial", label: "Filial" },
  { id: "op", label: "OP" },
  { id: "descricao_produto", label: "Descrição produto" },
  { id: "centro_trabalho", label: "CT" },
  { id: "operador", label: "Operador" },
  { id: "eficiencia_percentual", label: "Eficiência" },
  { id: "resultado_mod", label: "Resultado MOD" },
  { id: "status", label: "Status" },
];

type AppointmentsTableProps = {
  items: EficienciaFabrilItem[];
  exportItems: EficienciaFabrilItem[];
  exportDateStart: string;
  exportDateEnd: string;
  page: number;
  totalPages: number;
  total: number;
  sortBy: AppointmentsSortColumn;
  sortDir: SortDirection;
  onSortChange: (column: AppointmentsSortColumn) => void;
  onPageChange: (page: number) => void;
  onRowClick?: (item: EficienciaFabrilItem) => void;
  onExportError?: (message: string) => void;
  disabled?: boolean;
};

function SortIndicator({
  column,
  sortBy,
  sortDir,
}: {
  column: AppointmentsSortColumn;
  sortBy: AppointmentsSortColumn;
  sortDir: SortDirection;
}) {
  if (column !== sortBy) {
    return <ArrowUpDown size={14} className="ef-sortable-th__icon ef-sortable-th__icon--idle" />;
  }

  return sortDir === "asc" ? (
    <ArrowUp size={14} className="ef-sortable-th__icon" aria-hidden />
  ) : (
    <ArrowDown size={14} className="ef-sortable-th__icon" aria-hidden />
  );
}

export function AppointmentsTable({
  items,
  exportItems,
  exportDateStart,
  exportDateEnd,
  page,
  totalPages,
  total,
  sortBy,
  sortDir,
  onSortChange,
  onPageChange,
  onRowClick,
  onExportError,
  disabled = false,
}: AppointmentsTableProps) {
  const [exporting, setExporting] = useState(false);

  const handleExportExcel = useCallback(async () => {
    if (exporting || total <= 0) return;

    setExporting(true);
    try {
      await exportAppointmentsExcel(exportItems, exportDateStart, exportDateEnd);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Não foi possível exportar o Excel.";
      onExportError?.(message);
    } finally {
      setExporting(false);
    }
  }, [exportDateEnd, exportDateStart, exportItems, exporting, onExportError, total]);

  return (
    <section className="ef-table-card" aria-label="Apontamentos">
      <header className="ef-table-card__header">
        <div>
          <h2>Apontamentos</h2>
          <p>{total.toLocaleString("pt-BR")} registro(s) no período</p>
        </div>
        <div className="ef-table-card__actions">
          <button
            type="button"
            className="ef-btn ef-btn--ghost"
            disabled={disabled || exporting || total <= 0}
            onClick={() => void handleExportExcel()}
            aria-busy={exporting}
          >
            <FileSpreadsheet size={16} aria-hidden />
            {exporting ? "Exportando…" : "Exportar Excel"}
          </button>
          <div className="ef-pagination">
            <button
              type="button"
              className="ef-btn ef-btn--ghost"
              disabled={disabled || page <= 1}
              onClick={() => onPageChange(page - 1)}
            >
              Anterior
            </button>
            <span>
              Página {page} de {Math.max(totalPages, 1)}
            </span>
            <button
              type="button"
              className="ef-btn ef-btn--ghost"
              disabled={disabled || page >= totalPages}
              onClick={() => onPageChange(page + 1)}
            >
              Próxima
            </button>
          </div>
        </div>
      </header>

      <div className="ef-table-wrap">
        <table className="ef-table">
          <thead>
            <tr>
              {SORTABLE_COLUMNS.map((column) => {
                const isActive = sortBy === column.id;
                return (
                  <th key={column.id} scope="col" aria-sort={isActive ? (sortDir === "asc" ? "ascending" : "descending") : "none"}>
                    <button
                      type="button"
                      className={`ef-sortable-th${isActive ? " ef-sortable-th--active" : ""}`}
                      disabled={disabled}
                      onClick={() => onSortChange(column.id)}
                    >
                      <span>{column.label}</span>
                      <SortIndicator column={column.id} sortBy={sortBy} sortDir={sortDir} />
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={12} className="ef-table__empty">
                  Nenhum apontamento para os filtros selecionados.
                </td>
              </tr>
            ) : (
              items.map((item, index) => {
                const isOutlier = isProductionEfficiencyOutlier(item.eficiencia_percentual);
                const isClickable = Boolean(item.appointment_id) && Boolean(onRowClick);
                const rowClassName = [
                  "ef-row",
                  isOutlier ? "ef-row--verify" : "",
                  isClickable ? "ef-row--clickable" : "",
                ]
                  .filter(Boolean)
                  .join(" ");

                return (
                  <tr
                    key={`${item.appointment_id ?? item.op}-${item.data_producao}-${index}`}
                    className={rowClassName}
                    onClick={isClickable ? () => onRowClick?.(item) : undefined}
                    onKeyDown={
                      isClickable
                        ? (event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              onRowClick?.(item);
                            }
                          }
                        : undefined
                    }
                    tabIndex={isClickable ? 0 : undefined}
                    role={isClickable ? "button" : undefined}
                    aria-label={
                      isClickable
                        ? `Ver detalhe do apontamento ${item.appointment_id}`
                        : undefined
                    }
                  >
                    <td data-label="Data">{formatDisplayDate(item.data_producao)}</td>
                    <td data-label="Início">{item.hora_inicio ?? "—"}</td>
                    <td data-label="Fim">{item.hora_final ?? "—"}</td>
                    <td data-label="Qtd. apontada">{formatNumber(item.qtd_apontada, 3)}</td>
                    <td data-label="Filial">{item.filial ?? "—"}</td>
                    <td data-label="OP">{item.op ?? "—"}</td>
                    <td data-label="Descrição produto">
                      {item.descricao_produto?.trim() || item.produto || "—"}
                    </td>
                    <td data-label="CT">{item.centro_trabalho ?? "—"}</td>
                    <td data-label="Operador">
                      {item.nome_operador ?? item.login_operador ?? "—"}
                    </td>
                    <td data-label="Eficiência">{formatPercent(item.eficiencia_percentual)}</td>
                    <td data-label="Resultado MOD">{formatCurrency(item.resultado_mod)}</td>
                    <td data-label="Status">
                      {isProductionEfficiencyOutlier(item.eficiencia_percentual) ? (
                        <span className="ef-badge ef-badge--danger">Verificar</span>
                      ) : (
                        <span className="ef-badge">{item.status_registro ?? "—"}</span>
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
