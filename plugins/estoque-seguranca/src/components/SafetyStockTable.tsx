import { useMemo } from "react";
import { createDashboardStatusBadge } from "@delpi/plugin-ui/index";

import type { SafetyStockItem } from "../types/safetyStock";
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
        interactive: true,
        render: () => <SafetyStockDetailsActionHint />,
      },
    ],
    [],
  );

  const totalPages = Math.max(1, Math.ceil(total / pageSize) || 1);

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
