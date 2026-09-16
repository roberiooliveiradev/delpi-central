import { buildPurchaseOrderDetailPath } from "../../app/pluginRoutes";
import {
  SuppliesDataCardsGrid,
  SuppliesEntityLink,
  SuppliesStatusBadge,
} from "../../app/suppliesUi";
import { PURCHASE_ORDERS_CONTENT as C } from "./content";
import {
  formatDatePtBr,
  formatMoneyBr,
  formatProductLabel,
  formatQuantity,
  labelDeliveryStatus,
} from "./query";
import type { PurchaseOrderListItem } from "./types";

type PurchaseOrdersCardsProps = {
  items: PurchaseOrderListItem[];
  basePath: string;
  onSelectRow: (item: PurchaseOrderListItem) => void;
};

function statusBadgeVariant(
  status: string | null | undefined,
): "danger" | "success" | "neutral" {
  if (status === "late") return "danger";
  if (status === "on_time") return "success";
  return "neutral";
}

export function PurchaseOrdersCards({
  items,
  basePath,
  onSelectRow,
}: PurchaseOrdersCardsProps) {
  return (
    <SuppliesDataCardsGrid
      className="sp-purchase-orders__cards"
      ariaLabel={C.cardsAriaLabel}
    >
      {items.map((row) => {
        const href = buildPurchaseOrderDetailPath(row.branch, row.order_number, basePath);
        const label = row.order_number || "—";
        return (
          <article
            key={`${row.branch}-${row.order_number}-${row.order_item ?? ""}`}
            className="sp-purchase-orders__card"
          >
            <header className="sp-purchase-orders__card-header">
              <SuppliesEntityLink
                href={href}
                title={C.openPcLinkTitle(label)}
                className="sp-entity-link"
                onNavigate={() => onSelectRow(row)}
              >
                {label}
              </SuppliesEntityLink>
              <span>{row.order_item || "—"}</span>
            </header>
            <p className="sp-purchase-orders__card-product">
              {formatProductLabel(row.product_code, row.product_description)}
            </p>
            <p className="sp-purchase-orders__card-supplier">
              {row.supplier_name || row.supplier_code || "—"}
            </p>
            <dl className="sp-purchase-orders__card-meta">
              <div>
                <dt>{C.cardOpenQty}</dt>
                <dd>{formatQuantity(row.open_quantity)}</dd>
              </div>
              <div>
                <dt>{C.cardDelivery}</dt>
                <dd>{formatDatePtBr(row.expected_delivery_date)}</dd>
              </div>
              <div>
                <dt>{C.cardStatus}</dt>
                <dd>
                  <SuppliesStatusBadge
                    label={labelDeliveryStatus(row.delivery_status)}
                    variant={statusBadgeVariant(row.delivery_status)}
                  />
                </dd>
              </div>
              <div>
                <dt>{C.cardValue}</dt>
                <dd>{formatMoneyBr(row.open_value)}</dd>
              </div>
            </dl>
          </article>
        );
      })}
    </SuppliesDataCardsGrid>
  );
}
