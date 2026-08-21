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
} from "../types";
import { filterIncompleteSetsByRootProduct } from "../utils/filterIncompleteSetsByRootProduct";
import { formatIsoDate } from "../utils/formatIsoDate";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

const tableClassNames = dataTableBemClasses("ppc");
const navCardClassNames = navigationCardBemClasses("ppc");
const tableLabels = {
  emptyMessage: copy.problemAnalysis.incompleteSets.empty,
  loadingMessage: copy.table.loading,
  sortByAriaLabel: copy.table.sort,
  headerHelpAriaLabel: copy.table.help,
};

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

function detectorMeta(detector: ProblemDetector): string {
  const sets = copy.problemAnalysis.incompleteSets;
  const parts = [
    sets.breakdown(
      metricNumber(detector.metrics, "missing_set_count"),
      metricNumber(detector.metrics, "extra_set_count"),
    ),
    sets.checked(metricNumber(detector.metrics, "checked_set_count")),
  ];
  return parts.join(" · ");
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
  const sets = copy.problemAnalysis.incompleteSets;
  const allRows = (items?.items ?? []) as IncompleteOrderSetItem[];
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
        titleHint={helpTooltips.problemAnalysis}
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
                          {sets.missingLabel}{" "}
                          {row.missing_components.map(componentLine).join(" · ")}
                        </span>
                      ) : null}
                      {row.extra_components.length > 0 ? (
                        <span className="ppc-detector-items__diff">
                          {sets.extraLabel} {row.extra_components.map(componentLine).join(" · ")}
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
                  header: sets.columns.missing,
                  align: "right",
                  render: (row) => row.missing_count,
                },
                {
                  key: "extra",
                  header: sets.columns.extra,
                  align: "right",
                  render: (row) => row.extra_count,
                },
              ]}
              rows={rows}
              rowKey={(row) => row.id}
              classNames={tableClassNames}
              labels={{
                ...tableLabels,
                loadingMessage: copy.problemAnalysis.itemsLoading,
                emptyMessage: rootFilterActive
                  ? sets.emptyFilter(rootQuery.trim())
                  : sets.empty,
              }}
              loading={itemsLoading}
              layout="embedded"
            />
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
