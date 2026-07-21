import { useMemo, useState } from "react";
import {
  createDashboardStatusBadge,
  ExcelExportButton,
} from "@delpi/plugin-ui/index";

import type { SafetyStockItem, SafetyStockQueryParams } from "../types/safetyStock";
import { exportSafetyStockExcel } from "../utils/exportSafetyStockExcel";
import { computeDisplayBalance, computeDisplayDeficit, formatNumberPtBr } from "../utils/formatters";
import {
  safetyStockStatusLabel,
  safetyStockStatusVariant,
} from "../utils/safetyStockStatus";
import {
  DataTableSection,
  type DataTableColumn,
} from "./dataTableUi";
import { SafetyStockDetailsActionHint } from "./SafetyStockDetailModal";

const StatusBadge = createDashboardStatusBadge({ prefix: "ess" });

type SafetyStockTableProps = {
  items: SafetyStockItem[];
  exportParams: SafetyStockQueryParams | null;
  loading?: boolean;
  refreshing?: boolean;
  page: number;
  pageSize: number;
  total: number;
  emptyMessage?: string;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onRowClick?: (item: SafetyStockItem) => void;
};

export function SafetyStockTable({
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
}: SafetyStockTableProps) {
  const [exporting, setExporting] = useState(false);

  const columns = useMemo<DataTableColumn<SafetyStockItem>[]>(
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
        header: "Unidade",
        render: (row) => row.unit || "—",
      },
      {
        key: "product_group",
        header: "Grupo",
        className: "ess-table__col--secondary",
        render: (row) => row.product_group || "—",
      },
      {
        key: "safety_stock",
        header: "Est. segurança",
        className: "ess-table__col--numeric",
        render: (row) => formatNumberPtBr(row.safety_stock),
      },
      {
        key: "display_balance",
        header: "Saldo",
        headerHint: "Soma dos armazéns 01, 98 e 99",
        className: "ess-table__col--numeric ess-table__col--primary",
        render: (row) => formatNumberPtBr(computeDisplayBalance(row)),
      },
      {
        key: "deficit_quantity",
        header: "Déficit",
        className: "ess-table__col--numeric",
        render: (row) => formatNumberPtBr(computeDisplayDeficit(row)),
      },
      {
        key: "status",
        header: "Situação",
        render: (row) => (
          <StatusBadge
            label={safetyStockStatusLabel(row.status)}
            variant={safetyStockStatusVariant(row.status)}
          />
        ),
      },
      {
        key: "actions",
        header: "Detalhes",
        className: "ess-table__col--action",
        render: () => <SafetyStockDetailsActionHint />,
      },
    ],
    [],
  );

  const totalPages = Math.max(1, Math.ceil(total / pageSize) || 1);

  const handleExportExcel = async () => {
    if (!exportParams) return;
    setExporting(true);
    try {
      await exportSafetyStockExcel(exportParams);
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
      title="Matérias-primas"
      hint={`${total.toLocaleString("pt-BR")} registro(s) · Página ${page} de ${totalPages}`}
      columns={columns}
      rows={items}
      rowKey={(row) => `${row.branch}-${row.product_code}`}
      loading={loading && items.length === 0}
      refreshing={refreshing || (loading && items.length > 0)}
      emptyMessage={emptyMessage}
      hideSearch
      columnPreferencesKey="estoque-seguranca:items:v3"
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
