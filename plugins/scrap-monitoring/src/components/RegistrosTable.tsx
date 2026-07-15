import { useCallback, useMemo, useState } from "react";

import { fetchAllScrapRegistros } from "../api/fetchAllScrapRegistros";
import { SCRAP_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ScrapQueryFilters, ScrapRegistroItem } from "../types/scrap";
import { exportRegistrosExcel } from "../utils/exportRegistros";
import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatQuantity,
} from "../utils/formatters";
import {
  DataTableSection,
  type DataTableColumn,
} from "./dataTableUi";
import { ExportExcelButton } from "./ExportExcelButton";

type RegistrosTableProps = {
  items: ScrapRegistroItem[];
  filters: ScrapQueryFilters;
  loading?: boolean;
  refreshing?: boolean;
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onRowClick: (item: ScrapRegistroItem) => void;
  onExportError?: (message: string) => void;
};

const T = SCRAP_HELP_TOOLTIPS.table;

export function RegistrosTable({
  items,
  filters,
  loading = false,
  refreshing = false,
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
  onRowClick,
  onExportError,
}: RegistrosTableProps) {
  const [exporting, setExporting] = useState(false);

  const columns = useMemo<DataTableColumn<ScrapRegistroItem>[]>(
    () => [
      {
        key: "data",
        header: "Data",
        headerHint: T.data,
        render: (row) => formatDatePtBr(row.dataPerda),
      },
      {
        key: "op",
        header: "OP",
        headerHint: T.op,
        render: (row) => row.op || "—",
      },
      {
        key: "pa",
        header: "PA",
        headerHint: T.pa,
        render: (row) => row.pa || "—",
      },
      {
        key: "mp",
        header: "MP",
        headerHint: T.mp,
        render: (row) => row.mp || "—",
      },
      {
        key: "descricao",
        header: "Descrição",
        headerHint: T.descricao,
        className: "sm-table__col--wide",
        render: (row) => {
          const text = row.descricao?.trim() || "—";
          return (
            <span className="sm-table__cell-ellipsis" title={text === "—" ? undefined : text}>
              {text}
            </span>
          );
        },
      },
      {
        key: "motivo",
        header: "Motivo",
        headerHint: T.motivo,
        render: (row) => row.motivo || row.motivoCodigo || "—",
      },
      {
        key: "ct",
        header: "CT",
        headerHint: T.ct,
        render: (row) => row.centroTrabalho || "—",
      },
      {
        key: "colaborador",
        header: "Colaborador",
        headerHint: T.colaborador,
        render: (row) => {
          const text = row.nomeOperador || row.codigoOperador || "—";
          return (
            <span className="sm-table__cell-ellipsis" title={text === "—" ? undefined : text}>
              {text}
            </span>
          );
        },
      },
      {
        key: "qtd",
        header: "Qtd",
        headerHint: T.qtd,
        className: "sm-table__col--numeric",
        render: (row) =>
          `${formatQuantity(row.quantidade)}${row.um ? ` ${row.um}` : ""}`,
      },
      {
        key: "valor",
        header: "Valor",
        headerHint: T.valor,
        className: "sm-table__col--numeric",
        render: (row) => formatCurrencyBrl(row.valor),
      },
    ],
    [],
  );

  const handleExportExcel = useCallback(async () => {
    if (exporting || total <= 0) return;
    setExporting(true);
    try {
      const allItems = await fetchAllScrapRegistros(filters);
      await exportRegistrosExcel(allItems, filters);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Não foi possível exportar o Excel.";
      onExportError?.(message);
    } finally {
      setExporting(false);
    }
  }, [exporting, filters, onExportError, total]);

  return (
    <DataTableSection
      title="Registros de refugo"
      titleHint={T.section}
      hint={`${total.toLocaleString("pt-BR")} registro(s) no período`}
      columns={columns}
      rows={items}
      rowKey={(row) =>
        `${row.dataPerda}|${row.op}|${row.mp}|${row.motivoCodigo}|${row.centroTrabalho}|${row.codigoOperador}|${row.quantidade}|${row.valor}`
      }
      onRowClick={onRowClick}
      loading={loading && items.length === 0}
      refreshing={refreshing || (loading && items.length > 0)}
      hideSearch
      serverPagination={{
        page,
        pageSize,
        total,
        onPageChange,
        onPageSizeChange,
      }}
      emptyMessage="Nenhum registro no período."
      headerActions={
        <ExportExcelButton
          disabled={loading || total <= 0}
          exporting={exporting}
          onExport={handleExportExcel}
        />
      }
    />
  );
}
