import { useEffect, useState } from "react";

import { ApiRequestError } from "../../api/httpClient";
import { formatSuppliesUnitName } from "../../app/suppliesUnits";
import {
  SuppliesActionButton,
  SuppliesLoadingCard,
  SuppliesModal,
  SuppliesSectionHintLabel,
  SuppliesStateBanner,
  SuppliesStatusBadge,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import {
  getSafetyStockItemDetails,
  getSafetyStockItemSuppliers,
  SafetyStockContractError,
} from "./api";
import {
  SAFETY_STOCK_COVERAGE_STATUS_LABELS,
  SAFETY_STOCK_DATE_STATUS_LABELS,
  SAFETY_STOCK_DETAIL_CONTENT as D,
  SAFETY_STOCK_PROJECTION_STATUS_LABELS,
  labelDetailStatus,
  labelSafetyStockStatus,
  statusBadgeVariant,
} from "./content";
import {
  formatCurrencyPtBr,
  formatDatePtBr,
  formatQuantity,
  formatUnitOfMeasure,
} from "./query";
import type {
  SafetyStockDetailTarget,
  SafetyStockItemDetail,
  SafetyStockLinkedSupplier,
} from "./types";

type LoadState<T> = {
  status: "loading" | "ready" | "error";
  data: T | null;
  error: string | null;
};

function initialLoad<T>(): LoadState<T> {
  return { status: "loading", data: null, error: null };
}

function mapDetailError(err: unknown): string {
  if (err instanceof SafetyStockContractError) return D.invalidResponse;
  if (err instanceof ApiRequestError) {
    if (err.status === 404) return D.notFound;
    if (err.status === 403 || err.status === 401) return D.forbidden;
  }
  return err instanceof Error && err.message ? err.message : D.error;
}

function coverageBadgeVariant(
  status: string | null | undefined,
): "neutral" | "success" | "warning" | "danger" {
  switch (status) {
    case "sufficient":
      return "success";
    case "partial":
      return "warning";
    case "none":
      return "danger";
    default:
      return "neutral";
  }
}

function projectionBadgeVariant(
  status: string | null | undefined,
): "neutral" | "success" | "warning" | "danger" {
  switch (status) {
    case "sufficient":
      return "success";
    case "temporary_shortage":
      return "warning";
    case "projected_deficit":
      return "danger";
    default:
      return "neutral";
  }
}

function dateStatusBadgeVariant(
  status: string | null | undefined,
): "neutral" | "info" | "warning" | "danger" {
  switch (status) {
    case "today":
      return "info";
    case "overdue":
      return "danger";
    case "unscheduled":
      return "warning";
    default:
      return "neutral";
  }
}

function Metric({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <li className="sp-safety-stock-detail__metric">
      <span className="sp-safety-stock-detail__metric-label">
        {hint ? <SuppliesSectionHintLabel label={label} hint={hint} /> : label}
      </span>
      <span className="sp-safety-stock-detail__metric-value">{value}</span>
    </li>
  );
}

function Warnings({ warnings }: { warnings: string[] }) {
  if (!warnings.length) return null;
  return (
    <div className="sp-safety-stock-detail__warnings">
      <strong>{D.warningsTitle}</strong>
      <ul>
        {warnings.map((warning, index) => (
          <li key={index}>{warning}</li>
        ))}
      </ul>
    </div>
  );
}

function joinRef(...parts: Array<string | null | undefined>): string {
  return (
    parts
      .map((part) => String(part ?? "").trim())
      .filter(Boolean)
      .join("/") || "—"
  );
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

type SafetyStockDetailModalProps = {
  target: SafetyStockDetailTarget | null;
  onClose: () => void;
};

export function SafetyStockDetailModal({
  target,
  onClose,
}: SafetyStockDetailModalProps) {
  const [detail, setDetail] = useState<LoadState<SafetyStockItemDetail>>(() =>
    initialLoad(),
  );
  const [suppliers, setSuppliers] = useState<
    LoadState<SafetyStockLinkedSupplier[]>
  >(() => initialLoad());
  const [retryKey, setRetryKey] = useState(0);

  const open = target != null;
  const targetKey = target ? `${target.branch}|${target.productCode}` : "";

  // Dois canais independentes (detalhe / fornecedores): falha de um não
  // bloqueia o outro; troca de item cancela a resposta atrasada do anterior.
  useEffect(() => {
    if (!target) return undefined;
    const controller = new AbortController();
    setDetail(initialLoad());
    getSafetyStockItemDetails(target, controller.signal)
      .then((payload) =>
        setDetail({ status: "ready", data: payload, error: null }),
      )
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setDetail({ status: "error", data: null, error: mapDetailError(err) });
      });
    return () => controller.abort();
  }, [target, targetKey, retryKey]);

  useEffect(() => {
    if (!target) return undefined;
    const controller = new AbortController();
    setSuppliers(initialLoad());
    getSafetyStockItemSuppliers(target, controller.signal)
      .then((payload) =>
        setSuppliers({ status: "ready", data: payload.items, error: null }),
      )
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setSuppliers({
          status: "error",
          data: null,
          error: mapDetailError(err),
        });
      });
    return () => controller.abort();
  }, [target, targetKey, retryKey]);

  if (!open || !target) return null;

  const data = detail.data;
  const product = data?.product;
  const stock = data?.stock;
  const coverage = data?.purchase_coverage;
  const orders = data?.open_purchase_orders;
  const requests = data?.open_purchase_requests;
  const commitments = data?.open_commitments;
  const projection = data?.stock_projection;
  const monthly = data?.monthly_consumption;
  const annual = data?.annual_comparison;

  return (
    <SuppliesModal
      open={open}
      title={D.title(target.productCode)}
      description={D.description}
      onClose={onClose}
      className="sp-safety-stock-detail"
      closeAriaLabel="Fechar detalhes do material"
    >
      {detail.status === "loading" ? (
        <SuppliesLoadingCard title={D.loading} variant="panel" />
      ) : null}

      {detail.status === "error" ? (
        <div className="sp-safety-stock-detail__error">
          <SuppliesStateBanner variant="error">
            {detail.error ?? D.error}
          </SuppliesStateBanner>
          <SuppliesActionButton
            type="button"
            variant="primary"
            onClick={() => setRetryKey((v) => v + 1)}
          >
            {D.retry}
          </SuppliesActionButton>
        </div>
      ) : null}

      {detail.status === "ready" && data && product && stock ? (
        <div className="sp-safety-stock-detail__body">
          <section
            className="sp-safety-stock-detail__section"
            aria-label={D.sectionIdentification}
          >
            <h4 className="sp-safety-stock-detail__section-title">
              {D.sectionIdentification}
            </h4>
            <dl className="sp-safety-stock-detail__grid">
              <div>
                <dt>{D.labelProduct}</dt>
                <dd>{product.product_code?.trim() || "—"}</dd>
              </div>
              <div>
                <dt>{D.labelDescription}</dt>
                <dd>
                  {product.product_description?.trim() || "—"}{" "}
                  {product.blocked ? (
                    <SuppliesStatusBadge label="Bloqueado" variant="neutral" />
                  ) : null}
                </dd>
              </div>
              <div>
                <dt>{D.labelBranch}</dt>
                <dd>{formatSuppliesUnitName(product.branch)}</dd>
              </div>
              <div>
                <dt>{D.labelUnit}</dt>
                <dd>{formatUnitOfMeasure(product.unit)}</dd>
              </div>
              {product.secondary_unit?.trim() ? (
                <div>
                  <dt>{D.labelSecondaryUnit}</dt>
                  <dd>
                    {formatUnitOfMeasure(product.secondary_unit)}
                    {product.conversion_factor != null
                      ? ` · fator ${formatQuantity(product.conversion_factor)}`
                      : ""}
                  </dd>
                </div>
              ) : null}
              <div>
                <dt>{D.labelGroup}</dt>
                <dd>{product.product_group?.trim() || "—"}</dd>
              </div>
              <div>
                <dt>{D.labelType}</dt>
                <dd>{product.product_type?.trim() || "—"}</dd>
              </div>
              <div>
                <dt>{D.labelStatus}</dt>
                <dd>
                  <SuppliesStatusBadge
                    label={labelSafetyStockStatus(product.status)}
                    variant={statusBadgeVariant(product.status)}
                  />
                </dd>
              </div>
            </dl>
          </section>

          <section
            className="sp-safety-stock-detail__section"
            aria-label={D.sectionStock}
          >
            <h4 className="sp-safety-stock-detail__section-title">
              {D.sectionStock}
            </h4>
            <ul className="sp-safety-stock-detail__metrics">
              <Metric
                label={D.labelSafetyStock}
                value={formatQuantity(stock.safety_stock)}
                hint={SP_HELP.safetyStockSafetyStock}
              />
              <Metric
                label={D.labelAvailableStock}
                value={formatQuantity(stock.available_stock)}
              />
              <Metric
                label={D.labelPrimaryStock}
                value={formatQuantity(stock.primary_stock)}
                hint={SP_HELP.safetyStockPrimaryStock}
              />
              <Metric
                label={D.labelWarehouse98}
                value={formatQuantity(stock.warehouse_98_stock)}
              />
              <Metric
                label={D.labelWarehouse99}
                value={formatQuantity(stock.warehouse_99_stock)}
              />
              <Metric
                label={D.labelWorkInProcess}
                value={formatQuantity(stock.work_in_process_stock)}
                hint={SP_HELP.safetyStockWorkInProcess}
              />
              <Metric
                label={D.labelDeficit}
                value={formatQuantity(stock.deficit_quantity)}
                hint={SP_HELP.safetyStockDeficit}
              />
              <Metric
                label={D.labelLastInventoryDate}
                value={formatDatePtBr(stock.last_inventory_date)}
              />
            </ul>
            {coverage ? (
              <div className="sp-safety-stock-detail__coverage">
                <h5>
                  <SuppliesSectionHintLabel
                    label={D.coverageTitle}
                    hint={SP_HELP.safetyStockDetailCoverage}
                  />
                </h5>
                <ul className="sp-safety-stock-detail__metrics">
                  <li className="sp-safety-stock-detail__metric">
                    <span className="sp-safety-stock-detail__metric-label">
                      {D.coverageStatus}
                    </span>
                    <SuppliesStatusBadge
                      label={labelDetailStatus(
                        SAFETY_STOCK_COVERAGE_STATUS_LABELS,
                        coverage.status,
                      )}
                      variant={coverageBadgeVariant(coverage.status)}
                    />
                  </li>
                  <Metric
                    label={D.coverageDeficit}
                    value={formatQuantity(coverage.deficit_quantity)}
                  />
                  <Metric
                    label={D.coverageEligible}
                    value={formatQuantity(coverage.eligible_open_quantity)}
                  />
                  <Metric
                    label={D.coverageRemaining}
                    value={formatQuantity(coverage.remaining_to_buy)}
                  />
                  <Metric
                    label={D.coverageNextDelivery}
                    value={formatDatePtBr(coverage.next_expected_delivery_date)}
                  />
                </ul>
                <Warnings warnings={coverage.warnings ?? []} />
              </div>
            ) : null}
          </section>

          <section
            className="sp-safety-stock-detail__section"
            aria-label={D.sectionSupply}
          >
            <h4 className="sp-safety-stock-detail__section-title">
              {D.sectionSupply}
            </h4>

            <h5 className="sp-safety-stock-detail__subsection">
              {D.ordersTitle}
            </h5>
            {!orders ? (
              <p className="sp-safety-stock-detail__unavailable">
                {D.sectionUnavailable}
              </p>
            ) : orders.items.length === 0 ? (
              <p className="sp-safety-stock-detail__empty">{D.ordersEmpty}</p>
            ) : (
              <div className="sp-safety-stock-detail__table-wrap">
                <table className="sp-safety-stock-detail__table">
                  <thead>
                    <tr>
                      <th>{D.colOrder}</th>
                      <th>{D.colSupplier}</th>
                      <th>{D.colWarehouse}</th>
                      <th>{D.colExpectedDelivery}</th>
                      <th className="num">{D.colOpenQuantity}</th>
                      <th className="num">{D.colOpenValue}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.items.map((order, i) => (
                      <tr key={`${order.order_number}|${order.order_item}|${i}`}>
                        <td>{joinRef(order.order_number, order.order_item)}</td>
                        <td>
                          {order.supplier_name?.trim() ||
                            joinRef(order.supplier_code, order.supplier_store)}
                        </td>
                        <td>{order.warehouse?.trim() || "—"}</td>
                        <td>{formatDatePtBr(order.expected_delivery_date)}</td>
                        <td className="num">
                          {formatQuantity(order.open_quantity)}{" "}
                          {formatUnitOfMeasure(order.unit)}{" "}
                          {order.unit_compatible === false ? (
                            <SuppliesStatusBadge
                              label="UM divergente"
                              variant="warning"
                            />
                          ) : null}
                        </td>
                        <td className="num">
                          {formatCurrencyPtBr(order.open_value)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <h5 className="sp-safety-stock-detail__subsection">
              {D.requestsTitle}
            </h5>
            {!requests ? (
              <p className="sp-safety-stock-detail__unavailable">
                {D.sectionUnavailable}
              </p>
            ) : requests.items.length === 0 ? (
              <p className="sp-safety-stock-detail__empty">{D.requestsEmpty}</p>
            ) : (
              <div className="sp-safety-stock-detail__table-wrap">
                <table className="sp-safety-stock-detail__table">
                  <thead>
                    <tr>
                      <th>{D.colRequest}</th>
                      <th>{D.colSupplier}</th>
                      <th>{D.colWarehouse}</th>
                      <th>{D.colRequiredDate}</th>
                      <th className="num">{D.colOpenQuantity}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {requests.items.map((request, i) => (
                      <tr
                        key={`${request.request_number}|${request.request_item}|${i}`}
                      >
                        <td>
                          {joinRef(request.request_number, request.request_item)}
                        </td>
                        <td>{request.supplier_name?.trim() || "—"}</td>
                        <td>{request.warehouse?.trim() || "—"}</td>
                        <td>{formatDatePtBr(request.required_date)}</td>
                        <td className="num">
                          {formatQuantity(request.open_quantity)}{" "}
                          {formatUnitOfMeasure(request.unit)}{" "}
                          {request.unit_compatible === false ? (
                            <SuppliesStatusBadge
                              label="UM divergente"
                              variant="warning"
                            />
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <h5 className="sp-safety-stock-detail__subsection">
              {D.commitmentsTitle}
            </h5>
            {!commitments ? (
              <p className="sp-safety-stock-detail__unavailable">
                {D.sectionUnavailable}
              </p>
            ) : commitments.items.length === 0 ? (
              <p className="sp-safety-stock-detail__empty">
                {D.commitmentsEmpty}
              </p>
            ) : (
              <div className="sp-safety-stock-detail__table-wrap">
                <table className="sp-safety-stock-detail__table">
                  <thead>
                    <tr>
                      <th>{D.colProductionOrder}</th>
                      <th>{D.colFinishedProduct}</th>
                      <th>{D.colWarehouse}</th>
                      <th>{D.colCommitmentDate}</th>
                      <th className="num">{D.colOpenQuantity}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {commitments.items.map((commitment, i) => (
                      <tr
                        key={`${commitment.production_order}|${commitment.warehouse}|${i}`}
                      >
                        <td>{commitment.production_order?.trim() || "—"}</td>
                        <td>{commitment.finished_product_code?.trim() || "—"}</td>
                        <td>{commitment.warehouse?.trim() || "—"}</td>
                        <td>{formatDatePtBr(commitment.commitment_date)}</td>
                        <td className="num">
                          {formatQuantity(commitment.open_quantity)}{" "}
                          {formatUnitOfMeasure(commitment.unit)}{" "}
                          {commitment.unit_compatible === false ? (
                            <SuppliesStatusBadge
                              label="UM divergente"
                              variant="warning"
                            />
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {commitments?.summary &&
            isStringArray(commitments.summary.warnings) ? (
              <Warnings warnings={commitments.summary.warnings} />
            ) : null}
          </section>

          <section
            className="sp-safety-stock-detail__section"
            aria-label={D.sectionProjection}
          >
            <h4 className="sp-safety-stock-detail__section-title">
              <SuppliesSectionHintLabel
                label={D.sectionProjection}
                hint={SP_HELP.safetyStockDetailProjection}
              />
            </h4>
            {!projection ? (
              <p className="sp-safety-stock-detail__unavailable">
                {D.sectionUnavailable}
              </p>
            ) : (
              <>
                {projection.summary ? (
                  <ul className="sp-safety-stock-detail__metrics">
                    <li className="sp-safety-stock-detail__metric">
                      <span className="sp-safety-stock-detail__metric-label">
                        {D.coverageStatus}
                      </span>
                      <SuppliesStatusBadge
                        label={labelDetailStatus(
                          SAFETY_STOCK_PROJECTION_STATUS_LABELS,
                          projection.summary.status,
                        )}
                        variant={projectionBadgeVariant(
                          projection.summary.status,
                        )}
                      />
                    </li>
                    <Metric
                      label={D.projectionAsOf}
                      value={formatDatePtBr(projection.summary.as_of_date)}
                    />
                    <Metric
                      label={D.projectionInitial}
                      value={formatQuantity(projection.summary.initial_balance)}
                    />
                    <Metric
                      label={D.projectionPurchases}
                      value={formatQuantity(
                        projection.summary.eligible_purchase_quantity,
                      )}
                    />
                    <Metric
                      label={D.projectionCommitments}
                      value={formatQuantity(
                        projection.summary.eligible_commitment_quantity,
                      )}
                    />
                    <Metric
                      label={D.projectionFinal}
                      value={formatQuantity(
                        projection.summary.final_projected_balance,
                      )}
                    />
                    <Metric
                      label={D.projectionAfterSafety}
                      value={formatQuantity(
                        projection.summary.final_balance_after_safety,
                      )}
                    />
                    <Metric
                      label={D.projectionFirstShortage}
                      value={formatDatePtBr(
                        projection.summary.first_shortage_date,
                      )}
                    />
                    <Metric
                      label={D.projectionRemainingToBuy}
                      value={formatQuantity(
                        projection.summary.projected_remaining_to_buy,
                      )}
                    />
                  </ul>
                ) : null}
                <Warnings warnings={projection.summary?.warnings ?? []} />
                {projection.items.length === 0 ? (
                  <p className="sp-safety-stock-detail__empty">
                    {D.projectionEmpty}
                  </p>
                ) : (
                  <div className="sp-safety-stock-detail__table-wrap">
                    <table className="sp-safety-stock-detail__table">
                      <thead>
                        <tr>
                          <th>{D.colDate}</th>
                          <th>{D.colEvent}</th>
                          <th>{D.colReference}</th>
                          <th className="num">{D.colInflow}</th>
                          <th className="num">{D.colOutflow}</th>
                          <th className="num">{D.colRunningBalance}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {projection.items.map((event) => (
                          <tr key={event.sequence}>
                            <td>
                              {formatDatePtBr(event.event_date)}{" "}
                              <SuppliesStatusBadge
                                label={labelDetailStatus(
                                  SAFETY_STOCK_DATE_STATUS_LABELS,
                                  event.date_status,
                                )}
                                variant={dateStatusBadgeVariant(
                                  event.date_status,
                                )}
                              />
                            </td>
                            <td>{event.origin_label?.trim() || "—"}</td>
                            <td>{event.reference?.trim() || "—"}</td>
                            <td className="num">
                              {event.inflow ? formatQuantity(event.inflow) : "—"}
                            </td>
                            <td className="num">
                              {event.outflow
                                ? formatQuantity(event.outflow)
                                : "—"}
                            </td>
                            <td className="num">
                              {formatQuantity(event.running_balance)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </section>

          <section
            className="sp-safety-stock-detail__section"
            aria-label={D.sectionConsumption}
          >
            <h4 className="sp-safety-stock-detail__section-title">
              {D.sectionConsumption}
            </h4>

            <h5 className="sp-safety-stock-detail__subsection">
              {D.monthlyConsumptionTitle}
            </h5>
            {!monthly ? (
              <p className="sp-safety-stock-detail__unavailable">
                {D.sectionUnavailable}
              </p>
            ) : monthly.items.length === 0 ? (
              <p className="sp-safety-stock-detail__empty">
                {D.monthlyConsumptionEmpty}
              </p>
            ) : (
              <>
                <p className="sp-safety-stock-detail__note">
                  {D.monthlyPeriodConsumption}:{" "}
                  <strong>{formatQuantity(monthly.period_consumption)}</strong> ·{" "}
                  {D.monthlyPeriod}: {formatDatePtBr(monthly.period_start)} —{" "}
                  {formatDatePtBr(monthly.period_end)}
                </p>
                <div className="sp-safety-stock-detail__table-wrap">
                  <table className="sp-safety-stock-detail__table">
                    <thead>
                      <tr>
                        <th>{D.colMonth}</th>
                        <th className="num">{D.colConsumption}</th>
                        <th className="num">{D.colMovements}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {monthly.items.map((point) => (
                        <tr key={point.year_month ?? ""}>
                          <td>{point.year_month_label || point.year_month}</td>
                          <td className="num">
                            {formatQuantity(point.consumption_quantity)}
                          </td>
                          <td className="num">
                            {point.movement_count != null
                              ? point.movement_count.toLocaleString("pt-BR")
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}

            <h5 className="sp-safety-stock-detail__subsection">
              {D.annualComparisonTitle}
            </h5>
            {!annual ? (
              <p className="sp-safety-stock-detail__unavailable">
                {D.sectionUnavailable}
              </p>
            ) : annual.items.length === 0 ? (
              <p className="sp-safety-stock-detail__empty">
                {D.annualComparisonEmpty}
              </p>
            ) : (
              <div className="sp-safety-stock-detail__table-wrap">
                <table className="sp-safety-stock-detail__table">
                  <thead>
                    <tr>
                      <th>{D.colMonth}</th>
                      {annual.years.map((year) => (
                        <th key={year} className="num">
                          {year}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {annual.items.map((row) => (
                      <tr key={row.month}>
                        <td>{row.month_label}</td>
                        {annual.years.map((year) => (
                          <td key={year} className="num">
                            {row.values_by_year[year] != null
                              ? formatQuantity(row.values_by_year[year])
                              : "—"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      ) : null}

      <section
        className="sp-safety-stock-detail__section"
        aria-label={D.sectionSuppliers}
      >
        <h4 className="sp-safety-stock-detail__section-title">
          <SuppliesSectionHintLabel
            label={D.suppliersTitle}
            hint={SP_HELP.safetyStockDetailSuppliers}
          />
        </h4>
        {suppliers.status === "loading" ? (
          <SuppliesLoadingCard title={D.loadingSuppliers} variant="panel" />
        ) : null}
        {suppliers.status === "error" ? (
          <div className="sp-safety-stock-detail__error">
            <SuppliesStateBanner variant="error">
              {suppliers.error ?? D.errorSuppliers}
            </SuppliesStateBanner>
            <SuppliesActionButton
              type="button"
              variant="ghost"
              onClick={() => setRetryKey((v) => v + 1)}
            >
              {D.retry}
            </SuppliesActionButton>
          </div>
        ) : null}
        {suppliers.status === "ready" ? (
          suppliers.data && suppliers.data.length === 0 ? (
            <p className="sp-safety-stock-detail__empty">{D.suppliersEmpty}</p>
          ) : (
            <div className="sp-safety-stock-detail__table-wrap">
              <table className="sp-safety-stock-detail__table">
                <thead>
                  <tr>
                    <th>{D.colSupplierCode}</th>
                    <th>{D.colSupplierStore}</th>
                    <th>{D.colSupplierName}</th>
                    <th>{D.colPartNumber}</th>
                    <th>{D.supplierLastPurchase}</th>
                    <th className="num">{D.colLastInvoice}</th>
                  </tr>
                </thead>
                <tbody>
                  {(suppliers.data ?? []).map((supplier) => (
                    <tr
                      key={`${supplier.supplier_code}|${supplier.supplier_store}`}
                    >
                      <td>{supplier.supplier_code?.trim() || "—"}</td>
                      <td>{supplier.supplier_store?.trim() || "—"}</td>
                      <td>
                        {supplier.trade_name?.trim() ||
                          supplier.legal_name?.trim() ||
                          "—"}
                      </td>
                      <td>{supplier.supplier_part_number?.trim() || "—"}</td>
                      <td>
                        {supplier.has_last_purchase ? (
                          <>
                            {formatDatePtBr(supplier.last_purchase_date)} ·{" "}
                            {formatCurrencyPtBr(supplier.last_unit_price)}
                          </>
                        ) : (
                          D.supplierNoPurchase
                        )}
                      </td>
                      <td className="num">
                        {supplier.last_invoice_number?.trim() || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : null}
      </section>
    </SuppliesModal>
  );
}
