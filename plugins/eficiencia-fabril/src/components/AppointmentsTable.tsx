import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { useCallback, useMemo, useState, type ReactNode } from "react";
import {
  createTablePaginationNav,
  dataTableBemClasses,
  DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS,
  HelpTooltip,
  TableColumnVisibilityMenu,
  useTableColumnVisibility,
} from "@delpi/plugin-ui/index";
import { resolveEficienciaFabrilAppointmentStatus } from "../utils/appointmentStatus";
import { EF_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";
import type { AppointmentsSortColumn, SortDirection } from "../utils/appointmentsTableSort";
import {
  APPOINTMENT_COLUMN_EMPTY_FALLBACK,
  APPOINTMENT_COLUMN_STORAGE_KEY,
  APPOINTMENT_COLUMN_VISIBILITY_ITEMS,
  APPOINTMENT_TABLE_COLUMNS,
  appointmentDisplayCell,
} from "../utils/appointmentsTableColumns";
import { exportAppointmentsExcel, exportAppointmentsPdf } from "../utils/exportAppointments";
import { ExportActions } from "./ExportActions";

const EF_TABLE = dataTableBemClasses("ef");

const AppointmentsPaginationNav = createTablePaginationNav({
  prefix: "ef",
  labels: {
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação de apontamentos",
    infoBeforeCurrent: "Página ",
    infoAfterCurrent: (totalPages) => ` de ${totalPages}`,
  },
});

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
    return <ArrowUpDown size={14} className={EF_TABLE.sortIndicator} aria-hidden />;
  }

  return sortDir === "asc" ? (
    <ArrowUp size={14} className={EF_TABLE.sortIndicator} aria-hidden />
  ) : (
    <ArrowDown size={14} className={EF_TABLE.sortIndicator} aria-hidden />
  );
}

function renderStatusCell(item: EficienciaFabrilItem): ReactNode {
  const statusKind = resolveEficienciaFabrilAppointmentStatus(item);
  if (statusKind === "verify") {
    return <span className="ef-badge ef-badge--danger">Verificar</span>;
  }
  if (statusKind === "low") {
    return <span className="ef-badge ef-badge--warning">Eficiência baixa</span>;
  }
  return <span className="ef-badge">{item.status_registro ?? "—"}</span>;
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

  const {
    visibility,
    visibleColumnCount,
    setColumnVisible,
    reset: resetColumnVisibility,
    filterColumns,
  } = useTableColumnVisibility({
    storageKey: APPOINTMENT_COLUMN_STORAGE_KEY,
    columns: APPOINTMENT_COLUMN_VISIBILITY_ITEMS,
    emptyFallbackKeys: APPOINTMENT_COLUMN_EMPTY_FALLBACK,
  });

  const visibleColumns = useMemo(
    () => filterColumns(APPOINTMENT_TABLE_COLUMNS),
    [filterColumns]
  );

  const visibleColumnIds = useMemo(
    () => visibleColumns.map((column) => column.key),
    [visibleColumns]
  );

  /** TablePaginationNav deriva totalPages de total/pageSize — reconstituir size estável. */
  const pageSize = useMemo(() => {
    if (totalPages <= 0) return Math.max(items.length, 1);
    return Math.max(1, Math.ceil(total / Math.max(totalPages, 1)));
  }, [items.length, total, totalPages]);

  const handleExportExcel = useCallback(async () => {
    if (exporting || total <= 0) return;

    setExporting(true);
    try {
      await exportAppointmentsExcel(
        exportItems,
        exportDateStart,
        exportDateEnd,
        visibleColumnIds
      );
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Não foi possível exportar o Excel.";
      onExportError?.(message);
    } finally {
      setExporting(false);
    }
  }, [
    exportDateEnd,
    exportDateStart,
    exportItems,
    exporting,
    onExportError,
    total,
    visibleColumnIds,
  ]);

  const handleExportPdf = useCallback(async () => {
    if (exporting || total <= 0) return;

    setExporting(true);
    try {
      await exportAppointmentsPdf(
        exportItems,
        exportDateStart,
        exportDateEnd,
        visibleColumnIds
      );
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Não foi possível exportar o PDF.";
      onExportError?.(message);
    } finally {
      setExporting(false);
    }
  }, [
    exportDateEnd,
    exportDateStart,
    exportItems,
    exporting,
    onExportError,
    total,
    visibleColumnIds,
  ]);

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
          <TableColumnVisibilityMenu
            columns={APPOINTMENT_COLUMN_VISIBILITY_ITEMS}
            visibility={visibility}
            onToggleColumn={setColumnVisible}
            onReset={resetColumnVisibility}
            labels={DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS}
            className="ef-table-columns"
          />
          <AppointmentsPaginationNav
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={onPageChange}
          />
        </div>
      </header>

      <div className={EF_TABLE.wrap}>
        <table className={EF_TABLE.sortableTable ?? EF_TABLE.table}>
          <thead>
            <tr>
              {visibleColumns.map((column) => {
                const isActive = sortBy === column.key;
                return (
                  <th
                    key={column.key}
                    scope="col"
                    aria-sort={
                      isActive ? (sortDir === "asc" ? "ascending" : "descending") : "none"
                    }
                  >
                    <button
                      type="button"
                      className={isActive ? EF_TABLE.sortButtonActive : EF_TABLE.sortButton}
                      disabled={disabled}
                      onClick={() => onSortChange(column.key)}
                    >
                      <span className={EF_TABLE.headerLabel}>
                        <span className={EF_TABLE.headerText}>{column.label}</span>
                        {column.hint ? (
                          <HelpTooltip
                            content={column.hint}
                            ariaLabel={`Ajuda: ${column.label}`}
                            className={EF_TABLE.headerHelp}
                          />
                        ) : null}
                      </span>
                      <SortIndicator column={column.key} sortBy={sortBy} sortDir={sortDir} />
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={Math.max(visibleColumnCount, 1)} className={EF_TABLE.empty}>
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
                    {visibleColumns.map((column) => (
                      <td key={column.key} data-label={column.label}>
                        {column.key === "status"
                          ? renderStatusCell(item)
                          : appointmentDisplayCell(item, column.key)}
                      </td>
                    ))}
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
