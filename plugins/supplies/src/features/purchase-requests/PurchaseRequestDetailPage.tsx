import { useEffect, useState } from "react";

import { navigatePluginView } from "../../app/pluginNavigation";
import { SuppliesPersonIdentity } from "../../app/SuppliesDirectoryIdentity";
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
import { getPurchaseRequest } from "./api";
import {
  classifyPurchaseRequestDetailError,
  PURCHASE_REQUESTS_CONTENT as C,
} from "./content";
import {
  approvalBadgeVariant,
  countLinkedOrders,
  formatDatePtBr,
  formatProductLabel,
  formatRequestNumber,
  isKnownOverallStage,
  labelApprovalStatus,
  labelOverallStage,
  stageBadgeVariant,
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
        <SuppliesSectionCard title={C.itemsTitle} hint={C.detailHint}>
          <ul className="sp-purchase-requests__detail-lines">
            {lines.map((line, index) => (
              <li key={`${line.request_item ?? index}-${line.product_code ?? index}`}>
                <strong>{line.request_item || "—"}</strong>{" "}
                {formatProductLabel(line.product_code, line.product_description)}
                <span>
                  {labelOverallStage(line.derived?.overall_stage)} · CC{" "}
                  {line.cost_center_code || "—"}
                </span>
              </li>
            ))}
          </ul>
        </SuppliesSectionCard>
      ) : null}
    </div>
  );
}
