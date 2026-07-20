import { useMemo, useState } from "react";
import {
  createDashboardStatusBadge,
  ExcelExportButton,
} from "@delpi/plugin-ui/index";

import type {
  ConsumptionAnalysisItem,
  ConsumptionAnalysisQueryParams,
} from "../types/consumptionAnalysis";
import { exportConsumptionAnalysisExcel } from "../utils/exportConsumptionAnalysisExcel";
import { formatNumberPtBr } from "../utils/formatters";
import {
  ANALYSIS_STATUS_HEADER_HINT,
  analysisStatusLabel,
  analysisStatusVariant,
} from "../utils/safetyStockStatus";
import { DataTableSection, type DataTableColumn } from "./dataTableUi";

const StatusBadge = createDashboardStatusBadge({ prefix: "ess" });

type ConsumptionAnalysisTableProps = {
  items: ConsumptionAnalysisItem[];
  exportParams: ConsumptionAnalysisQueryParams | null;
  loading?: boolean;
  refreshing?: boolean;
  page: number;
  pageSize: number;
  total: number;
  emptyMessage?: string;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onRowClick?: (item: ConsumptionAnalysisItem) => void;
};

function formatOptional(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return formatNumberPtBr(value);
}

export function ConsumptionAnalysisTable({
  items,
  exportParams,
  loading = false,
  refreshing = false,
  page,
  pageSize,
  total,
  emptyMessage,
  onPageChange,
  onPageSizeChange,
  onRowClick,
}: ConsumptionAnalysisTableProps) {
  const [exporting, setExporting] = useState(false);

  const columns = useMemo<DataTableColumn<ConsumptionAnalysisItem>[]>(
    () => [
      {
        key: "product_code",
        header: "Código",
        className: "ess-table__col--code",
        render: (row) => row.product_code,
      },
      {
        key: "product_description",
        header: "Descrição",
        className: "ess-table__col--description",
        render: (row) => {
          const text = row.product_description?.trim() || "—";
          return (
            <span className="ess-table__cell-ellipsis" title={text === "—" ? undefined : text}>
              {text}
            </span>
          );
        },
      },
      {
        key: "unit",
        header: "UM",
        render: (row) => row.unit || "—",
      },
      {
        key: "safety_stock",
        header: "ESTSEG atual",
        className: "ess-table__col--numeric",
        render: (row) => formatNumberPtBr(row.safety_stock),
      },
      {
        key: "suggested_safety_stock",
        header: "Sugerido",
        headerHint: "Consumo diário × dias úteis do lead time",
        className: "ess-table__col--numeric ess-table__col--primary",
        render: (row) => formatNumberPtBr(row.suggested_safety_stock),
      },
      {
        key: "difference_quantity",
        header: "Diferença",
        className: "ess-table__col--numeric",
        render: (row) => formatNumberPtBr(row.difference_quantity),
      },
      {
        key: "average_daily_consumption",
        header: "Consumo diário",
        headerHint: "Média das baixas por dia útil nos últimos 12 meses",
        className: "ess-table__col--numeric",
        render: (row) => formatNumberPtBr(row.average_daily_consumption),
      },
      {
        key: "lead_time_days",
        header: "Lead time",
        headerHint: "BZ_PE em dias corridos",
        className: "ess-table__col--numeric",
        render: (row) => formatNumberPtBr(row.lead_time_days, 0),
      },
      {
        key: "coverage_business_days",
        header: "Cobertura",
        headerHint: "Saldo disponível ÷ consumo diário",
        className: "ess-table__col--numeric",
        render: (row) => formatOptional(row.coverage_business_days),
      },
      {
        key: "analysis_status",
        header: "Situação",
        headerHint: ANALYSIS_STATUS_HEADER_HINT,
        render: (row) => (
          <StatusBadge
            label={analysisStatusLabel(row.analysis_status)}
            variant={analysisStatusVariant(row.analysis_status)}
          />
        ),
      },
    ],
    [],
  );

  const totalPages = Math.max(1, Math.ceil(total / pageSize) || 1);

  const handleExportExcel = async () => {
    if (!exportParams) return;
    setExporting(true);
    try {
      await exportConsumptionAnalysisExcel(exportParams);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Não foi possível exportar o Excel. Tente novamente.";
      window.alert(message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <DataTableSection
      title="Simulação do estoque de segurança"
      hint={`${total.toLocaleString("pt-BR")} registro(s) · Página ${page} de ${totalPages} · somente leitura`}
      columns={columns}
      rows={items}
      rowKey={(row) => `${row.branch}-${row.product_code}`}
      loading={loading && items.length === 0}
      refreshing={refreshing || (loading && items.length > 0)}
      emptyMessage={
        emptyMessage ??
        "Nenhum produto com estoque de segurança e movimentos elegíveis para os filtros."
      }
      hideSearch
      columnPreferencesKey="estoque-seguranca:consumption-analysis:v2"
      onRowClick={onRowClick}
      headerActions={
        <ExcelExportButton
          className="ess-export-actions"
          buttonClassName="ess-btn ess-btn--secondary ess-export-actions__btn"
          disabled={!exportParams || total === 0 || loading}
          exporting={exporting}
          onExport={handleExportExcel}
          label="Excel"
          exportingLabel="Exportando…"
        />
      }
      serverPagination={{
        page,
        pageSize,
        total,
        onPageChange,
        onPageSizeChange,
      }}
    />
  );
}
