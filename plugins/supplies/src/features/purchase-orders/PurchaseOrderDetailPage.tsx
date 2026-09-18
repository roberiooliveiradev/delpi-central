import { useEffect, useState } from "react";

import { navigatePluginView } from "../../app/pluginNavigation";
import {
  SuppliesPersonIdentity,
  SuppliesSupplierIdentity,
} from "../../app/SuppliesDirectoryIdentity";
import { buildPluginPath } from "../../app/pluginRoutes";
import { formatSuppliesUnitLabel } from "../../app/suppliesUnits";
import {
  SuppliesActionButton,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesSectionHintLabel,
  SuppliesStateBanner,
  SuppliesStatusBadge,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { getPurchaseOrder } from "./api";
import {
  classifyPurchaseOrderDetailError,
  PURCHASE_ORDERS_CONTENT as C,
} from "./content";
import {
  formatDatePtBr,
  formatMoneyBr,
  formatProductLabel,
  formatQuantity,
  labelDeliveryStatus,
} from "./query";
import type { PurchaseOrderDetail, PurchaseOrderDetailItem, PurchaseOrderReceipt } from "./types";

type PurchaseOrderDetailPageProps = {
  basePath: string;
  branch: string;
  orderNumber: string;
};

function statusBadgeVariant(
  status: string | null | undefined,
): "danger" | "success" | "neutral" {
  if (status === "late") return "danger";
  if (status === "on_time") return "success";
  return "neutral";
}

function sourceRequestLabel(item: PurchaseOrderDetailItem): string {
  const number = (item.source_request_number || "").trim();
  const line = (item.source_request_item || "").trim();
  if (number && line) return `${number} / ${line}`;
  return number || "—";
}

function invoiceLabel(receipt: PurchaseOrderReceipt): string {
  const number = (receipt.invoice_number || "").trim();
  const series = (receipt.invoice_series || "").trim();
  if (number && series) return `${number}-${series}`;
  return number || "—";
}

export function PurchaseOrderDetailPage({
  basePath,
  branch,
  orderNumber,
}: PurchaseOrderDetailPageProps) {
  const listHref = buildPluginPath("purchase_orders", basePath);
  const [loading, setLoading] = useState(true);
  const [errorKind, setErrorKind] = useState<"forbidden" | "not_found" | "error" | null>(
    null,
  );
  const [errorText, setErrorText] = useState<string | null>(null);
  const [detail, setDetail] = useState<PurchaseOrderDetail | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!branch || !orderNumber) return;
    const controller = new AbortController();
    setLoading(true);
    setErrorKind(null);
    setErrorText(null);
    getPurchaseOrder(branch, orderNumber, controller.signal)
      .then((payload) => {
        setDetail(payload);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setDetail(null);
        const message = err instanceof Error ? err.message : C.detailError;
        const classified = classifyPurchaseOrderDetailError(message);
        setErrorKind(classified.kind);
        setErrorText(classified.text);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, orderNumber, reloadKey]);

  const items = detail?.items ?? [];

  return (
    <div className="sp-page-stack sp-purchase-order-detail">
      <SuppliesPagePath
        back={{
          label: C.detailBack,
          href: listHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("purchase_orders", { basePath });
          },
        }}
        items={[]}
        current={`${C.detailTitle} ${orderNumber}`}
      />

      <SuppliesPageHero
        eyebrow={C.detailEyebrow}
        title={
          <SuppliesSectionHintLabel
            label={`${C.detailTitle} ${orderNumber}`}
            hint={SP_HELP.purchaseOrderDetail}
          />
        }
        description={C.detailDescription}
        aria-label={C.detailTitle}
      >
        <dl className="sp-purchase-order-detail__identity">
          <div>
            <dt>Filial</dt>
            <dd>{formatSuppliesUnitLabel(detail?.branch || branch)}</dd>
          </div>
          <div>
            <dt>Pedido</dt>
            <dd>{detail?.order_number || orderNumber}</dd>
          </div>
        </dl>
      </SuppliesPageHero>

      {errorKind === "forbidden" ? (
        <div className="sp-purchase-order-detail__error">
          <SuppliesStateBanner variant="error">{errorText}</SuppliesStateBanner>
        </div>
      ) : null}

      {errorKind === "not_found" ? (
        <SuppliesEmptyState title={C.detailTitle} message={errorText || C.detailNotFound} />
      ) : null}

      {errorKind === "error" ? (
        <div className="sp-purchase-order-detail__error">
          <SuppliesStateBanner variant="error">{errorText}</SuppliesStateBanner>
          <SuppliesActionButton
            type="button"
            variant="primary"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            {C.retry}
          </SuppliesActionButton>
        </div>
      ) : null}

      {loading ? <SuppliesLoadingCard title={C.detailLoading} variant="panel" /> : null}

      {!loading && !errorKind && items.length === 0 ? (
        <SuppliesEmptyState title={C.itemsTitle} message={C.itemsEmpty} />
      ) : null}

      {!loading && !errorKind && items.length > 0
        ? items.map((item) => {
            const receipts = item.receipts ?? [];
            const key = `${item.order_item ?? ""}-${item.product_code ?? ""}`;
            return (
              <div key={key} className="sp-purchase-order-detail__item-card">
                <SuppliesSectionCard
                  title={`${C.colItem} ${item.order_item || "—"} · ${formatProductLabel(
                    item.product_code,
                    item.product_description,
                  )}`}
                  hint={SP_HELP.purchaseOrderDetailItems}
                >
                <dl className="sp-purchase-order-detail__item-meta">
                  <div>
                    <dt>{C.colSupplier}</dt>
                    <dd>
                      <SuppliesSupplierIdentity
                        name={item.supplier_name}
                        code={item.supplier_code}
                        store={item.supplier_store}
                      />
                    </dd>
                  </div>
                  <div>
                    <dt>{C.sourceRequestLabel}</dt>
                    <dd>{sourceRequestLabel(item)}</dd>
                  </div>
                  <div>
                    <dt>{C.issueDateLabel}</dt>
                    <dd>{formatDatePtBr(item.issue_date)}</dd>
                  </div>
                  <div>
                    <dt>{C.colDelivery}</dt>
                    <dd>{formatDatePtBr(item.expected_delivery_date)}</dd>
                  </div>
                  <div>
                    <dt>{C.colStatus}</dt>
                    <dd>
                      <SuppliesStatusBadge
                        label={labelDeliveryStatus(item.delivery_status)}
                        variant={statusBadgeVariant(item.delivery_status)}
                      />
                    </dd>
                  </div>
                  {item.buyer_code ? (
                    <div>
                      <dt>{C.buyerLabel}</dt>
                      <dd>
                        <SuppliesPersonIdentity
                          person={{ code: item.buyer_code, name: item.buyer_code }}
                        />
                      </dd>
                    </div>
                  ) : null}
                  <div>
                    <dt>{C.orderedQtyLabel}</dt>
                    <dd>{formatQuantity(item.ordered_quantity)}</dd>
                  </div>
                  <div>
                    <dt>{C.deliveredQtyLabel}</dt>
                    <dd>{formatQuantity(item.delivered_quantity)}</dd>
                  </div>
                  <div>
                    <dt>{C.colOpenQty}</dt>
                    <dd>{formatQuantity(item.open_quantity)}</dd>
                  </div>
                  <div>
                    <dt>{C.unitPriceLabel}</dt>
                    <dd>{formatMoneyBr(item.unit_price)}</dd>
                  </div>
                  <div>
                    <dt>{C.colOpenValue}</dt>
                    <dd>{formatMoneyBr(item.open_value)}</dd>
                  </div>
                </dl>

                <h3 className="sp-purchase-order-detail__receipts-title">
                  <SuppliesSectionHintLabel
                    label={C.receiptsTitle}
                    hint={SP_HELP.purchaseOrderDetailReceipts}
                  />
                </h3>
                {receipts.length === 0 ? (
                  <SuppliesEmptyState title={C.receiptsTitle} message={C.receiptsEmpty} />
                ) : (
                  <div
                    className="sp-purchase-orders__table-wrap"
                    role="region"
                    aria-label={C.receiptsTableScrollRegion}
                    tabIndex={0}
                  >
                    <table className="sp-purchase-orders__table">
                      <thead>
                        <tr>
                          <th>{C.invoiceLabel}</th>
                          <th>{C.colItem}</th>
                          <th>{C.receiptQtyLabel}</th>
                          <th>{C.unitPriceLabel}</th>
                          <th>{C.receiptValueLabel}</th>
                          <th>{C.invoiceDateLabel}</th>
                          <th>{C.entryDateLabel}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {receipts.map((receipt, index) => (
                          <tr
                            key={`${receipt.invoice_number ?? ""}-${receipt.invoice_item ?? ""}-${index}`}
                          >
                            <td>{invoiceLabel(receipt)}</td>
                            <td>{receipt.invoice_item || "—"}</td>
                            <td>{formatQuantity(receipt.quantity)}</td>
                            <td>{formatMoneyBr(receipt.unit_price)}</td>
                            <td>{formatMoneyBr(receipt.total_value)}</td>
                            <td>{formatDatePtBr(receipt.invoice_issue_date)}</td>
                            <td>{formatDatePtBr(receipt.entry_date)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </SuppliesSectionCard>
              </div>
            );
          })
        : null}
    </div>
  );
}
