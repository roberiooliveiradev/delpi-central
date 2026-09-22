import {
  createDashboardLoadingActivityCard,
  createDashboardStatusBadge,
  DataTable,
  dataTableBemClasses,
  NavigationCard,
  navigationCardBemClasses,
} from "@delpi/plugin-ui/index";
import { Layers, Search, X } from "lucide-react";
import { useEffect, useId, useMemo, useState } from "react";

import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useProblemAnalysis } from "../hooks/useProblemAnalysis";
import type {
  IncompleteOrderSetItem,
  OrderSetComponent,
  PpcBranch,
  ProblemDetector,
  ProblemDetectorItem,
  QuantityMismatchComponent,
  QuantityMismatchOrderSetItem,
  SharedStructureIntermediateItem,
  UncoveredDemandItem,
} from "../types";
import { demandStatusBadge } from "../utils/demandStatus";
import { filterIncompleteSetsByRootProduct } from "../utils/filterIncompleteSetsByRootProduct";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });

const QUANTITY_DETECTOR_ID = "order-set-quantity-mismatches";
const DEMAND_DETECTOR_ID = "uncovered-demand-lines";
const SHARED_DETECTOR_ID = "shared-structure-intermediates";

const tableClassNames = dataTableBemClasses("ppc");
const navCardClassNames = navigationCardBemClasses("ppc");

const LoadingCard = createDashboardLoadingActivityCard({
  prefix: "ppc",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.problemAnalysis.loading,
  },
});

const severityLabel: Record<string, string> = {
  critical: copy.problemAnalysis.critical,
  attention: copy.problemAnalysis.attention,
  ok: copy.problemAnalysis.ok,
};

function metricNumber(metrics: Record<string, number | string | null>, key: string): number {
  const value = metrics[key];
  return typeof value === "number" ? value : Number(value ?? 0) || 0;
}

function isQuantityDetector(detectorId: string | null): boolean {
  return detectorId === QUANTITY_DETECTOR_ID;
}

function isDemandDetector(detectorId: string | null): boolean {
  return detectorId === DEMAND_DETECTOR_ID;
}

function isSharedDetector(detectorId: string | null): boolean {
  return detectorId === SHARED_DETECTOR_ID;
}

function detectorMeta(detector: ProblemDetector): string {
  if (isSharedDetector(detector.id)) {
    const sets = copy.problemAnalysis.sharedStructure;
    return [
      sets.breakdown(
        metricNumber(detector.metrics, "shared_intermediate_count"),
        metricNumber(detector.metrics, "max_shared_pa_count"),
      ),
      sets.checked(metricNumber(detector.metrics, "checked_pa_count")),
    ].join(" · ");
  }
  if (isDemandDetector(detector.id)) {
    const sets = copy.problemAnalysis.uncoveredDemand;
    return [
      sets.breakdown(
        metricNumber(detector.metrics, "uncovered_line_count"),
        metricNumber(detector.metrics, "late_op_line_count"),
      ),
      sets.checked(metricNumber(detector.metrics, "checked_line_count")),
    ].join(" · ");
  }
  if (isQuantityDetector(detector.id)) {
    const sets = copy.problemAnalysis.quantityMismatches;
    return [
      sets.breakdown(
        metricNumber(detector.metrics, "under_set_count"),
        metricNumber(detector.metrics, "over_set_count"),
      ),
      sets.checked(metricNumber(detector.metrics, "checked_set_count")),
    ].join(" · ");
  }
  const sets = copy.problemAnalysis.incompleteSets;
  return [
    sets.breakdown(
      metricNumber(detector.metrics, "missing_set_count"),
      metricNumber(detector.metrics, "extra_set_count"),
    ),
    sets.checked(metricNumber(detector.metrics, "checked_set_count")),
  ].join(" · ");
}

function componentLine(component: OrderSetComponent): string {
  const sets = copy.problemAnalysis.incompleteSets;
  const detail = component.production_order
    ? sets.componentOrder(component.production_order)
    : component.bom_level
      ? sets.componentLevel(component.bom_level)
      : null;
  const name = component.description
    ? `${component.product_code} — ${component.description}`
    : component.product_code;
  return detail ? `${name} (${detail})` : name;
}

function quantityComponentLine(component: QuantityMismatchComponent): string {
  const sets = copy.problemAnalysis.quantityMismatches;
  const name = component.description
    ? `${component.product_code} — ${component.description}`
    : component.product_code;
  const qty = sets.qtyDetail(
    formatOpQuantity(component.expected_quantity),
    formatOpQuantity(component.actual_quantity),
  );
  const order = component.production_order
    ? sets.componentOrder(component.production_order)
    : component.bom_level
      ? sets.componentLevel(component.bom_level)
      : null;
  return order ? `${name} (${qty} · ${order})` : `${name} (${qty})`;
}

function demandIssueDetail(row: UncoveredDemandItem): string | null {
  const sets = copy.problemAnalysis.uncoveredDemand;
  if (row.issue_kind === "uncovered" && row.uncovered_quantity > 0) {
    return `${sets.uncoveredLabel} ${sets.qtyUncovered(formatOpQuantity(row.uncovered_quantity))}`;
  }
  if (row.issue_kind === "late_op") {
    const when = formatIsoDate(row.coverage_date);
    return when
      ? `${sets.lateOpLabel} ${sets.coverageDate(when)}`
      : sets.lateOpLabel;
  }
  return null;
}

function isIncompleteItem(item: ProblemDetectorItem): item is IncompleteOrderSetItem {
  return "missing_components" in item;
}

function isQuantityItem(item: ProblemDetectorItem): item is QuantityMismatchOrderSetItem {
  return "under_components" in item;
}

function isDemandItem(item: ProblemDetectorItem): item is UncoveredDemandItem {
  return "issue_kind" in item;
}

function isSharedItem(item: ProblemDetectorItem): item is SharedStructureIntermediateItem {
  return "shared_pa_count" in item && "finished_products" in item;
}

function sharedProductCodes(
  products: SharedStructureIntermediateItem["finished_products"],
): string {
  return products
    .map((product) => product.product_code)
    .filter(Boolean)
    .join(" · ");
}

type ProblemAnalysisPageProps = {
  branch: PpcBranch;
  detectorId: string | null;
};

export function ProblemAnalysisPage({ branch, detectorId }: ProblemAnalysisPageProps) {
  const { detectors, items, activeId, loading, itemsLoading, error, reload } = useProblemAnalysis(
    branch,
    detectorId,
  );
  const [rootQuery, setRootQuery] = useState("");
  const rootFilterId = useId();

  const cards = detectors?.detectors ?? [];
  const quantityMode = isQuantityDetector(activeId);
  const demandMode = isDemandDetector(activeId);
  const sharedMode = isSharedDetector(activeId);
  const demandCopy = copy.problemAnalysis.uncoveredDemand;
  const quantityCopy = copy.problemAnalysis.quantityMismatches;
  const incompleteCopy = copy.problemAnalysis.incompleteSets;
  const sharedCopy = copy.problemAnalysis.sharedStructure;
  const sets = sharedMode
    ? sharedCopy
    : demandMode
      ? demandCopy
      : quantityMode
        ? quantityCopy
        : incompleteCopy;
  const titleHint = sharedMode
    ? helpTooltips.sharedStructureIntermediates
    : demandMode
      ? helpTooltips.uncoveredDemand
      : quantityMode
        ? helpTooltips.quantityMismatches
        : activeId === "incomplete-order-sets"
          ? helpTooltips.incompleteOrderSets
          : helpTooltips.problemAnalysis;

  const allRows = (items?.items ?? []) as ProblemDetectorItem[];
  const rows = useMemo(
    () => filterIncompleteSetsByRootProduct(allRows, rootQuery),
    [allRows, rootQuery],
  );
  const rootFilterActive = rootQuery.trim().length > 0;

  useEffect(() => {
    setRootQuery("");
  }, [activeId, branch]);

  const openDetector = (id: string) => {
    navigatePpc(buildPpcHref({ subpluginId: "problem-analysis", branch, detectorId: id }));
  };

  return (
    <div className="ppc-page-stack">
      <PpcWorkspaceHeader
        title={copy.problemAnalysis.title}
        subtitle={copy.problemAnalysis.subtitle}
        titleHint={titleHint}
        branch={branch}
        subpluginId="problem-analysis"
        detectorId={activeId}
        onRefresh={reload}
      />

      {loading && !detectors ? (
        <LoadingCard
          title={copy.problemAnalysis.loading}
          description={copy.problemAnalysis.loadingHint}
        />
      ) : null}

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error || copy.problemAnalysis.loadError}
        </div>
      ) : null}

      {detectors ? (
        <div className="ppc-detectors">
          <section
            className="ppc-detectors__grid"
            aria-label={copy.problemAnalysis.detectorsAria}
          >
            {cards.length === 0 ? (
              <div className="ppc-state">{copy.problemAnalysis.noDetectors}</div>
            ) : (
              cards.map((detector) => (
                <div
                  key={detector.id}
                  className="ppc-detector-card"
                  data-severity={detector.severity}
                  data-active={detector.id === activeId ? "true" : undefined}
                >
                  <NavigationCard
                    classNames={navCardClassNames}
                    icon={<Layers size={20} strokeWidth={1.75} />}
                    eyebrow={`${severityLabel[detector.severity] ?? ""} · ${
                      detector.count > 0
                        ? copy.problemAnalysis.detectorCount(detector.count)
                        : copy.problemAnalysis.detectorClear
                    }`}
                    title={detector.title}
                    description={detector.description}
                    meta={detectorMeta(detector)}
                    onClick={() => openDetector(detector.id)}
                  />
                </div>
              ))
            )}
          </section>

          <section className="ppc-detector-items" aria-label={items?.detector.title ?? ""}>
            {items?.detector.action_hint ? (
              <p className="ppc-detector-items__hint">{items.detector.action_hint}</p>
            ) : null}

            <form
              className="ppc-detector-filter"
              role="search"
              aria-label={sets.rootFilterAria}
              onSubmit={(event) => event.preventDefault()}
            >
              <label className="ppc-detector-filter__label" htmlFor={rootFilterId}>
                {sets.rootFilterLabel}
              </label>
              <div className="ppc-detector-filter__field">
                <Search
                  size={16}
                  strokeWidth={1.75}
                  aria-hidden
                  className="ppc-detector-filter__icon"
                />
                <input
                  id={rootFilterId}
                  type="search"
                  value={rootQuery}
                  onChange={(event) => setRootQuery(event.target.value)}
                  placeholder={sets.rootFilterPlaceholder}
                  autoComplete="off"
                  spellCheck={false}
                />
                {rootFilterActive ? (
                  <button
                    type="button"
                    className="ppc-detector-filter__clear"
                    onClick={() => setRootQuery("")}
                    title={sets.rootFilterClear}
                  >
                    <X size={16} strokeWidth={1.75} aria-hidden />
                    <span className="ppc-sr-only">{sets.rootFilterClear}</span>
                  </button>
                ) : null}
              </div>
            </form>

            {sharedMode ? (
              <DataTable<SharedStructureIntermediateItem>
                columns={[
                  {
                    key: "intermediate",
                    header: sharedCopy.columns.intermediate,
                    render: (row) => (
                      <span className="ppc-detector-items__root">
                        <strong>{row.intermediate_code ?? "—"}</strong>
                        {row.intermediate_description ? (
                          <span>{row.intermediate_description}</span>
                        ) : null}
                      </span>
                    ),
                  },
                  {
                    key: "type",
                    header: sharedCopy.columns.type,
                    render: (row) => row.intermediate_type || "—",
                  },
                  {
                    key: "pas",
                    header: sharedCopy.columns.pas,
                    align: "right",
                    render: (row) => row.shared_pa_count,
                  },
                  {
                    key: "products",
                    header: sharedCopy.columns.products,
                    render: (row) => sharedProductCodes(row.finished_products) || "—",
                  },
                ]}
                rows={rows.filter(isSharedItem)}
                rowKey={(row) => row.id}
                classNames={tableClassNames}
                labels={{
                  emptyMessage: rootFilterActive
                    ? sharedCopy.emptyFilter(rootQuery.trim())
                    : sharedCopy.empty,
                  loadingMessage: copy.problemAnalysis.itemsLoading,
                  sortByAriaLabel: copy.table.sort,
                  headerHelpAriaLabel: copy.table.help,
                }}
                loading={itemsLoading}
                layout="embedded"
              />
            ) : demandMode ? (
              <DataTable<UncoveredDemandItem>
                columns={[
                  {
                    key: "order",
                    header: demandCopy.columns.order,
                    render: (row) => (
                      <span className="ppc-detector-items__set">
                        <strong>
                          {row.sales_order && row.line_item
                            ? `${row.sales_order}/${row.line_item}`
                            : row.sales_order || "—"}
                        </strong>
                        {row.customer_order ? <span>{row.customer_order}</span> : null}
                      </span>
                    ),
                  },
                  {
                    key: "product",
                    header: demandCopy.columns.product,
                    render: (row) => {
                      const detail = demandIssueDetail(row);
                      return (
                        <span className="ppc-detector-items__root">
                          <strong>{row.product_code ?? "—"}</strong>
                          {detail ? (
                            <span className="ppc-detector-items__diff">{detail}</span>
                          ) : null}
                        </span>
                      );
                    },
                  },
                  {
                    key: "customer",
                    header: demandCopy.columns.customer,
                    render: (row) => row.customer_name || "—",
                  },
                  {
                    key: "due",
                    header: demandCopy.columns.due,
                    render: (row) => (
                      <span className="ppc-demand__due">
                        <strong>{formatIsoDate(row.due_date) || "—"}</strong>
                        {row.days_late > 0 ? (
                          <span>{copy.demand.lateBadge(row.days_late)}</span>
                        ) : null}
                      </span>
                    ),
                  },
                  {
                    key: "open",
                    header: demandCopy.columns.open,
                    align: "right",
                    render: (row) => formatOpQuantity(row.open_quantity),
                  },
                  {
                    key: "uncovered",
                    header: demandCopy.columns.uncovered,
                    align: "right",
                    render: (row) => formatOpQuantity(row.uncovered_quantity),
                  },
                  {
                    key: "status",
                    header: copy.demand.columns.status,
                    render: (row) => {
                      const badge = demandStatusBadge(row.status);
                      return <StatusBadge label={badge.label} variant={badge.variant} />;
                    },
                  },
                ]}
                rows={rows.filter(isDemandItem)}
                rowKey={(row) => row.id}
                classNames={tableClassNames}
                labels={{
                  emptyMessage: rootFilterActive
                    ? demandCopy.emptyFilter(rootQuery.trim())
                    : demandCopy.empty,
                  loadingMessage: copy.problemAnalysis.itemsLoading,
                  sortByAriaLabel: copy.table.sort,
                  headerHelpAriaLabel: copy.table.help,
                }}
                loading={itemsLoading}
                layout="embedded"
              />
            ) : quantityMode ? (
              <DataTable<QuantityMismatchOrderSetItem>
                columns={[
                  {
                    key: "set",
                    header: quantityCopy.columns.set,
                    render: (row) => (
                      <span className="ppc-detector-items__set">
                        <strong>{row.set_key ?? "—"}</strong>
                        <span>
                          {quantityCopy.openOrders(row.open_order_count, row.order_count)}
                        </span>
                      </span>
                    ),
                  },
                  {
                    key: "root",
                    header: quantityCopy.columns.root,
                    render: (row) => (
                      <span className="ppc-detector-items__root">
                        <strong>{row.root_code ?? "—"}</strong>
                        {row.root_description ? <span>{row.root_description}</span> : null}
                        <span className="ppc-detector-items__diff">
                          OP mãe: {formatOpQuantity(row.root_quantity)}
                        </span>
                        {row.under_components.length > 0 ? (
                          <span className="ppc-detector-items__diff">
                            {quantityCopy.underLabel}{" "}
                            {row.under_components.map(quantityComponentLine).join(" · ")}
                          </span>
                        ) : null}
                        {row.over_components.length > 0 ? (
                          <span className="ppc-detector-items__diff">
                            {quantityCopy.overLabel}{" "}
                            {row.over_components.map(quantityComponentLine).join(" · ")}
                          </span>
                        ) : null}
                      </span>
                    ),
                  },
                  {
                    key: "due",
                    header: quantityCopy.columns.due,
                    render: (row) => formatIsoDate(row.due_date) || "—",
                  },
                  {
                    key: "orders",
                    header: quantityCopy.columns.orders,
                    align: "right",
                    render: (row) => row.order_count,
                  },
                  {
                    key: "under",
                    header: quantityCopy.columns.under,
                    align: "right",
                    render: (row) => row.under_count,
                  },
                  {
                    key: "over",
                    header: quantityCopy.columns.over,
                    align: "right",
                    render: (row) => row.over_count,
                  },
                ]}
                rows={rows.filter(isQuantityItem)}
                rowKey={(row) => row.id}
                classNames={tableClassNames}
                labels={{
                  emptyMessage: rootFilterActive
                    ? quantityCopy.emptyFilter(rootQuery.trim())
                    : quantityCopy.empty,
                  loadingMessage: copy.problemAnalysis.itemsLoading,
                  sortByAriaLabel: copy.table.sort,
                  headerHelpAriaLabel: copy.table.help,
                }}
                loading={itemsLoading}
                layout="embedded"
              />
            ) : (
              <DataTable<IncompleteOrderSetItem>
                columns={[
                  {
                    key: "set",
                    header: incompleteCopy.columns.set,
                    render: (row) => (
                      <span className="ppc-detector-items__set">
                        <strong>{row.set_key ?? "—"}</strong>
                        <span>
                          {incompleteCopy.openOrders(row.open_order_count, row.order_count)}
                        </span>
                      </span>
                    ),
                  },
                  {
                    key: "root",
                    header: incompleteCopy.columns.root,
                    render: (row) => (
                      <span className="ppc-detector-items__root">
                        <strong>{row.root_code ?? "—"}</strong>
                        {row.root_description ? <span>{row.root_description}</span> : null}
                        {row.missing_components.length > 0 ? (
                          <span className="ppc-detector-items__diff">
                            {incompleteCopy.missingLabel}{" "}
                            {row.missing_components.map(componentLine).join(" · ")}
                          </span>
                        ) : null}
                        {row.extra_components.length > 0 ? (
                          <span className="ppc-detector-items__diff">
                            {incompleteCopy.extraLabel}{" "}
                            {row.extra_components.map(componentLine).join(" · ")}
                          </span>
                        ) : null}
                      </span>
                    ),
                  },
                  {
                    key: "due",
                    header: incompleteCopy.columns.due,
                    render: (row) => formatIsoDate(row.due_date) || "—",
                  },
                  {
                    key: "orders",
                    header: incompleteCopy.columns.orders,
                    align: "right",
                    render: (row) => row.order_count,
                  },
                  {
                    key: "missing",
                    header: incompleteCopy.columns.missing,
                    align: "right",
                    render: (row) => row.missing_count,
                  },
                  {
                    key: "extra",
                    header: incompleteCopy.columns.extra,
                    align: "right",
                    render: (row) => row.extra_count,
                  },
                ]}
                rows={rows.filter(isIncompleteItem)}
                rowKey={(row) => row.id}
                classNames={tableClassNames}
                labels={{
                  emptyMessage: rootFilterActive
                    ? incompleteCopy.emptyFilter(rootQuery.trim())
                    : incompleteCopy.empty,
                  loadingMessage: copy.problemAnalysis.itemsLoading,
                  sortByAriaLabel: copy.table.sort,
                  headerHelpAriaLabel: copy.table.help,
                }}
                loading={itemsLoading}
                layout="embedded"
              />
            )}
            {!itemsLoading && rows.length === 0 ? (
              <p className="ppc-detector-items__empty">
                {rootFilterActive
                  ? sets.emptyFilter(rootQuery.trim())
                  : sets.emptyHint}
              </p>
            ) : null}
          </section>
        </div>
      ) : null}
    </div>
  );
}
