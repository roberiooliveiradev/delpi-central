import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import {
  createTablePaginationNav,
  dataTableBemClasses,
  HelpTooltip,
} from "@delpi/plugin-ui/index";

import { fetchAllUnproductiveHoursItems } from "../api/unproductiveHoursApi";
import { EF_HELP_TOOLTIPS } from "../content/helpTooltips";
import type {
  UnproductiveHoursItem,
  UnproductiveHoursQueryFilters,
  UnproductiveHoursSort,
} from "../types/unproductiveHours";
import { resolveItemCost, resolveItemHours } from "../types/unproductiveHours";
import { formatDisplayDate } from "../utils/dates";
import {
  exportUnproductiveHoursExcel,
  exportUnproductiveHoursPdf,
} from "../utils/exportUnproductiveHours";
import { formatCurrency, formatHours } from "../utils/format";
import { ExportActions } from "./ExportActions";

const EF_TABLE = dataTableBemClasses("ef");

const PaginationNav = createTablePaginationNav({
  prefix: "ef",
  labels: {
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação de horas improdutivas",
    infoBeforeCurrent: "Página ",
    infoAfterCurrent: (totalPages) => ` de ${totalPages}`,
  },
});

type SortColumn = "date" | "hours" | "cost";

type UnproductiveHoursTableProps = {
  items: UnproductiveHoursItem[];
  filters: UnproductiveHoursQueryFilters;
  page: number;
  totalPages: number;
  total: number;
  sort: UnproductiveHoursSort;
  onSortChange: (sort: UnproductiveHoursSort) => void;
  onPageChange: (page: number) => void;
  onExportError?: (message: string) => void;
  disabled?: boolean;
};

function sortColumnFromApi(sort: UnproductiveHoursSort): SortColumn {
  if (sort.startsWith("hours")) return "hours";
  if (sort.startsWith("cost")) return "cost";
  return "date";
}

function sortDirFromApi(sort: UnproductiveHoursSort): "asc" | "desc" {
  return sort.endsWith("_asc") ? "asc" : "desc";
}

function nextSort(column: SortColumn, current: UnproductiveHoursSort): UnproductiveHoursSort {
  const currentColumn = sortColumnFromApi(current);
  const currentDir = sortDirFromApi(current);
  const nextDir = currentColumn === column && currentDir === "desc" ? "asc" : "desc";
  if (column === "hours") return nextDir === "asc" ? "hours_asc" : "hours_desc";
  if (column === "cost") return nextDir === "asc" ? "cost_asc" : "cost_desc";
  return nextDir === "asc" ? "date_asc" : "date_desc";
}

function SortIndicator({
  column,
  sort,
}: {
  column: SortColumn;
  sort: UnproductiveHoursSort;
}) {
  if (sortColumnFromApi(sort) !== column) {
    return <ArrowUpDown size={14} className={EF_TABLE.sortIndicator} aria-hidden />;
  }
  return sortDirFromApi(sort) === "asc" ? (
    <ArrowUp size={14} className={EF_TABLE.sortIndicator} aria-hidden />
  ) : (
    <ArrowDown size={14} className={EF_TABLE.sortIndicator} aria-hidden />
  );
}

function motivoCell(item: UnproductiveHoursItem): string {
  const code = (item.stop_reason ?? item.motivo ?? "").trim();
  const description = (item.stop_reason_description ?? item.motivoDescricao ?? "").trim();
  if (code && description) return `${code} — ${description}`;
  return code || description || "—";
}

function SortableHeader({
  label,
  column,
  sort,
  disabled,
  onSortChange,
}: {
  label: string;
  column: SortColumn;
  sort: UnproductiveHoursSort;
  disabled: boolean;
  onSortChange: (sort: UnproductiveHoursSort) => void;
}) {
  const isActive = sortColumnFromApi(sort) === column;
  return (
    <th
      scope="col"
      aria-sort={isActive ? (sortDirFromApi(sort) === "asc" ? "ascending" : "descending") : "none"}
    >
      <button
        type="button"
        className={isActive ? EF_TABLE.sortButtonActive : EF_TABLE.sortButton}
        disabled={disabled}
        onClick={() => onSortChange(nextSort(column, sort))}
      >
        <span className={EF_TABLE.headerLabel}>
          <span className={EF_TABLE.headerText}>{label}</span>
        </span>
        <SortIndicator column={column} sort={sort} />
      </button>
    </th>
  );
}

export function UnproductiveHoursTable({
  items,
  filters,
  page,
  totalPages,
  total,
  sort,
  onSortChange,
  onPageChange,
  onExportError,
  disabled = false,
}: UnproductiveHoursTableProps) {
  const [exporting, setExporting] = useState(false);

  const pageSize = useMemo(() => {
    if (totalPages <= 0) return Math.max(items.length, 1);
    return Math.max(1, Math.ceil(total / Math.max(totalPages, 1)));
  }, [items.length, total, totalPages]);

  const handleExport = useCallback(
    async (kind: "excel" | "pdf") => {
      if (exporting || total <= 0) return;
      setExporting(true);
      try {
        const allItems = await fetchAllUnproductiveHoursItems(filters);
        if (kind === "excel") {
          await exportUnproductiveHoursExcel(allItems, filters);
        } else {
          await exportUnproductiveHoursPdf(allItems, filters);
        }
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Não foi possível exportar os apontamentos.";
        onExportError?.(message);
      } finally {
        setExporting(false);
      }
    },
    [exporting, filters, onExportError, total],
  );

  return (
    <section className="ef-table-card" aria-label="Apontamentos de horas improdutivas">
      <header className="ef-table-card__header">
        <div>
          <h2>
            Apontamentos de parada
            <HelpTooltip
              content={EF_HELP_TOOLTIPS.unproductiveHours.table.section}
              ariaLabel="Ajuda: apontamentos de parada"
              className="ef-table-card__title-help"
            />
          </h2>
          <p>{total.toLocaleString("pt-BR")} registro(s) no período</p>
        </div>
        <div className="ef-table-card__actions">
          <ExportActions
            disabled={disabled || total <= 0}
            exporting={exporting}
            onExportExcel={() => void handleExport("excel")}
            onExportPdf={() => void handleExport("pdf")}
          />
          <PaginationNav
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
              <SortableHeader
                label="Data"
                column="date"
                sort={sort}
                disabled={disabled}
                onSortChange={onSortChange}
              />
              <th scope="col">Recurso</th>
              <th scope="col">CT custo</th>
              <th scope="col">Operador</th>
              <th scope="col">Motivo</th>
              <SortableHeader
                label="Horas"
                column="hours"
                sort={sort}
                disabled={disabled}
                onSortChange={onSortChange}
              />
              <SortableHeader
                label="Valor"
                column="cost"
                sort={sort}
                disabled={disabled}
                onSortChange={onSortChange}
              />
              <th scope="col">Observação</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={8} className={EF_TABLE.empty}>
                  Nenhum apontamento de parada para os filtros selecionados.
                </td>
              </tr>
            ) : (
              items.map((item, index) => {
                const key = String(
                  item.recno ?? `${item.reference_date ?? item.dataReferencia}-${index}`,
                );
                return (
                  <tr key={key} className="ef-row">
                    <td>{formatDisplayDate(item.reference_date ?? item.dataReferencia)}</td>
                    <td>{item.resource ?? item.recurso ?? "—"}</td>
                    <td>{item.cost_center ?? item.centroCusto ?? "—"}</td>
                    <td>{item.operator_name ?? item.nomeOperador ?? "—"}</td>
                    <td>{motivoCell(item)}</td>
                    <td className={EF_TABLE.colNumeric}>{formatHours(resolveItemHours(item))}</td>
                    <td className={EF_TABLE.colNumeric}>{formatCurrency(resolveItemCost(item))}</td>
                    <td>{item.observation ?? item.observacao ?? "—"}</td>
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
