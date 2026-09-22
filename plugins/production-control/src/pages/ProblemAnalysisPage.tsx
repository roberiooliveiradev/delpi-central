import {
  createDashboardLoadingActivityCard,
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
} from "../types";
import { filterIncompleteSetsByRootProduct } from "../utils/filterIncompleteSetsByRootProduct";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

const QUANTITY_DETECTOR_ID = "order-set-quantity-mismatches";

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

function detectorMeta(detector: ProblemDetector): string {
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

function isIncompleteItem(item: ProblemDetectorItem): item is IncompleteOrderSetItem {
  return "missing_components" in item;
}

function isQuantityItem(item: ProblemDetectorItem): item is QuantityMismatchOrderSetItem {
  return "under_components" in item;
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
  const sets = quantityMode
    ? copy.problemAnalysis.quantityMismatches
    : copy.problemAnalysis.incompleteSets;
  const titleHint = quantityMode
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

            {quantityMode ? (
              <DataTable<QuantityMismatchOrderSetItem>
                columns={[
                  {
                    key: "set",
                    header: sets.columns.set,
                    render: (row) => (
                      <span className="ppc-detector-items__set">
                        <strong>{row.set_key ?? "—"}</strong>
                        <span>{sets.openOrders(row.open_order_count, row.order_count)}</span>
                      </span>
                    ),
                  },
                  {
                    key: "root",
                    header: sets.columns.root,
                    render: (row) => (
                      <span className="ppc-detector-items__root">
                        <strong>{row.root_code ?? "—"}</strong>
                        {row.root_description ? <span>{row.root_description}</span> : null}
                        <span className="ppc-detector-items__diff">
                          OP mãe: {formatOpQuantity(row.root_quantity)}
                        </span>
                        {row.under_components.length > 0 ? (
                          <span className="ppc-detector-items__diff">
                            {copy.problemAnalysis.quantityMismatches.underLabel}{" "}
                            {row.under_components.map(quantityComponentLine).join(" · ")}
                          </span>
                        ) : null}
                        {row.over_components.length > 0 ? (
                          <span className="ppc-detector-items__diff">
                            {copy.problemAnalysis.quantityMismatches.overLabel}{" "}
                            {row.over_components.map(quantityComponentLine).join(" · ")}
                          </span>
                        ) : null}
                      </span>
                    ),
                  },
                  {
                    key: "due",
                    header: sets.columns.due,
                    render: (row) => formatIsoDate(row.due_date) || "—",
                  },
                  {
                    key: "orders",
                    header: sets.columns.orders,
                    align: "right",
                    render: (row) => row.order_count,
                  },
                  {
                    key: "under",
                    header: copy.problemAnalysis.quantityMismatches.columns.under,
                    align: "right",
                    render: (row) => row.under_count,
                  },
                  {
                    key: "over",
                    header: copy.problemAnalysis.quantityMismatches.columns.over,
                    align: "right",
                    render: (row) => row.over_count,
                  },
                ]}
                rows={rows.filter(isQuantityItem)}
                rowKey={(row) => row.id}
                classNames={tableClassNames}
                labels={{
                  emptyMessage: rootFilterActive
                    ? sets.emptyFilter(rootQuery.trim())
                    : sets.empty,
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
                    header: sets.columns.set,
                    render: (row) => (
                      <span className="ppc-detector-items__set">
                        <strong>{row.set_key ?? "—"}</strong>
                        <span>{sets.openOrders(row.open_order_count, row.order_count)}</span>
                      </span>
                    ),
                  },
                  {
                    key: "root",
                    header: sets.columns.root,
                    render: (row) => (
                      <span className="ppc-detector-items__root">
                        <strong>{row.root_code ?? "—"}</strong>
                        {row.root_description ? <span>{row.root_description}</span> : null}
                        {row.missing_components.length > 0 ? (
                          <span className="ppc-detector-items__diff">
                            {copy.problemAnalysis.incompleteSets.missingLabel}{" "}
                            {row.missing_components.map(componentLine).join(" · ")}
                          </span>
                        ) : null}
                        {row.extra_components.length > 0 ? (
                          <span className="ppc-detector-items__diff">
                            {copy.problemAnalysis.incompleteSets.extraLabel}{" "}
                            {row.extra_components.map(componentLine).join(" · ")}
                          </span>
                        ) : null}
                      </span>
                    ),
                  },
                  {
                    key: "due",
                    header: sets.columns.due,
                    render: (row) => formatIsoDate(row.due_date) || "—",
                  },
                  {
                    key: "orders",
                    header: sets.columns.orders,
                    align: "right",
                    render: (row) => row.order_count,
                  },
                  {
                    key: "missing",
                    header: copy.problemAnalysis.incompleteSets.columns.missing,
                    align: "right",
                    render: (row) => row.missing_count,
                  },
                  {
                    key: "extra",
                    header: copy.problemAnalysis.incompleteSets.columns.extra,
                    align: "right",
                    render: (row) => row.extra_count,
                  },
                ]}
                rows={rows.filter(isIncompleteItem)}
                rowKey={(row) => row.id}
                classNames={tableClassNames}
                labels={{
                  emptyMessage: rootFilterActive
                    ? sets.emptyFilter(rootQuery.trim())
                    : sets.empty,
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
