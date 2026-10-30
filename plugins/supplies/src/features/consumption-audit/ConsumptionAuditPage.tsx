import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Filter } from "lucide-react";

import { ApiRequestError } from "../../api/httpClient";
import { formatSuppliesUnitName } from "../../app/suppliesUnits";
import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import {
  matchSuppliesQuickPeriod,
  resolveSuppliesQuickPeriod,
  SUPPLIES_QUICK_PERIOD_OPTIONS,
  type SuppliesQuickPeriodId,
} from "../../app/periodPreset";
import {
  SuppliesActionButton,
  SuppliesClearFiltersButton,
  SuppliesCompactPagination,
  SuppliesDataTable,
  SuppliesDateField,
  SuppliesEmptyState,
  SuppliesFilterBarShell,
  SuppliesFilterCheckbox,
  SuppliesLoadingCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesSectionHintLabel,
  SuppliesSegmentToggle,
  SuppliesSelectField,
  spFiltersKit,
  SuppliesStateBanner,
  SuppliesStatusBadge,
  SuppliesTextField,
  type DataTableColumn,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import {
  ConsumptionAuditContractError,
  getConsumptionAuditComparison,
  getConsumptionAuditOrder,
  searchConsumptionAuditOrders,
} from "./api";
import { CONSUMPTION_AUDIT_CONTENT as C } from "./content";
import {
  buildSearchQuery,
  buildTargetSearch,
  EMPTY_FILTERS,
  filtersAreEmpty,
  formatDatePtBr,
  formatDateTimePtBr,
  formatQuantity,
  isValidProductionOrder,
  normalizeUnit,
  parseFiltersFromSearch,
  parseTargetFromSearch,
} from "./query";
import type {
  ConsumptionAuditComparisonResponse,
  ConsumptionAuditComponent,
  ConsumptionAuditDateType,
  ConsumptionAuditMovement,
  ConsumptionAuditOperation,
  ConsumptionAuditOrderSummary,
  ConsumptionAuditResponse,
  ConsumptionAuditSearchPage,
} from "./types";
import type { ConsumptionAuditFilterState, ConsumptionAuditTarget } from "./query";

type LoadState = {
  key: string;
  status: "loading" | "ready" | "error";
  data: ConsumptionAuditResponse | null;
  error: string | null;
};

type SearchState = {
  key: string;
  status: "idle" | "loading" | "ready" | "error";
  page: ConsumptionAuditSearchPage | null;
  error: string | null;
};

type ComparisonState = {
  status: "idle" | "loading" | "ready" | "error";
  data: ConsumptionAuditComparisonResponse | null;
  error: string | null;
};

const SEARCH_DEBOUNCE_MS = 350;
const SEARCH_MIN_CHARS = 2;
const SEARCH_PAGE_SIZE = 10;
const COMPARE_MAX = 10;

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

// ————————————————————————————————————————————————————————————
// Detalhe da OP (inalterado — F5/regressão)
// ————————————————————————————————————————————————————————————

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
      collapsible
      defaultOpen
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

// ————————————————————————————————————————————————————————————
// F4 · seção de comparação
// ————————————————————————————————————————————————————————————

function ComparisonSection({ data }: { data: ConsumptionAuditComparisonResponse }) {
  const items = data.items;
  const uoms = useMemo(() => {
    const set = new Map<string, string | null>();
    for (const item of items) {
      for (const t of item.totals_by_unit) set.set(t.unit_of_measure ?? "?", t.unit_of_measure);
    }
    return [...set.keys()];
  }, [items]);

  const totalsFor = (itemIndex: number, uom: string) =>
    items[itemIndex].totals_by_unit.find(
      (t) => (t.unit_of_measure ?? "?") === uom,
    );

  const metricRows: Array<{ key: string; label: string; pick: (t: { theoretical_quantity: number; committed_quantity: number; open_commitment_quantity: number; derived_consumption_quantity: number; eligible_consumption_quantity: number } | undefined) => number | null }> = [
    { key: "theoretical", label: C.metricTheoretical, pick: (t) => t?.theoretical_quantity ?? null },
    { key: "committed", label: C.metricCommitted, pick: (t) => t?.committed_quantity ?? null },
    { key: "open", label: C.metricOpen, pick: (t) => t?.open_commitment_quantity ?? null },
    { key: "derived", label: C.metricDerived, pick: (t) => t?.derived_consumption_quantity ?? null },
    { key: "eligible", label: C.metricEligible, pick: (t) => t?.eligible_consumption_quantity ?? null },
  ];

  return (
    <div className="sp-consumption-audit__comparison">
      {data.not_found.length ? (
        <SuppliesStateBanner variant="default">
          {C.compareNotFound}
          {data.not_found.join(", ")}
        </SuppliesStateBanner>
      ) : null}

      {uoms.map((uom) => (
        <SuppliesSectionCard
          key={uom}
          title={`${C.compareTotalsTitle} — ${uom === "?" ? C.compareNoUm : uom}`}
          subtitle={C.compareHint}
        >
          <div className="sp-consumption-audit__table-wrap">
            <table className="sp-consumption-audit__materials-table">
              <thead>
                <tr>
                  <th scope="col">{C.compareColMetric}</th>
                  {items.map((item) => (
                    <th scope="col" key={item.production_order}>
                      {item.production_order}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metricRows.map((row) => (
                  <tr key={row.key}>
                    <td>{row.label}</td>
                    {items.map((item, itemIndex) => (
                      <td key={item.production_order}>
                        {formatQuantity(row.pick(totalsFor(itemIndex, uom)))}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SuppliesSectionCard>
      ))}

      {items.map((item) => (
        <SuppliesSectionCard
          key={item.production_order}
          title={C.suggestionFor(
            item.production_order,
            item.order?.product_code ?? "",
          )}
          subtitle={`${C.colStatus}: ${labelOf(C.statusLabels, item.order?.status ?? "")}`}
        >
          {item.operations.map((op) => (
            <div key={op.operation} className="sp-consumption-audit__compare-op">
              <h5>
                {C.operationTitle(op.operation, op.work_center || "—")}{" "}
                <SuppliesStatusBadge
                  label={labelOf(C.executionStates, op.execution_state)}
                  variant={executionBadgeVariant(op.execution_state)}
                />
              </h5>
              <div className="sp-consumption-audit__table-wrap">
                <table className="sp-consumption-audit__materials-table">
                  <thead>
                    <tr>
                      <th scope="col">{C.colComponent}</th>
                      <th scope="col">{C.colUm}</th>
                      <th scope="col">{C.colTheoretical}</th>
                      <th scope="col">{C.colCommitment}</th>
                      <th scope="col">{C.colDerived}</th>
                      <th scope="col">{C.colClassified}</th>
                      <th scope="col">{C.colDiscrepancy}</th>
                      <th scope="col">{C.colClassification}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {op.components.map((comp, idx) => (
                      <tr key={`${comp.component_code}-${idx}`}>
                        <td>
                          <div className="sp-consumption-audit__component-code">
                            {comp.component_code}
                          </div>
                          <div className="sp-consumption-audit__component-type">
                            {comp.component_description}
                          </div>
                        </td>
                        <td>{comp.unit_of_measure || "—"}</td>
                        <td>{formatQuantity(comp.theoretical_quantity)}</td>
                        <td>{formatQuantity(comp.original_commitment_quantity)}</td>
                        <td>{formatQuantity(comp.derived_consumption_quantity)}</td>
                        <td>{formatQuantity(comp.eligible_consumption_quantity)}</td>
                        <td>{formatQuantity(comp.difference)}</td>
                        <td>
                          <SuppliesStatusBadge
                            label={labelOf(C.classifications, comp.classification)}
                            variant={classificationBadgeVariant(comp.classification)}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
          <p className="sp-consumption-audit__meta">
            {C.qualityTitle}: {labelOf(
              { complete: C.qualityStatusComplete, partial: C.qualityStatusPartial },
              item.quality?.status ?? "",
            )}
            {item.unmatched_movements_count
              ? ` · ${item.unmatched_movements_count} ${C.unmatchedTitle.toLowerCase()}`
              : ""}
          </p>
        </SuppliesSectionCard>
      ))}
    </div>
  );
}

// ————————————————————————————————————————————————————————————
// Página
// ————————————————————————————————————————————————————————————

type ConsumptionAuditPageProps = {
  basePath: string;
};

export function ConsumptionAuditPage({ basePath }: ConsumptionAuditPageProps) {
  const [target, setTarget] = useState<ConsumptionAuditTarget | null>(() =>
    parseTargetFromSearch(readBrowserSearch()),
  );
  const [result, setResult] = useState<LoadState>(() => initialLoad(""));
  const [retryKey, setRetryKey] = useState(0);
  const [lastQueriedAt, setLastQueriedAt] = useState<Date | null>(null);

  // ——— Estado da pesquisa (F2/F3) ———
  const parsed = useMemo(() => parseFiltersFromSearch(readBrowserSearch()), []);
  const [unitDraft, setUnitDraft] = useState<string>(
    () => parseTargetFromSearch(readBrowserSearch())?.unit ?? parsed.unit ?? "01",
  );
  const [searchDraft, setSearchDraft] = useState<string>("");
  const [filters, setFilters] = useState<ConsumptionAuditFilterState>(
    () => parsed.filters,
  );
  const [listPage, setListPage] = useState(1);
  const [searchState, setSearchState] = useState<SearchState>({
    key: "",
    status: "idle",
    page: null,
    error: null,
  });
  const [suggestOpen, setSuggestOpen] = useState(false);
  const [suggestActive, setSuggestActive] = useState(-1);
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComparisonState>({
    status: "idle",
    data: null,
    error: null,
  });
  const [advancedOpen, setAdvancedOpen] = useState<boolean>(
    () => !filtersAreEmpty(parsed.filters),
  );
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const lastSearchKey = useRef("");

  // URL → estado: popstate re-sincroniza alvo e filtros.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const onPopState = () => {
      const browserSearch = readBrowserSearch();
      setTarget(parseTargetFromSearch(browserSearch));
      const parsedNow = parseFiltersFromSearch(browserSearch);
      setFilters(parsedNow.filters);
      if (parsedNow.unit) setUnitDraft(parsedNow.unit);
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const targetKey = target ? `${target.unit}|${target.productionOrder}` : "";

  // ——— Detalhe da OP ———
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
        setResult({ key, status: "error", data: null, error: mapFetchError(err) });
      });
    return () => controller.abort();
  }, [target, retryKey]);

  const resultState = result.key === targetKey ? result : initialLoad(targetKey);
  const loading = Boolean(target) && resultState.status === "loading";
  const data = resultState.data;

  // ——— Pesquisa automática: digitação ou filtros (debounce + cancel) ———
  const unit = normalizeUnit(unitDraft);
  const hasCriteria =
    Boolean(unit) &&
    (searchDraft.trim().length >= SEARCH_MIN_CHARS || !filtersAreEmpty(filters));

  useEffect(() => {
    if (!unit || !hasCriteria) {
      // O bloco de resultados é renderizado apenas quando hasCriteria —
      // estado obsoleto aqui nunca chega à tela.
      return undefined;
    }
    const key = JSON.stringify({ unit, searchDraft, filters, listPage });
    const timer = window.setTimeout(() => {
      const controller = new AbortController();
      lastSearchKey.current = key;
      setSearchState((prev) => ({
        key,
        status: "loading",
        page: prev.key === key ? prev.page : prev.page,
        error: null,
      }));
      searchConsumptionAuditOrders(
        {
          unit,
          search: searchDraft,
          dateType: filters.dateType,
          periodStart: filters.periodStart || undefined,
          periodEnd: filters.periodEnd || undefined,
          product: filters.product || undefined,
          status: filters.status || undefined,
          workCenter: filters.workCenter || undefined,
          operation: filters.operation || undefined,
          page: listPage,
          pageSize: SEARCH_PAGE_SIZE,
        },
        controller.signal,
      )
        .then((page) => {
          if (lastSearchKey.current !== key) return;
          setSearchState({ key, status: "ready", page, error: null });
          setSuggestActive(-1);
          // Filtros relevantes na URL — replaceState (sem poluir o histórico).
          if (typeof window !== "undefined") {
            const qs = buildSearchQuery(unit, filters, searchDraft);
            window.history.replaceState(
              null,
              "",
              `${window.location.pathname}${qs}`,
            );
          }
        })
        .catch((err: unknown) => {
          if (controller.signal.aborted || lastSearchKey.current !== key) return;
          setSearchState({
            key,
            status: "error",
            page: null,
            error: mapFetchError(err),
          });
        });
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [unit, searchDraft, filters, listPage, hasCriteria]);

  const selectOrder = useCallback(
    (op: string) => {
      if (!unit) return;
      setSuggestOpen(false);
      const next: ConsumptionAuditTarget = {
        unit,
        productionOrder: op,
      };
      navigatePluginPath(
        `${buildPluginPath("consumption_audit", basePath)}${buildTargetSearch(next)}`,
      );
    },
    [unit, basePath],
  );

  const toggleSelect = useCallback((op: string) => {
    setSelected((prev) => {
      if (prev.includes(op)) return prev.filter((x) => x !== op);
      if (prev.length >= COMPARE_MAX) return prev;
      return [...prev, op];
    });
  }, []);

  const resultColumns = useMemo(
    (): DataTableColumn<ConsumptionAuditOrderSummary>[] => [
      {
        key: "compare",
        header: "",
        align: "center",
        interactive: true,
        render: (item) => (
          <SuppliesFilterCheckbox
            aria-label={`${C.compareSelect} ${item.production_order}`}
            checked={selected.includes(item.production_order)}
            disabled={
              !selected.includes(item.production_order) &&
              selected.length >= COMPARE_MAX
            }
            onChange={() => toggleSelect(item.production_order)}
          />
        ),
      },
      {
        key: "order",
        header: C.colOrder,
        render: (item) => <strong>{item.production_order}</strong>,
      },
      {
        key: "product",
        header: C.colProduct,
        render: (item) => (
          <>
            {item.product_code}
            {item.product_description
              ? ` · ${item.product_description}`
              : ""}
          </>
        ),
      },
      {
        key: "status",
        header: C.colStatus,
        render: (item) => labelOf(C.statusLabels, item.status),
      },
      {
        key: "emission",
        header: C.colEmission,
        render: (item) => formatDatePtBr(item.emission_date),
      },
      {
        key: "finished",
        header: C.colFinished,
        render: (item) => formatDatePtBr(item.finished_at),
      },
      {
        key: "planned",
        header: C.colPlanned,
        align: "right",
        render: (item) =>
          `${formatQuantity(item.planned_quantity, 3)} ${item.unit_of_measure}`,
      },
    ],
    [selected, toggleSelect],
  );

  const runComparison = useCallback(() => {
    if (!unit || selected.length < 2 || selected.length > COMPARE_MAX) return;
    setComparison({ status: "loading", data: null, error: null });
    getConsumptionAuditComparison(unit, selected)
      .then((cmp) =>
        setComparison({ status: "ready", data: cmp, error: null }),
      )
      .catch((err: unknown) =>
        setComparison({
          status: "error",
          data: null,
          error: mapFetchError(err),
        }),
      );
  }, [unit, selected]);

  const onSearchKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    const items = searchState.page?.items ?? [];
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setSuggestOpen(true);
      setSuggestActive((i) => Math.min(i + 1, items.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setSuggestActive((i) => Math.max(i - 1, -1));
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (suggestActive >= 0 && items[suggestActive]) {
        selectOrder(items[suggestActive].production_order);
      } else if (isValidProductionOrder(searchDraft.trim().toUpperCase()) && unit) {
        selectOrder(searchDraft.trim().toUpperCase());
      }
    } else if (event.key === "Escape") {
      setSuggestOpen(false);
      setSuggestActive(-1);
    }
  };

  const unitOptions = useMemo(
    () => [
      { value: "01", label: formatSuppliesUnitName("01") },
      { value: "02", label: formatSuppliesUnitName("02") },
    ],
    [],
  );
  const dateTypeOptions = useMemo(
    () =>
      (["emission", "appointment", "finished"] as ConsumptionAuditDateType[]).map(
        (value) => ({ value, label: C.dateTypes[value] }),
      ),
    [],
  );
  const statusOptions = useMemo(
    () => [
      { value: "", label: C.statusAllLabel },
      ...Object.entries(C.statusLabels).map(([value, label]) => ({
        value,
        label,
      })),
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

  const suggestions =
    suggestOpen && hasCriteria ? (searchState.page?.items ?? []) : [];
  const searchReady =
    hasCriteria && searchState.status === "ready" && searchState.page;
  const searchEmpty =
    hasCriteria &&
    searchState.status === "ready" &&
    !searchState.page?.items.length;

  // ——— Período rápido (Bloco B) ———
  const activePeriodPreset = useMemo(
    () => matchSuppliesQuickPeriod(filters.periodStart, filters.periodEnd),
    [filters.periodStart, filters.periodEnd],
  );
  const periodIsSet = Boolean(filters.periodStart || filters.periodEnd);

  const applyQuickPeriod = useCallback(
    (preset: SuppliesQuickPeriodId) => {
      if (preset === "custom") return;
      const range = resolveSuppliesQuickPeriod(preset);
      if (!range) return;
      setFilters((f) => ({ ...f, periodStart: range.from, periodEnd: range.to }));
      setListPage(1);
    },
    [],
  );

  const clearPeriod = useCallback(() => {
    setFilters((f) => ({ ...f, periodStart: "", periodEnd: "" }));
    setListPage(1);
  }, []);

  const { FiltersRow } = spFiltersKit;

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
      />

      <form
        className="sp-list-filters sp-consumption-audit__filters-form"
        onSubmit={(event) => event.preventDefault()}
        aria-label={C.filtersAriaLabel}
      >
        <SuppliesFilterBarShell
          embedded
          ariaLabel={C.filtersAriaLabel}
          leading={
            <div className="sp-filter-bar__period-block">
              <div className="sp-filter-bar__header">
                <div className="sp-filter-bar__title">
                  <Filter size={18} aria-hidden="true" />
                  <h2>
                    <SuppliesSectionHintLabel
                      label={C.searchTitle}
                      hint={SP_HELP.consumptionAuditQuery}
                    />
                  </h2>
                </div>
                {!filtersAreEmpty(filters) ? (
                  <div className="sp-filter-bar__header-actions">
                    <SuppliesClearFiltersButton
                      density="compact"
                      label={C.clearFilters}
                      onClick={() => {
                        setFilters(EMPTY_FILTERS);
                        setListPage(1);
                      }}
                    />
                  </div>
                ) : null}
              </div>

              {/* Bloco A — busca principal */}
              <FiltersRow variant="extended">
                <SuppliesSelectField
                  label={C.unitLabel}
                  hint={C.searchHint}
                  value={unitDraft}
                  options={unitOptions}
                  onChange={(value) => {
                    setUnitDraft(value);
                    setSelected([]);
                  }}
                />
                <div className="sp-consumption-audit__combobox sp-field">
                  <label className="sp-field__label" htmlFor="ca-op-search">
                    {C.opLabel}
                  </label>
                  <input
                    id="ca-op-search"
                    ref={searchInputRef}
                    className="sp-field__control"
                    type="search"
                    role="combobox"
                    aria-expanded={suggestOpen && suggestions.length > 0}
                    aria-controls="ca-op-suggestions"
                    aria-activedescendant={
                      suggestActive >= 0
                        ? `ca-suggestion-${suggestActive}`
                        : undefined
                    }
                    aria-autocomplete="list"
                    autoComplete="off"
                    value={searchDraft}
                    placeholder={C.searchPlaceholder}
                    onChange={(event) => {
                      setSearchDraft(event.target.value.toUpperCase());
                      setSuggestOpen(true);
                      setListPage(1);
                    }}
                    onFocus={() => setSuggestOpen(true)}
                    onKeyDown={onSearchKeyDown}
                  />
                  {suggestOpen && searchState.status === "loading" ? (
                    <div className="sp-consumption-audit__suggestions-status">
                      {C.searchLoading}
                    </div>
                  ) : null}
                  {suggestOpen && suggestions.length ? (
                    <ul
                      id="ca-op-suggestions"
                      role="listbox"
                      className="sp-consumption-audit__suggestions"
                    >
                      {suggestions.map((item, index) => (
                        <li
                          key={item.production_order}
                          id={`ca-suggestion-${index}`}
                          role="option"
                          aria-selected={index === suggestActive}
                          className={
                            index === suggestActive
                              ? "sp-consumption-audit__suggestion is-active"
                              : "sp-consumption-audit__suggestion"
                          }
                          onMouseDown={(event) => {
                            event.preventDefault();
                            selectOrder(item.production_order);
                          }}
                        >
                          <strong>{item.production_order}</strong>
                          <span>
                            {item.product_code}
                            {item.product_description
                              ? ` · ${item.product_description}`
                              : ""}
                          </span>
                          <span className="sp-consumption-audit__suggestion-meta">
                            {formatDatePtBr(item.emission_date)} ·{" "}
                            {labelOf(C.statusLabels, item.status)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              </FiltersRow>

              {/* Bloco B — ações rápidas de período */}
              <div className="sp-consumption-audit__period-presets">
                <div className="sp-consumption-audit__period-presets-head">
                  <SuppliesSectionHintLabel
                    label={C.quickPeriodLabel}
                    hint={C.quickPeriodHint}
                  />
                  <SuppliesActionButton
                    type="button"
                    variant="default"
                    disabled={!periodIsSet}
                    onClick={clearPeriod}
                  >
                    {C.clearPeriod}
                  </SuppliesActionButton>
                </div>
                <SuppliesSegmentToggle
                  ariaLabel={C.quickPeriodLabel}
                  idPrefix="ca-period-preset"
                  size="sm"
                  value={activePeriodPreset}
                  onChange={(value) =>
                    applyQuickPeriod(value as SuppliesQuickPeriodId)
                  }
                  options={SUPPLIES_QUICK_PERIOD_OPTIONS}
                />
              </div>
            </div>
          }
        >
          {null}
        </SuppliesFilterBarShell>

        {/* Bloco C — filtros avançados */}
        <details
          className="sp-consumption-audit__advanced"
          open={advancedOpen}
          onToggle={(event) =>
            setAdvancedOpen(event.currentTarget.open)
          }
        >
          <summary>
            <SuppliesSectionHintLabel
              label={C.advancedFiltersTitle}
              hint={C.filtersHint}
            />
          </summary>
          <FiltersRow variant="extended">
            <SuppliesSelectField
              label={C.dateTypeLabel}
              value={filters.dateType}
              options={dateTypeOptions}
              onChange={(value) => {
                setFilters((f) => ({
                  ...f,
                  dateType: value as ConsumptionAuditDateType,
                }));
                setListPage(1);
              }}
            />
            <SuppliesDateField
              label={C.periodStartLabel}
              value={filters.periodStart}
              onChange={(value) => {
                setFilters((f) => ({ ...f, periodStart: value }));
                setListPage(1);
              }}
            />
            <SuppliesDateField
              label={C.periodEndLabel}
              value={filters.periodEnd}
              onChange={(value) => {
                setFilters((f) => ({ ...f, periodEnd: value }));
                setListPage(1);
              }}
            />
            <SuppliesTextField
              label={C.productLabel}
              value={filters.product}
              onChange={(value) => {
                setFilters((f) => ({ ...f, product: value }));
                setListPage(1);
              }}
              placeholder={C.productPlaceholder}
            />
            <SuppliesSelectField
              label={C.statusFilterLabel}
              value={filters.status}
              options={statusOptions}
              onChange={(value) => {
                setFilters((f) => ({ ...f, status: value }));
                setListPage(1);
              }}
            />
            <SuppliesTextField
              label={C.workCenterLabel}
              value={filters.workCenter}
              onChange={(value) => {
                setFilters((f) => ({ ...f, workCenter: value }));
                setListPage(1);
              }}
              placeholder={C.workCenterPlaceholder}
            />
            <SuppliesTextField
              label={C.operationLabel}
              value={filters.operation}
              onChange={(value) => {
                setFilters((f) => ({ ...f, operation: value }));
                setListPage(1);
              }}
              placeholder={C.operationPlaceholder}
            />
          </FiltersRow>
        </details>
      </form>

      {/* ——— Lista de resultados (F3) ——— */}
      {!hasCriteria && !target ? (
        <SuppliesEmptyState
          title={C.emptyTitle}
          message={C.searchMinChars(SEARCH_MIN_CHARS)}
        />
      ) : null}

      {hasCriteria && searchState.status === "loading" ? (
        <SuppliesLoadingCard title={C.searchLoading} variant="panel" />
      ) : null}

      {hasCriteria && searchState.status === "error" ? (
        <SuppliesStateBanner variant="error">
          {searchState.error ?? C.error}
        </SuppliesStateBanner>
      ) : null}

      {searchReady && searchState.page ? (
        <SuppliesSectionCard
          title={C.searchResultsTitle}
          subtitle={C.searchResultsSubtitle(searchState.page.total)}
        >
          {searchState.page.items.length ? (
            <>
              <div
                className="sp-list-table-region"
                role="region"
                aria-label={C.searchResultsTitle}
                tabIndex={0}
              >
                <SuppliesDataTable
                  layout="section"
                  columns={resultColumns}
                  rows={searchState.page.items}
                  rowKey={(item) => item.production_order}
                  onRowClick={(item) => selectOrder(item.production_order)}
                  getRowClassName={(item) =>
                    selected.includes(item.production_order)
                      ? "is-selected"
                      : undefined
                  }
                />
              </div>
              <SuppliesCompactPagination
                page={searchState.page.page}
                pageSize={searchState.page.page_size}
                total={searchState.page.total}
                totalPages={Math.max(1, searchState.page.total_pages)}
                onPageChange={setListPage}
              />
            </>
          ) : (
            <p className="sp-consumption-audit__note">{C.searchEmpty}</p>
          )}

          <div className="sp-consumption-audit__compare-bar">
            <SuppliesActionButton
              type="button"
              variant="primary"
              disabled={selected.length < 2 || selected.length > COMPARE_MAX || comparison.status === "loading"}
              onClick={runComparison}
            >
              {comparison.status === "loading"
                ? C.compareLoading
                : C.compareAction(selected.length)}
            </SuppliesActionButton>
            <span className="sp-consumption-audit__note">
              {selected.length >= COMPARE_MAX
                ? C.compareMaxReached
                : C.compareMinMax}
            </span>
          </div>
        </SuppliesSectionCard>
      ) : null}

      {searchEmpty ? (
        <SuppliesStateBanner variant="default">{C.searchEmpty}</SuppliesStateBanner>
      ) : null}

      {/* ——— Comparação (F4) ——— */}
      {comparison.status === "ready" && comparison.data ? (
        <>
          <h2 className="sp-consumption-audit__section-heading">
            {C.compareTitle}
          </h2>
          <ComparisonSection data={comparison.data} />
        </>
      ) : null}
      {comparison.status === "error" ? (
        <SuppliesStateBanner variant="error">
          {comparison.error ?? C.error}
        </SuppliesStateBanner>
      ) : null}

      {/* ——— Detalhe da OP selecionada ——— */}
      {target && loading ? (
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
                        const relUnit = normalizeUnit(data.branch);
                        if (!relUnit) return;
                        navigatePluginPath(
                          `${buildPluginPath("consumption_audit", basePath)}${buildTargetSearch({ unit: relUnit, productionOrder: rel.production_order })}`,
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
