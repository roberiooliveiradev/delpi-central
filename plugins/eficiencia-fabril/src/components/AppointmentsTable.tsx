import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { useCallback, useState } from "react";

import { resolveEficienciaFabrilAppointmentStatus } from "../utils/appointmentStatus";
import { EF_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";
import { HelpTooltip } from "./HelpTooltip";
import type { AppointmentsSortColumn, SortDirection } from "../utils/appointmentsTableSort";
import { formatDisplayDate } from "../utils/dates";
import { exportAppointmentsExcel, exportAppointmentsPdf } from "../utils/exportAppointments";
import { ExportActions } from "./ExportActions";
import { formatCurrency, formatPercent, formatProductionQuantity } from "../utils/format";

type SortableColumn = {
  id: AppointmentsSortColumn;
  label: string;
  hint?: string;
};

const SORTABLE_COLUMNS: SortableColumn[] = [
  { id: "data_producao", label: "Data", hint: EF_HELP_TOOLTIPS.table.dataProducao },
  { id: "hora_inicio", label: "Início", hint: EF_HELP_TOOLTIPS.table.horaInicio },
  { id: "hora_final", label: "Fim", hint: EF_HELP_TOOLTIPS.table.horaFinal },
  { id: "qtd_apontada", label: "Qtd. apontada", hint: EF_HELP_TOOLTIPS.table.qtdApontada },
  { id: "filial", label: "Filial", hint: EF_HELP_TOOLTIPS.table.filial },
  { id: "op", label: "OP", hint: EF_HELP_TOOLTIPS.table.op },
  { id: "descricao_produto", label: "Descrição produto", hint: EF_HELP_TOOLTIPS.table.descricaoProduto },
  { id: "centro_trabalho", label: "CT", hint: EF_HELP_TOOLTIPS.table.centroTrabalho },
  { id: "operador", label: "Operador", hint: EF_HELP_TOOLTIPS.table.operador },
  {
    id: "eficiencia_percentual",
    label: "Eficiência",
    hint: EF_HELP_TOOLTIPS.table.eficienciaPercentual,
  },
  { id: "resultado_mod", label: "Resultado MOD", hint: EF_HELP_TOOLTIPS.table.resultadoMod },
  { id: "status", label: "Status", hint: EF_HELP_TOOLTIPS.table.status },
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

  const handleExportPdf = useCallback(async () => {
    if (exporting || total <= 0) return;

    setExporting(true);
    try {
      await exportAppointmentsPdf(exportItems, exportDateStart, exportDateEnd);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Não foi possível exportar o PDF.";
      onExportError?.(message);
    } finally {
      setExporting(false);
    }
  }, [exportDateEnd, exportDateStart, exportItems, exporting, onExportError, total]);

  return (
    <section className="ef-table-card" aria-label="Apontamentos">
      <header className="ef-table-card__header">
        <div>
          <h2>
            Apontamentos
            <HelpTooltip
              content={EF_HELP_TOOLTIPS.table.section}
              ariaLabel="Ajuda: Apontamentos"
              className="ef-table-card__title-help"
            />
          </h2>
          <p>{total.toLocaleString("pt-BR")} registro(s) no período</p>
        </div>
        <div className="ef-table-card__actions">
          <ExportActions
            disabled={disabled || total <= 0}
            exporting={exporting}
            onExportExcel={handleExportExcel}
            onExportPdf={handleExportPdf}
            excelLabel="Excel"
          />
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
        <table className="ef-table ef-table--sortable">
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
                      <span className="ef-sortable-th__label">
                        <span>{column.label}</span>
                        {column.hint ? (
                          <HelpTooltip
                            content={column.hint}
                            ariaLabel={`Ajuda: ${column.label}`}
                          />
                        ) : null}
                      </span>
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
                const statusKind = resolveEficienciaFabrilAppointmentStatus(item);
                const isClickable = Boolean(item.appointment_id) && Boolean(onRowClick);
                const rowClassName = [
                  "ef-row",
                  statusKind === "verify" ? "ef-row--verify" : "",
                  statusKind === "low" ? "ef-row--low-efficiency" : "",
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
                    <td data-label="Qtd. apontada">
                      {formatProductionQuantity(item.qtd_apontada, item.unidade)}
                    </td>
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
                      {statusKind === "verify" ? (
                        <span className="ef-badge ef-badge--danger">Verificar</span>
                      ) : statusKind === "low" ? (
                        <span className="ef-badge ef-badge--warning">Eficiência baixa</span>
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
