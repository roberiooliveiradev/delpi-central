import { useCallback, useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";

import { ApiRequestError } from "../../api/httpClient";
import { formatSuppliesUnitName } from "../../app/suppliesUnits";
import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import {
  SuppliesActionButton,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesSectionHintLabel,
  SuppliesSelectField,
  SuppliesStateBanner,
  SuppliesStatusBadge,
  SuppliesTextField,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { ConsumptionAuditContractError, getConsumptionAuditOrder } from "./api";
import { CONSUMPTION_AUDIT_CONTENT as C } from "./content";
import {
  buildTargetSearch,
  formatDatePtBr,
  formatDateTimePtBr,
  formatQuantity,
  isValidProductionOrder,
  normalizeProductionOrder,
  normalizeUnit,
  parseTargetFromSearch,
  sameTarget,
} from "./query";
import type {
  ConsumptionAuditComponent,
  ConsumptionAuditMovement,
  ConsumptionAuditOperation,
  ConsumptionAuditResponse,
} from "./types";
import type { ConsumptionAuditTarget } from "./query";

type LoadState = {
  key: string;
  status: "loading" | "ready" | "error";
  data: ConsumptionAuditResponse | null;
  error: string | null;
};

function initialLoad(key: string): LoadState {
  return { key, status: "loading", data: null, error: null };
}

function readBrowserSearch(): string {
  if (typeof window === "undefined") return "";
  return window.location.search || "";
}

function mapFetchError(err: unknown): string {
  if (err instanceof ConsumptionAuditContractError) return C.invalidResponse;
  if (err instanceof ApiRequestError) {
    if (err.status === 404) return C.notFound;
    if (err.status === 401 || err.status === 403) return C.forbidden;
    if (err.status === 502 || err.status === 503 || err.status === 504) {
      return C.upstreamDown;
    }
  }
  return err instanceof Error && err.message ? err.message : C.error;
}

function classificationBadgeVariant(
  classification: string,
): "neutral" | "success" | "warning" | "danger" | "info" {
  switch (classification) {
    case "reconciled":
      return "success";
    case "pending":
      return "info";
    case "requires_investigation":
      return "warning";
    case "partial":
      return "warning";
    default:
      return "neutral";
  }
}

function executionBadgeVariant(
  state: string,
): "neutral" | "success" | "warning" | "danger" | "info" {
  switch (state) {
    case "evidenced":
      return "success";
    case "pending":
      return "warning";
    default:
      return "neutral";
  }
}

function labelOf(map: Record<string, string>, key: string): string {
  return map[key] ?? key;
}

function MovementTable({
  movements,
  showReason,
}: {
  movements: ConsumptionAuditMovement[];
  showReason: boolean;
}) {
  if (!movements.length) return null;
  return (
    <table className="sp-consumption-audit__movements-table">
      <thead>
        <tr>
          <th scope="col">{C.colDocument}</th>
          <th scope="col">{C.colIssueDate}</th>
          <th scope="col">{C.colMovementKind}</th>
          <th scope="col">{C.colDirection}</th>
          <th scope="col">{C.colQuantity}</th>
          <th scope="col">{C.colWarehouse}</th>
          {showReason ? <th scope="col">{C.colReason}</th> : null}
        </tr>
      </thead>
      <tbody>
        {movements.map((mv, index) => (
          <tr key={`${mv.document}-${index}`}>
            <td>{mv.document || "—"}</td>
            <td>{formatDatePtBr(mv.issue_date)}</td>
            <td>{labelOf(C.movementKinds, mv.kind)}</td>
            <td>
              {labelOf(C.movementDirections, mv.direction)}
              {mv.reversed ? ` (${C.reversedTag})` : ""}
            </td>
            <td>
              {formatQuantity(mv.quantity)} {mv.unit_of_measure}
            </td>
            <td>{mv.warehouse || "—"}</td>
            {showReason ? (
              <td>{labelOf(C.exclusionReasons, mv.reason ?? "")}</td>
            ) : null}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ComponentMovements({ component }: { component: ConsumptionAuditComponent }) {
  const { classified, excluded } = component.movements;
  if (!classified.length && !excluded.length) {
    return <p className="sp-consumption-audit__note">{C.movementsNone}</p>;
  }
  return (
    <div className="sp-consumption-audit__movements">
      {classified.length ? (
        <div className="sp-consumption-audit__movements-group">
          <h5>{C.movementsClassified}</h5>
          <MovementTable movements={classified} showReason={false} />
        </div>
      ) : null}
      {excluded.length ? (
        <div className="sp-consumption-audit__movements-group">
          <h5>{C.movementsExcluded}</h5>
          <MovementTable movements={excluded} showReason />
        </div>
      ) : null}
    </div>
  );
}

function ExecutionEvidence({ operation }: { operation: ConsumptionAuditOperation }) {
  const ev = operation.execution_evidence;
  const state = ev.execution_state || "unknown";
  const sh8 = ev.sh8_allocation;
  return (
    <div className="sp-consumption-audit__execution">
      <div className="sp-consumption-audit__execution-head">
        <SuppliesSectionHintLabel
          label={C.executionStateTitle}
          hint={C.executionStateHints[state] ?? C.executionStateHints.unknown}
        />
        <SuppliesStatusBadge
          label={labelOf(C.executionStates, state)}
          variant={executionBadgeVariant(state)}
        />
      </div>

      <div className="sp-consumption-audit__evidence-grid">
        <div className="sp-consumption-audit__evidence-block">
          <h5>{C.sh8Title}</h5>
          {sh8.row_present ? (
            <dl className="sp-consumption-audit__kv">
              {sh8.quantity !== undefined ? (
                <div>
                  <dt>{C.sh8Quantity}</dt>
                  <dd>{formatQuantity(sh8.quantity, 3)}</dd>
                </div>
              ) : null}
              {sh8.scheduled_start || sh8.scheduled_end ? (
                <div>
                  <dt>{C.sh6Window}</dt>
                  <dd>
                    {C.sh8Window(
                      formatDateTimePtBr(sh8.scheduled_start),
                      formatDateTimePtBr(sh8.scheduled_end),
                    )}
                  </dd>
                </div>
              ) : null}
            </dl>
          ) : (
            <p className="sp-consumption-audit__note">{C.sh8Absent}</p>
          )}
        </div>

        <div className="sp-consumption-audit__evidence-block">
          <h5>{C.sh6Title}</h5>
          {ev.sh6_appointments.length ? (
            <ul className="sp-consumption-audit__appt-list">
              {ev.sh6_appointments.map((appt, index) => (
                <li key={`${appt.appointment_id}-${index}`}>
                  <span>{`${formatDatePtBr(appt.reported_at)} ${appt.started_at || ""}→${appt.ended_at || ""}`}</span>
                  <span>
                    {C.sh6Reported}: {formatQuantity(appt.reported_quantity, 3)}
                    {appt.lost_quantity
                      ? ` · ${C.sh6Lost}: ${formatQuantity(appt.lost_quantity, 3)}`
                      : ""}
                    {appt.resource ? ` · ${C.sh6Resource}: ${appt.resource}` : ""}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="sp-consumption-audit__note">—</p>
          )}
        </div>

        <div className="sp-consumption-audit__evidence-block">
          <h5>{C.hzaTitle}</h5>
          {ev.hza_records.length ? (
            <ul className="sp-consumption-audit__appt-list">
              {ev.hza_records.map((rec, index) => (
                <li key={`${rec.appointment_ref}-${index}`}>
                  <span>
                    {formatDateTimePtBr(rec.started_at)} →{" "}
                    {formatDateTimePtBr(rec.ended_at)}
                  </span>
                  <span>
                    {C.hzaStatus}: {rec.status || C.hzaNoResource}
                    {rec.resource ? ` · ${C.sh6Resource}: ${rec.resource}` : ""}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="sp-consumption-audit__note">—</p>
          )}
        </div>
      </div>
    </div>
  );
}

function ComponentRow({
  component,
  expanded,
  onToggle,
}: {
  component: ConsumptionAuditComponent;
  expanded: boolean;
  onToggle: () => void;
}) {
  const classification = component.classification || "unknown";
  const movementsCount =
    component.movements.classified.length + component.movements.excluded.length;
  return (
    <>
      <tr>
        <td>
          <div className="sp-consumption-audit__component-code">
            {component.component_code}
          </div>
          <div className="sp-consumption-audit__component-type">
            {component.component_type}
          </div>
        </td>
        <td>{component.component_description || "—"}</td>
        <td>{component.unit_of_measure || "—"}</td>
        <td>{formatQuantity(component.bom.theoretical_quantity)}</td>
        <td>{formatQuantity(component.commitment.original_quantity)}</td>
        <td>{formatQuantity(component.commitment.open_quantity)}</td>
        <td>{formatQuantity(component.commitment.derived_consumed_quantity)}</td>
        <td>{formatQuantity(component.movements.eligible_consumption_quantity)}</td>
        <td>{formatQuantity(component.discrepancy.value)}</td>
        <td>
          <SuppliesStatusBadge
            label={labelOf(C.classifications, classification)}
            variant={classificationBadgeVariant(classification)}
          />
        </td>
        <td>
          <button
            type="button"
            className="sp-consumption-audit__movements-toggle"
            aria-expanded={expanded}
            onClick={onToggle}
            disabled={!movementsCount}
          >
            {expanded ? C.movementsHide : C.movementsShow}
          </button>
        </td>
      </tr>
      {expanded ? (
        <tr className="sp-consumption-audit__movements-row">
          <td colSpan={11}>
            <ComponentMovements component={component} />
          </td>
        </tr>
      ) : null}
    </>
  );
}

function OperationSection({ operation }: { operation: ConsumptionAuditOperation }) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const toggle = (index: number) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });

  return (
    <SuppliesSectionCard
      title={C.operationTitle(operation.operation, operation.work_center || "—")}
      subtitle={C.operationsHint}
    >
      <ExecutionEvidence operation={operation} />

      {operation.components.length ? (
        <div className="sp-consumption-audit__table-wrap">
          <table className="sp-consumption-audit__materials-table">
            <thead>
              <tr>
                <th scope="col">{C.colComponent}</th>
                <th scope="col">{C.colDescription}</th>
                <th scope="col">{C.colUm}</th>
                <th scope="col">{C.colTheoretical}</th>
                <th scope="col">{C.colCommitment}</th>
                <th scope="col">{C.colOpenQty}</th>
                <th scope="col">{C.colDerived}</th>
                <th scope="col">{C.colClassified}</th>
                <th scope="col">{C.colDiscrepancy}</th>
                <th scope="col">{C.colClassification}</th>
                <th scope="col">
                  <span className="sp-visually-hidden">{C.movementsTitle}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {operation.components.map((component, index) => (
                <ComponentRow
                  key={`${component.component_code}-${index}`}
                  component={component}
                  expanded={expanded.has(index)}
                  onToggle={() => toggle(index)}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="sp-consumption-audit__note">{C.operationNoComponents}</p>
      )}
    </SuppliesSectionCard>
  );
}

function QualityBanner({ data }: { data: ConsumptionAuditResponse }) {
  const quality = data.quality;
  if (quality.status !== "partial") return null;
  return (
    <SuppliesStateBanner variant="default">
      <strong>{C.qualityTitle}: {C.qualityStatusPartial}.</strong>{" "}
      {C.qualityPartialHint}
    </SuppliesStateBanner>
  );
}

function QualitySection({ data }: { data: ConsumptionAuditResponse }) {
  const quality = data.quality;
  const hasContent =
    quality.warnings.length > 0 || quality.unresolved_semantics.length > 0;
  if (!hasContent) return null;
  return (
    <SuppliesSectionCard
      title={C.qualityTitle}
      subtitle={C.qualityPartialHint}
    >
      {quality.warnings.length ? (
        <div className="sp-consumption-audit__quality-block">
          <h5>{C.warningsTitle}</h5>
          <ul className="sp-consumption-audit__quality-list">
            {quality.warnings.map((warning) => (
              <li key={warning}>{labelOf(C.warningLabels, warning)}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {quality.unresolved_semantics.length ? (
        <div className="sp-consumption-audit__quality-block">
          <h5>{C.unresolvedTitle}</h5>
          <ul className="sp-consumption-audit__quality-list">
            {quality.unresolved_semantics.map((item) => (
              <li key={item}>{labelOf(C.unresolvedLabels, item)}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </SuppliesSectionCard>
  );
}

type ConsumptionAuditPageProps = {
  basePath: string;
};

export function ConsumptionAuditPage({ basePath }: ConsumptionAuditPageProps) {
  const [target, setTarget] = useState<ConsumptionAuditTarget | null>(() =>
    parseTargetFromSearch(readBrowserSearch()),
  );
  const [result, setResult] = useState<LoadState>(() =>
    initialLoad(""),
  );
  const [retryKey, setRetryKey] = useState(0);
  const [lastQueriedAt, setLastQueriedAt] = useState<Date | null>(null);

  // Campos do formulário — espelham o último alvo válido na URL.
  const [unitDraft, setUnitDraft] = useState<string>(
    () => parseTargetFromSearch(readBrowserSearch())?.unit ?? "",
  );
  const [opDraft, setOpDraft] = useState<string>(
    () => parseTargetFromSearch(readBrowserSearch())?.productionOrder ?? "",
  );
  const [formError, setFormError] = useState<string | null>(null);

  // URL → estado: popstate (voltar/avançar/navigatePluginPath) re-sincroniza.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const onPopState = () => {
      setTarget(parseTargetFromSearch(readBrowserSearch()));
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const targetKey = target
    ? `${target.unit}|${target.productionOrder}`
    : "";

  useEffect(() => {
    if (!target) return undefined;
    const controller = new AbortController();
    const key = `${target.unit}|${target.productionOrder}`;
    getConsumptionAuditOrder(
      { unit: target.unit, productionOrder: target.productionOrder },
      controller.signal,
    )
      .then((data) => {
        setResult({ key, status: "ready", data, error: null });
        setLastQueriedAt(new Date());
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setResult({
          key,
          status: "error",
          data: null,
          error: mapFetchError(err),
        });
      });
    return () => controller.abort();
  }, [target, retryKey]);

  const resultState =
    result.key === targetKey ? result : initialLoad(targetKey);
  const loading = Boolean(target) && resultState.status === "loading";
  const data = resultState.data;

  const submitQuery = useCallback(() => {
    const unit = normalizeUnit(unitDraft);
    const op = normalizeProductionOrder(opDraft);
    if (!unit) {
      setFormError(C.unitInvalid);
      return;
    }
    if (!isValidProductionOrder(op)) {
      setFormError(C.opInvalid);
      return;
    }
    setFormError(null);
    const next: ConsumptionAuditTarget = { unit, productionOrder: op };
    if (sameTarget(next, target)) {
      setRetryKey((value) => value + 1);
      return;
    }
    navigatePluginPath(
      `${buildPluginPath("consumption_audit", basePath)}${buildTargetSearch(next)}`,
    );
  }, [unitDraft, opDraft, target, basePath]);

  const unitOptions = useMemo(
    () => [
      { value: "01", label: formatSuppliesUnitName("01") },
      { value: "02", label: formatSuppliesUnitName("02") },
    ],
    [],
  );

  const homeBack = {
    label: "Portal Suprimentos",
    href: buildPluginPath("home", basePath),
    onNavigate: (event: { preventDefault(): void }) => {
      event.preventDefault();
      navigatePluginView("home", { basePath });
    },
  };

  return (
    <div className="sp-page-stack sp-consumption-audit">
      <SuppliesPagePath back={homeBack} items={[]} current={C.title} />

      <SuppliesPageHero
        eyebrow={C.eyebrow}
        title={
          <SuppliesSectionHintLabel label={C.title} hint={SP_HELP.consumptionAudit} />
        }
        description={C.description}
        actions={
          data && !loading ? (
            <span className="sp-list-freshness">
              {lastQueriedAt
                ? C.updatedAtLabel(
                    lastQueriedAt.toLocaleTimeString("pt-BR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    }),
                  )
                : ""}
            </span>
          ) : null
        }
      >
        <form
          className="sp-consumption-audit__query"
          aria-label={C.queryTitle}
          onSubmit={(event) => {
            event.preventDefault();
            submitQuery();
          }}
        >
          <div className="sp-consumption-audit__query-grid">
            <SuppliesSelectField
              label={C.unitLabel}
              hint={C.queryHint}
              value={unitDraft}
              options={unitOptions}
              onChange={(value) => setUnitDraft(value)}
            />
            <SuppliesTextField
              label={C.opLabel}
              value={opDraft}
              onChange={(value) => setOpDraft(value)}
              placeholder={C.opPlaceholder}
              hint={C.opInvalid}
            />
            <div className="sp-consumption-audit__query-actions">
              <SuppliesActionButton
                type="submit"
                variant="primary"
                disabled={loading}
              >
                <Search size={16} aria-hidden="true" />
                <span>{loading ? C.loading : C.consultAction}</span>
              </SuppliesActionButton>
            </div>
          </div>
          {formError ? (
            <SuppliesStateBanner variant="error">{formError}</SuppliesStateBanner>
          ) : null}
        </form>
      </SuppliesPageHero>

      {!target ? (
        <SuppliesEmptyState title={C.emptyTitle} message={C.emptyMessage} />
      ) : null}

      {loading ? (
        <SuppliesLoadingCard title={C.loading} variant="panel" />
      ) : null}

      {target && resultState.status === "error" ? (
        <div className="sp-consumption-audit__error">
          <SuppliesStateBanner variant="error">
            {resultState.error ?? C.error}
          </SuppliesStateBanner>
          <SuppliesActionButton
            type="button"
            variant="primary"
            onClick={() => setRetryKey((value) => value + 1)}
          >
            {C.retry}
          </SuppliesActionButton>
        </div>
      ) : null}

      {data ? (
        <>
          <QualityBanner data={data} />

          <SuppliesSectionCard title={C.orderTitle} subtitle={C.orderHint}>
            <dl className="sp-consumption-audit__grid">
              <div>
                <dt>{C.orderProduct}</dt>
                <dd>
                  {data.order.product_code}
                  {data.order.product_description
                    ? ` · ${data.order.product_description}`
                    : ""}
                </dd>
              </div>
              <div>
                <dt>{C.orderProductType}</dt>
                <dd>{data.order.product_type || "—"}</dd>
              </div>
              <div>
                <dt>{C.orderPlannedQty}</dt>
                <dd>
                  {formatQuantity(data.order.planned_quantity, 3)}{" "}
                  {data.order.unit_of_measure}
                </dd>
              </div>
              <div>
                <dt>
                  <SuppliesSectionHintLabel
                    label={C.orderProducedQty}
                    hint={C.producedBasisStockReceipt}
                  />
                </dt>
                <dd>
                  {formatQuantity(data.order.produced_quantity, 3)}{" "}
                  {data.order.unit_of_measure}
                </dd>
              </div>
              <div>
                <dt>{C.orderStatus}</dt>
                <dd>{labelOf(C.statusLabels, data.order.status)}</dd>
              </div>
              <div>
                <dt>{C.orderEmission}</dt>
                <dd>{formatDatePtBr(data.order.emission_date)}</dd>
              </div>
              <div>
                <dt>{C.orderPlannedStart}</dt>
                <dd>{formatDatePtBr(data.order.planned_start_date)}</dd>
              </div>
              <div>
                <dt>{C.orderDue}</dt>
                <dd>{formatDatePtBr(data.order.due_date)}</dd>
              </div>
              {data.order.finished_at ? (
                <div>
                  <dt>{C.orderFinishedAt}</dt>
                  <dd>{formatDatePtBr(data.order.finished_at)}</dd>
                </div>
              ) : null}
              <div>
                <dt>{C.orderWarehouse}</dt>
                <dd>{data.order.warehouse || "—"}</dd>
              </div>
            </dl>
          </SuppliesSectionCard>

          <h2 className="sp-consumption-audit__section-heading">
            {C.operationsTitle}
          </h2>
          {data.operations.map((operation) => (
            <OperationSection
              key={operation.operation}
              operation={operation}
            />
          ))}

          {data.unmatched_movements.length ? (
            <SuppliesSectionCard
              title={C.unmatchedTitle}
              subtitle={C.unmatchedHint}
            >
              <div className="sp-consumption-audit__table-wrap">
                <table className="sp-consumption-audit__movements-table">
                  <thead>
                    <tr>
                      <th scope="col">{C.colComponent}</th>
                      <th scope="col">{C.colDocument}</th>
                      <th scope="col">{C.colIssueDate}</th>
                      <th scope="col">{C.colMovementKind}</th>
                      <th scope="col">{C.colQuantity}</th>
                      <th scope="col">{C.colReason}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.unmatched_movements.map((mv, index) => (
                      <tr key={`${mv.document}-${mv.component_code}-${index}`}>
                        <td>{mv.component_code}</td>
                        <td>{mv.document || "—"}</td>
                        <td>{formatDatePtBr(mv.issue_date)}</td>
                        <td>{labelOf(C.movementKinds, mv.kind)}</td>
                        <td>
                          {formatQuantity(mv.quantity, 3)} {mv.unit_of_measure}
                        </td>
                        <td>{labelOf(C.exclusionReasons, mv.reason ?? "")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </SuppliesSectionCard>
          ) : null}

          {data.related_orders.length ? (
            <SuppliesSectionCard
              title={C.relatedTitle}
              subtitle={C.relatedHint}
            >
              <ul className="sp-consumption-audit__related-list">
                {data.related_orders.map((rel, index) => (
                  <li key={`${rel.production_order}-${index}`}>
                    <button
                      type="button"
                      className="sp-consumption-audit__related-link"
                      onClick={() => {
                        const unit = normalizeUnit(data.branch);
                        if (!unit) return;
                        navigatePluginPath(
                          `${buildPluginPath("consumption_audit", basePath)}${buildTargetSearch({ unit, productionOrder: rel.production_order })}`,
                        );
                      }}
                    >
                      <strong>{rel.production_order}</strong>
                      {rel.product_code ? ` · ${rel.product_code}` : ""}
                      {rel.product_type ? ` (${rel.product_type})` : ""}
                      <span className="sp-consumption-audit__related-rel">
                        {labelOf(C.relatedRelationships, rel.relationship)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </SuppliesSectionCard>
          ) : null}

          <QualitySection data={data} />

          <p className="sp-consumption-audit__meta">
            {C.metaContract(data.metadata.contract_version)} ·{" "}
            {C.metaSource(data.metadata.generated_at_source)}
          </p>
        </>
      ) : null}
    </div>
  );
}
