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
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { getPurchaseRequest } from "./api";
import {
  classifyPurchaseRequestDetailError,
  PURCHASE_REQUESTS_CONTENT as C,
} from "./content";
import {
  formatDatePtBr,
  formatProductLabel,
  formatRequestNumber,
  labelOverallStage,
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
            <dt>Unidade</dt>
            <dd>{formatSuppliesUnitLabel(header?.branch || branch)}</dd>
          </div>
          <div>
            <dt>Solicitação</dt>
            <dd>{displayNumber}</dd>
          </div>
          <div>
            <dt>Solicitante</dt>
            <dd>
              <SuppliesPersonIdentity person={header?.requester} />
            </dd>
          </div>
          <div>
            <dt>Abertura</dt>
            <dd>{formatDatePtBr(header?.issue_date)}</dd>
          </div>
          <div>
            <dt>Situação</dt>
            <dd>{labelOverallStage(header?.overall_stage)}</dd>
          </div>
          <div>
            <dt>Itens</dt>
            <dd>{header?.visible_items_count ?? lines.length}</dd>
          </div>
        </dl>
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
