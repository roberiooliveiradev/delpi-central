import { useMemo } from "react";

import { DataTable, type DataTableColumn } from "@delpi/plugin-ui/index";

import type { PurchaseRequestListItem } from "../types/purchaseRequests";
import { computeDaysOpen, formatDatePtBr } from "../utils/formatters";
import {
  formatForecastSummaryForLine,
  formatProductLabel,
  formatCostCenterLine,
  formatRequestNumber,
  labelApprovalStatus,
  labelDeliveryDeadlineForLine,
  labelOverallStage,
  labelReceiptSummaryForLine,
  listItemApprovalStatus,
  listItemIssueDate,
  listItemOrdersSummary,
  listItemOverallStage,
  listItemRequesterName,
  listItemSuppliersSummary,
  overallStageVariant,
  deliveryVariantForLine,
} from "../utils/labels";
import { PurchaseRequestsStatusBadge } from "../ui/purchaseRequestsUi";
import { TABLE, TABLE_LABELS, TABLE_SECTION } from "../ui/purchaseRequestsUiContracts";

type PurchaseRequestsTableProps = {
  items: PurchaseRequestListItem[];
  loading?: boolean;
  onSelect: (item: PurchaseRequestListItem) => void;
};

export function PurchaseRequestsTable({
  items,
  loading = false,
  onSelect,
}: PurchaseRequestsTableProps) {
  const columns = useMemo<DataTableColumn<PurchaseRequestListItem>[]>(
    () => [
      {
        key: "request_number",
        header: "SC",
        render: (item) => (
          <span className="pr-sc-number">{formatRequestNumber(item.request_number)}</span>
        ),
      },
      {
        key: "product",
        header: "Produto",
        render: (item) => (
          <span className="pr-product-cell">
            {formatProductLabel(item.product_code, item.product_description)}
          </span>
        ),
      },
      {
        key: "requester",
        header: "Solicitante",
        render: (item) => listItemRequesterName(item),
      },
      {
        key: "cost_center",
        header: "Centro de custo",
        render: (item) => formatCostCenterLine(item),
      },
      {
        key: "issue_date",
        header: "Abertura",
        render: (item) => formatDatePtBr(listItemIssueDate(item)),
      },
      {
        key: "days_open",
        header: "Dias em aberto",
        render: (item) => {
          const days = computeDaysOpen(listItemIssueDate(item), listItemOverallStage(item));
          return days == null ? "—" : String(days);
        },
      },
      {
        key: "overall_stage",
        header: "Situação",
        render: (item) => (
          <PurchaseRequestsStatusBadge
            label={labelOverallStage(listItemOverallStage(item))}
            variant={overallStageVariant(listItemOverallStage(item))}
          />
        ),
      },
      {
        key: "approval",
        header: "Aprovação",
        render: (item) => labelApprovalStatus(listItemApprovalStatus(item)),
      },
      {
        key: "orders",
        header: "Pedido(s)",
        render: (item) => listItemOrdersSummary(item),
      },
      {
        key: "suppliers",
        header: "Fornecedor(es)",
        render: (item) => listItemSuppliersSummary(item),
      },
      {
        key: "forecast",
        header: "Previsão",
        render: (item) => formatForecastSummaryForLine(item),
      },
      {
        key: "receipt",
        header: "Recebimento",
        render: (item) => labelReceiptSummaryForLine(item),
      },
      {
        key: "deadline",
        header: "Prazo",
        render: (item) => (
          <PurchaseRequestsStatusBadge
            label={labelDeliveryDeadlineForLine(item)}
            variant={deliveryVariantForLine(item)}
          />
        ),
      },
    ],
    [],
  );

  return (
    <div className={TABLE_SECTION.section}>
      <DataTable
        classNames={TABLE}
        labels={TABLE_LABELS}
        columns={columns}
        rows={items}
        loading={loading}
        rowKey={(item) => `${item.branch}:${item.request_number}:${item.request_item}`}
        onRowClick={onSelect}
      />
    </div>
  );
}
