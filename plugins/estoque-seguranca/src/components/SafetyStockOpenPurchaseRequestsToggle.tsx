import { useEffect, useId, useState } from "react";

import type { SafetyStockOpenPurchaseRequest } from "../types/safetyStock";
import { formatNumberPtBr } from "../utils/formatters";
import { formatIsoDatePtBr } from "../utils/safetyStockStatus";
import { DataTable, type DataTableColumn } from "./dataTableUi";

type SafetyStockOpenPurchaseRequestsToggleProps = {
  requests: SafetyStockOpenPurchaseRequest[];
};

const requestColumns: DataTableColumn<SafetyStockOpenPurchaseRequest>[] = [
  {
    key: "request_number",
    header: "Solicitação",
    render: (row) =>
      `${row.request_number}/${row.request_item}`.replace(/\/$/, ""),
  },
  {
    key: "required_date",
    header: "Necessidade",
    render: (row) => formatIsoDatePtBr(row.required_date),
  },
  {
    key: "supplier_name",
    header: "Fornecedor",
    className: "ess-table__col--secondary",
    render: (row) => row.supplier_name || row.supplier_code || "—",
  },
  {
    key: "open_quantity",
    header: "Saldo",
    align: "right",
    className: "ess-table__col--numeric",
    render: (row) =>
      formatNumberPtBr(row.open_quantity_primary_unit ?? row.open_quantity),
  },
  {
    key: "purchase_order_number",
    header: "PC gerado",
    render: (row) => row.purchase_order_number?.trim() || "—",
  },
  {
    key: "unit",
    header: "UM",
    render: (row) => row.unit || "—",
  },
];

export function SafetyStockOpenPurchaseRequestsToggle({
  requests,
}: SafetyStockOpenPurchaseRequestsToggleProps) {
  const panelId = useId();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setOpen(false);
  }, [requests]);

  if (requests.length === 0) {
    return null;
  }

  return (
    <div className="ess-detail__purchase-toggles">
      <div className="ess-detail__purchase-toggle">
        <button
          type="button"
          className="ess-btn ess-btn--secondary ess-calc-toggle"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => setOpen((current) => !current)}
        >
          {open
            ? "Ocultar solicitações de compra"
            : `Ver solicitações de compra (${requests.length})`}
        </button>
        {open ? (
          <div
            id={panelId}
            className="ess-detail__purchase-panel"
            role="region"
            aria-label="Solicitações de compra em aberto"
          >
            <p className="ess-detail__hint">
              Solicitações com saldo em aberto no Protheus (SC1). Não entram na
              projeção de saldo — só o pedido de compra (SC7) gera entrada
              prevista.
            </p>
            <DataTable
              columns={requestColumns}
              rows={requests}
              rowKey={(row) =>
                `${row.branch}-${row.request_number}-${row.request_item}`
              }
              layout="embedded"
              emptyMessage="Nenhuma solicitação em aberto."
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}
