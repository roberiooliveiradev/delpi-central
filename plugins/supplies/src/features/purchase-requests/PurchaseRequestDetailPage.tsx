import { useEffect, useState } from "react";

import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import {
  SuppliesPersonIdentity,
  SuppliesSupplierIdentity,
} from "../../app/SuppliesDirectoryIdentity";
import {
  buildPluginPath,
  buildPurchaseOrderDetailPath,
} from "../../app/pluginRoutes";
import { formatSuppliesUnitLabel } from "../../app/suppliesUnits";
import {
  SuppliesActionButton,
  SuppliesEmptyState,
  SuppliesEntityLink,
  SuppliesEventsSection,
  SuppliesInlineEmptyState,
  SuppliesLoadingCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesSectionHintLabel,
  SuppliesStateBanner,
  SuppliesStatusBadge,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { getPurchaseRequest } from "./api";
import {
  classifyPurchaseRequestDetailError,
  PURCHASE_REQUESTS_CONTENT as C,
} from "./content";
import {
  approvalBadgeVariant,
  collectLinkedOrders,
  collectReceipts,
  countLinkedOrders,
  formatDatePtBr,
  formatMoneyBr,
  formatProductLabel,
  formatQuantity,
  formatQuantityWithUnit,
  formatRequestNumber,
  hasCompleteOrderIdentity,
  isKnownOverallStage,
  labelApprovalStatus,
  labelLinkedOrderDeliveryStatus,
  labelOverallStage,
  linkedOrderDeliveryVariant,
  stageBadgeVariant,
  timelineEventTone,
  timelineReferenceLabel,
  uniqueApproverNames,
} from "./query";
import type { PurchaseRequestDetail } from "./types";

type PurchaseRequestDetailPageProps = {
  basePath: string;
  branch: string;
  requestNumber: string;
};

export function PurchaseRequestDetailPage({
  basePath,
  branch,
  requestNumber,
}: PurchaseRequestDetailPageProps) {
  const listHref = buildPluginPath("purchase_requests", basePath);
  const [loading, setLoading] = useState(true);
  const [errorKind, setErrorKind] = useState<"forbidden" | "not_found" | "error" | null>(
    null,
  );
  const [errorText, setErrorText] = useState<string | null>(null);
  const [detail, setDetail] = useState<PurchaseRequestDetail | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!branch || !requestNumber) return;
    const controller = new AbortController();
    setLoading(true);
    setErrorKind(null);
    setErrorText(null);
    getPurchaseRequest(branch, requestNumber, undefined, controller.signal)
      .then((payload) => {
        setDetail(payload);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setDetail(null);
        const message = err instanceof Error ? err.message : C.detailError;
        const classified = classifyPurchaseRequestDetailError(message);
        setErrorKind(classified.kind);
        setErrorText(classified.text);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, requestNumber, reloadKey]);

  const header = detail?.header;
  const lines = detail?.lines ?? [];
  const displayNumber = formatRequestNumber(header?.request_number || requestNumber);

  const stage = header?.overall_stage;
  const costCenters = header?.cost_centers ?? [];
  const firstCostCenter = costCenters[0];
  const costCenterLabel = firstCostCenter
    ? `${firstCostCenter.code}${
        firstCostCenter.description ? ` — ${firstCostCenter.description}` : ""
      }${costCenters.length > 1 ? ` (+${costCenters.length - 1})` : ""}`
    : "—";
  const costCenterTitle =
    costCenters.length > 1
      ? costCenters
          .map(
            (cc) => `${cc.code}${cc.description ? ` — ${cc.description}` : ""}`,
          )
          .join(" · ")
      : undefined;
  const approverNames = uniqueApproverNames(lines);
  const linkedOrdersCount = countLinkedOrders(header?.purchase_orders);
  const hasLinkedOrders = Boolean(header?.purchase_orders?.length);
  const overdueDays = header?.max_days_overdue;

  // Enriched linked orders/receipts live at line level (the header carries a
  // deduped order+supplier summary only).
  const linkedOrders = collectLinkedOrders(lines);
  const receipts = collectReceipts(linkedOrders);
  const timelineEvents = detail?.timeline ?? [];

  return (
    <div className="sp-page-stack sp-purchase-request-detail">
      <SuppliesPagePath
        back={{
          label: C.detailBack,
          href: listHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("purchase_requests", { basePath });
          },
        }}
        items={[]}
        current={`${C.detailTitle} ${displayNumber}`}
      />

      <SuppliesPageHero
        eyebrow={C.detailEyebrow}
        title={
          <SuppliesSectionHintLabel
            label={`${C.detailTitle} ${displayNumber}`}
            hint={SP_HELP.purchaseRequestDetail}
          />
        }
        description={C.detailDescription}
        aria-label={C.detailTitle}
      >
        <dl className="sp-purchase-request-detail__identity">
          <div>
            <dt>{C.detailUnitLabel}</dt>
            <dd>{formatSuppliesUnitLabel(header?.branch || branch)}</dd>
          </div>
          <div>
            <dt>{C.detailTitle}</dt>
            <dd>{displayNumber}</dd>
          </div>
          <div>
            <dt>{C.detailOpenedLabel}</dt>
            <dd>{formatDatePtBr(header?.issue_date)}</dd>
          </div>
          <div>
            <dt>{C.detailStageLabel}</dt>
            <dd>
              {isKnownOverallStage(stage) ? (
                <SuppliesStatusBadge
                  label={labelOverallStage(stage)}
                  variant={stageBadgeVariant(stage)}
                />
              ) : (
                labelOverallStage(stage)
              )}
            </dd>
          </div>
        </dl>
        <dl className="sp-purchase-request-detail__identity sp-purchase-request-detail__context">
          <div>
            <dt>{C.detailRequesterLabel}</dt>
            <dd>
              <SuppliesPersonIdentity
                person={header?.requester}
                photoPeriod={{
                  dateFrom: header?.issue_date,
                  dateTo: header?.issue_date,
                }}
                basePath={basePath}
              />
            </dd>
          </div>
          <div>
            <dt>{C.detailCostCenterLabel}</dt>
            <dd title={costCenterTitle}>{costCenterLabel}</dd>
          </div>
          <div>
            <dt>{C.detailApprovalLabel}</dt>
            <dd>
              <SuppliesStatusBadge
                label={labelApprovalStatus(header?.approval_summary?.status, {
                  approved: C.approvalApproved,
                  rejected: C.approvalRejected,
                  blocked: C.approvalBlocked,
                  unknown: C.approvalUnknown,
                })}
                variant={approvalBadgeVariant(
                  header?.approval_summary?.status,
                )}
              />
              {approverNames.length === 1 ? (
                <span className="sp-purchase-request-detail__approver">
                  {" "}
                  {approverNames[0]}
                </span>
              ) : null}
              {approverNames.length > 1 ? (
                <span className="sp-purchase-request-detail__approver">
                  {" "}
                  {C.detailApproversMany(approverNames.length)}
                </span>
              ) : null}
            </dd>
          </div>
        </dl>
        <dl className="sp-purchase-request-detail__identity sp-purchase-request-detail__indicators">
          <div>
            <dt>{C.detailIndicatorItems}</dt>
            <dd>{header?.visible_items_count ?? lines.length}</dd>
          </div>
          <div>
            <dt>{C.detailIndicatorOrders}</dt>
            <dd>{linkedOrdersCount}</dd>
          </div>
          <div>
            <dt>{C.detailIndicatorOverdue}</dt>
            <dd>
              {!hasLinkedOrders ? (
                "—"
              ) : header?.has_overdue_order ? (
                <>
                  <SuppliesStatusBadge
                    label={C.detailOverdueYes}
                    variant="danger"
                  />
                  {typeof overdueDays === "number" && overdueDays > 0 ? (
                    <span className="sp-purchase-request-detail__overdue-note">
                      {" "}
                      {C.detailOverdueDays(overdueDays)}
                    </span>
                  ) : null}
                </>
              ) : (
                C.detailOverdueNone
              )}
            </dd>
          </div>
        </dl>
        <p className="sp-purchase-request-detail__scope-note">
          {C.detailScopeNote}
        </p>
      </SuppliesPageHero>

      {errorKind === "forbidden" ? (
        <div className="sp-purchase-request-detail__error">
          <SuppliesStateBanner variant="error">{errorText}</SuppliesStateBanner>
        </div>
      ) : null}

      {errorKind === "not_found" ? (
        <SuppliesEmptyState title={C.detailTitle} message={errorText || C.detailNotFound} />
      ) : null}

      {errorKind === "error" ? (
        <div className="sp-purchase-request-detail__error">
          <SuppliesStateBanner variant="error">{errorText}</SuppliesStateBanner>
          <SuppliesActionButton
            type="button"
            variant="primary"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            {C.detailRetry}
          </SuppliesActionButton>
        </div>
      ) : null}

      {loading ? <SuppliesLoadingCard title={C.detailLoading} variant="panel" /> : null}

      {!loading && !errorKind && lines.length === 0 ? (
        <SuppliesEmptyState title={C.itemsTitle} message={C.itemsEmpty} />
      ) : null}

      {!loading && !errorKind && lines.length > 0 ? (
        <>
          <SuppliesSectionCard title={C.itemsTitle} hint={C.detailHint}>
            <ul className="sp-purchase-requests__detail-lines">
              {lines.map((line, index) => {
                const lineStage = line.derived?.overall_stage;
                const lineCostCenter = line.cost_center;
                const costCenterText = lineCostCenter?.code
                  ? `${lineCostCenter.code}${
                      lineCostCenter.description
                        ? ` — ${lineCostCenter.description}`
                        : ""
                    }`
                  : line.cost_center_code || "—";
                const suggested = line.suggested_supplier;
                const hasSuggested = Boolean(
                  (suggested?.code || "").trim() || (suggested?.name || "").trim(),
                );
                const approverName = (line.approval?.approver_name || "").trim();
                return (
                  <li key={`${line.request_item ?? index}-${line.product_code ?? index}`}>
                    <div className="sp-purchase-request-detail__line-head">
                      <strong>{line.request_item || "—"}</strong>{" "}
                      {formatProductLabel(line.product_code, line.product_description)}
                      {isKnownOverallStage(lineStage) ? (
                        <SuppliesStatusBadge
                          label={labelOverallStage(lineStage)}
                          variant={stageBadgeVariant(lineStage)}
                        />
                      ) : null}
                    </div>
                    <dl className="sp-purchase-request-detail__identity sp-purchase-request-detail__line-meta">
                      <div>
                        <dt>{C.colRequestedQty}</dt>
                        <dd>
                          {formatQuantityWithUnit(line.requested_quantity, line.unit)}
                        </dd>
                      </div>
                      <div>
                        <dt>{C.colOrderedQty}</dt>
                        <dd>
                          {formatQuantityWithUnit(line.ordered_quantity, line.unit)}
                        </dd>
                      </div>
                      <div>
                        <dt>{C.colOpenQty}</dt>
                        <dd>
                          {formatQuantityWithUnit(line.request_open_quantity, line.unit)}
                        </dd>
                      </div>
                      <div>
                        <dt>{C.colRequiredDate}</dt>
                        <dd>{formatDatePtBr(line.request_required_date)}</dd>
                      </div>
                      <div>
                        <dt>{C.detailCostCenterLabel}</dt>
                        <dd>{costCenterText}</dd>
                      </div>
                      <div>
                        <dt>{C.detailApprovalLabel}</dt>
                        <dd>
                          <SuppliesStatusBadge
                            label={labelApprovalStatus(line.approval?.status, {
                              approved: C.approvalApproved,
                              rejected: C.approvalRejected,
                              blocked: C.approvalBlocked,
                              unknown: C.approvalUnknown,
                            })}
                            variant={approvalBadgeVariant(line.approval?.status)}
                          />
                          {approverName ? (
                            <span className="sp-purchase-request-detail__approver">
                              {" "}
                              {approverName}
                            </span>
                          ) : null}
                        </dd>
                      </div>
                      <div>
                        <dt>{C.colSuggestedSupplier}</dt>
                        <dd>
                          {hasSuggested ? (
                            <SuppliesSupplierIdentity
                              name={suggested?.name}
                              code={suggested?.code}
                              store={suggested?.store}
                              basePath={basePath}
                            />
                          ) : (
                            "—"
                          )}
                        </dd>
                      </div>
                      <div>
                        <dt>{C.colAccountCode}</dt>
                        <dd>{line.account_code || "—"}</dd>
                      </div>
                    </dl>
                  </li>
                );
              })}
            </ul>
          </SuppliesSectionCard>

          <SuppliesSectionCard
            title={C.ordersTitle}
            hint={SP_HELP.purchaseRequestDetailOrders}
          >
            {linkedOrders.length === 0 ? (
              <SuppliesInlineEmptyState message={C.ordersEmpty} />
            ) : (
              <div
                className="sp-purchase-request-detail__table-wrap"
                role="region"
                aria-label={C.ordersTableScrollRegion}
                tabIndex={0}
              >
                <table className="sp-purchase-request-detail__table">
                  <thead>
                    <tr>
                      <th>{C.colOrderNumber}</th>
                      <th>{C.colOrderItem}</th>
                      <th>{C.colOrderProduct}</th>
                      <th>{C.colOrderSupplier}</th>
                      <th className="num">{C.colOrderQty}</th>
                      <th className="num">{C.colReceivedQty}</th>
                      <th className="num">{C.colOrderOpenQty}</th>
                      <th>{C.colExpectedDelivery}</th>
                      <th>{C.colDeliveryStatus}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {linkedOrders.map((order, index) => {
                      const orderNumber = (order.order_number || "").trim();
                      const orderHref = hasCompleteOrderIdentity(order)
                        ? buildPurchaseOrderDetailPath(
                            order.branch || "",
                            orderNumber,
                            basePath,
                          )
                        : null;
                      const key = `${order.branch ?? ""}-${order.order_number ?? ""}-${order.order_item ?? index}`;
                      return (
                        <tr key={key}>
                          <td>
                            {orderHref ? (
                              <SuppliesEntityLink
                                href={orderHref}
                                title={C.openOrderTitle(orderNumber)}
                                className="sp-purchase-request-detail__order-link"
                                onNavigate={() => navigatePluginPath(orderHref)}
                              >
                                {orderNumber}
                              </SuppliesEntityLink>
                            ) : (
                              orderNumber || "—"
                            )}
                          </td>
                          <td>{order.order_item || "—"}</td>
                          <td>
                            {formatProductLabel(
                              order.product_code,
                              order.product_description,
                            )}
                          </td>
                          <td>
                            <SuppliesSupplierIdentity
                              name={order.supplier_name}
                              code={order.supplier_code}
                              store={order.supplier_store}
                              basePath={basePath}
                            />
                          </td>
                          <td className="num">{formatQuantity(order.ordered_quantity)}</td>
                          <td className="num">{formatQuantity(order.received_quantity)}</td>
                          <td className="num">{formatQuantity(order.open_quantity)}</td>
                          <td>{formatDatePtBr(order.expected_delivery_date)}</td>
                          <td>
                            <SuppliesStatusBadge
                              label={labelLinkedOrderDeliveryStatus(
                                order.derived?.delivery_status,
                              )}
                              variant={linkedOrderDeliveryVariant(
                                order.derived?.delivery_status,
                              )}
                            />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </SuppliesSectionCard>

          <SuppliesSectionCard
            title={C.receiptsTitle}
            hint={SP_HELP.purchaseRequestDetailReceipts}
          >
            {receipts.length === 0 ? (
              <SuppliesInlineEmptyState message={C.receiptsEmpty} />
            ) : (
              <div
                className="sp-purchase-request-detail__table-wrap"
                role="region"
                aria-label={C.receiptsTableScrollRegion}
                tabIndex={0}
              >
                <table className="sp-purchase-request-detail__table">
                  <thead>
                    <tr>
                      <th>{C.colInvoice}</th>
                      <th>{C.colInvoiceSeries}</th>
                      <th>{C.colInvoiceItem}</th>
                      <th>{C.colReceiptOrder}</th>
                      <th className="num">{C.colReceiptQty}</th>
                      <th className="num">{C.colReceiptValue}</th>
                      <th>{C.colInvoiceDate}</th>
                      <th>{C.colEntryDate}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {receipts.map((receipt, index) => (
                      <tr
                        key={`${receipt.invoice_number ?? ""}-${receipt.invoice_series ?? ""}-${receipt.invoice_item ?? index}-${index}`}
                      >
                        <td>{receipt.invoice_number || "—"}</td>
                        <td>{receipt.invoice_series || "—"}</td>
                        <td>{receipt.invoice_item || "—"}</td>
                        <td>{receipt.purchase_order_number || "—"}</td>
                        <td className="num">{formatQuantity(receipt.quantity)}</td>
                        <td className="num">{formatMoneyBr(receipt.total_value)}</td>
                        <td>{formatDatePtBr(receipt.invoice_issue_date)}</td>
                        <td>{formatDatePtBr(receipt.entry_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </SuppliesSectionCard>

          <SuppliesEventsSection
            title={C.timelineTitle}
            hint={C.timelineHint}
            omitWhenEmpty={false}
            emptyMessage={C.timelineEmpty}
            listAriaLabel={C.timelineListLabel}
            items={timelineEvents.map((event, index) => {
              const reference = timelineReferenceLabel(event, {
                order: C.timelineRefOrder,
                invoice: C.timelineRefInvoice,
                item: C.timelineRefItem,
              });
              const label =
                event.type === "expected_delivery"
                  ? `${event.label || event.type} (${C.timelinePlannedSuffix})`
                  : event.label || event.type;
              const description = [
                formatDatePtBr(event.date),
                reference,
              ]
                .filter((part) => part && part !== "—")
                .join(" · ");
              return {
                id: `${event.type}-${event.date ?? ""}-${index}`,
                title: label,
                description: description || undefined,
                tone: timelineEventTone(event.type),
              };
            })}
          />
        </>
      ) : null}
    </div>
  );
}
