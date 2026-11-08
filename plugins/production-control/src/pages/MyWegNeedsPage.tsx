import {
  createDashboardKpiCard,
  createDashboardLoadingActivityCard,
  HelpTooltip,
  UnderlineNav,
  underlineNavBemClasses,
} from "@delpi/plugin-ui/index";
import {
  CalendarDays,
  Eraser,
  Factory,
  Layers,
  Search,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { DataTableSection, type DataTableColumn } from "../components/dataTableUi";
import { MyWegInvoiceObservationsPanel } from "../components/MyWegInvoiceObservationsPanel";
import { MyWegNeedsHistoryChart } from "../components/MyWegNeedsHistoryChart";
import { MyWegPlanningEvolutionPanel } from "../components/MyWegPlanningEvolutionPanel";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useMyWegNeeds } from "../hooks/useMyWegNeeds";
import type { MyWegNeedsRecord, PpcBranch } from "../types";
import { formatDecimalStringFixed } from "../utils/formatDecimalString";
import { formatRefreshedAt } from "../utils/formatRefreshedAt";
import {
  buildPpcHref,
  myWegNeedsTabToAnalysis,
  navigatePpc,
  resolveMyWegNeedsTab,
  type MyWegCompareAnalysis,
  type MyWegNeedsTab,
  type MyWegNeedsView,
} from "../utils/routeParser";

const LoadingCard = createDashboardLoadingActivityCard({
  prefix: "ppc",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.mywegNeeds.loading,
  },
});

const KpiCard = createDashboardKpiCard({
  prefix: "ppc",
  labels: copy.kpi,
});

const navClassNames = underlineNavBemClasses("ppc");

type MyWegNeedsPageProps = {
  branch: PpcBranch;
  batchId: string | null;
  search: string | null;
  remessaFrom: string | null;
  remessaTo: string | null;
  page: number | null;
  view: MyWegNeedsView | null;
  analysis: MyWegCompareAnalysis | null;
};

function syncUrl(input: {
  branch: PpcBranch;
  batchId?: string | null;
  search?: string | null;
  remessaFrom?: string | null;
  remessaTo?: string | null;
  page?: number | null;
  tab?: MyWegNeedsTab;
}) {
  const tab = input.tab ?? "needs";
  navigatePpc(
    buildPpcHref({
      subpluginId: "myweg-needs",
      branch: input.branch,
      mywegNeedsBatchId: input.batchId ?? null,
      mywegNeedsSearch: input.search || null,
      mywegNeedsRemessaFrom: input.remessaFrom ?? null,
      mywegNeedsRemessaTo: input.remessaTo ?? null,
      mywegNeedsPage: input.page && input.page > 1 ? input.page : null,
      mywegNeedsView: tab,
      mywegNeedsAnalysis: myWegNeedsTabToAnalysis(tab),
    }),
  );
}

function formatCollectedAt(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return formatRefreshedAt(value);
  } catch {
    return value;
  }
}

function formatRemessa(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  if (!text) return "—";
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const [y, m, d] = text.slice(0, 10).split("-");
    return `${d}/${m}/${y}`;
  }
  return text;
}

function sb1Label(status: string | null | undefined): string {
  const normalized = (status ?? "").trim().toLowerCase();
  switch (normalized) {
    case "confirmed":
      return copy.mywegNeeds.sb1Confirmed;
    case "not_found":
      return copy.mywegNeeds.sb1NotFound;
    case "divergent":
      return copy.mywegNeeds.sb1Divergent;
    case "ambiguous":
      return copy.mywegNeeds.sb1Ambiguous;
    case "blocked":
      return copy.mywegNeeds.sb1Blocked;
    case "unavailable":
      return copy.mywegNeeds.sb1Unavailable;
    case "pending":
    case "":
      return copy.mywegNeeds.sb1Pending;
    default:
      return copy.mywegNeeds.sb1Other(status ?? "");
  }
}

export function MyWegNeedsPage({
  branch,
  batchId,
  search,
  remessaFrom,
  remessaTo,
  page,
  view,
  analysis,
}: MyWegNeedsPageProps) {
  const texts = copy.mywegNeeds;
  const activeTab = resolveMyWegNeedsTab(view, analysis);
  const compareAnalysis: MyWegCompareAnalysis =
    activeTab === "products" ? "products" : "remessa";
  const loadNeedsMeta =
    activeTab === "needs" ||
    activeTab === "reprogramming" ||
    activeTab === "products";
  const loadNeedsItems = activeTab === "needs";

  const [searchDraft, setSearchDraft] = useState(search ?? "");
  const [remessaFromDraft, setRemessaFromDraft] = useState(remessaFrom ?? "");
  const [remessaToDraft, setRemessaToDraft] = useState(remessaTo ?? "");

  const filters = useMemo(
    () => ({
      batchId,
      search: search ?? "",
      remessaFrom,
      remessaTo,
      page: page && page > 0 ? page : 1,
      pageSize: 50,
    }),
    [batchId, page, remessaFrom, remessaTo, search],
  );

  const { latest, selected, history, items, loading, refreshing, error, status, reload } =
    useMyWegNeeds(branch, filters, {
      enabled: loadNeedsMeta,
      loadItems: loadNeedsItems,
    });

  useEffect(() => {
    setSearchDraft(search ?? "");
    setRemessaFromDraft(remessaFrom ?? "");
    setRemessaToDraft(remessaTo ?? "");
  }, [remessaFrom, remessaTo, search]);

  const applyFilters = useCallback(() => {
    syncUrl({
      branch: "02",
      batchId,
      search: searchDraft.trim() || null,
      remessaFrom: remessaFromDraft.trim() || null,
      remessaTo: remessaToDraft.trim() || null,
      page: 1,
      tab: activeTab,
    });
  }, [activeTab, batchId, remessaFromDraft, remessaToDraft, searchDraft]);

  const clearFilters = useCallback(() => {
    setSearchDraft("");
    setRemessaFromDraft("");
    setRemessaToDraft("");
    syncUrl({
      branch: "02",
      batchId,
      search: null,
      remessaFrom: null,
      remessaTo: null,
      page: 1,
      tab: activeTab,
    });
  }, [activeTab, batchId]);

  const selectBatch = useCallback(
    (nextBatchId: string) => {
      syncUrl({
        branch: "02",
        batchId: nextBatchId === latest?.id ? null : nextBatchId,
        search: search ?? null,
        remessaFrom,
        remessaTo,
        page: 1,
        tab: activeTab,
      });
    },
    [activeTab, latest?.id, remessaFrom, remessaTo, search],
  );

  const setTab = useCallback(
    (next: MyWegNeedsTab) => {
      syncUrl({
        branch: "02",
        batchId,
        search: search ?? null,
        remessaFrom,
        remessaTo,
        page: activeTab === "needs" ? page : 1,
        tab: next,
      });
    },
    [activeTab, batchId, page, remessaFrom, remessaTo, search],
  );

  const goToFilial02 = useCallback(() => {
    syncUrl({
      branch: "02",
      batchId: null,
      search: null,
      remessaFrom: null,
      remessaTo: null,
      page: 1,
      tab: "needs",
    });
  }, []);

  const isLatest = Boolean(selected && latest && selected.id === latest.id);
  const historyOptions = history?.items ?? [];

  const tabItems = useMemo(
    () =>
      (
        [
          ["needs", texts.tabs.needs],
          ["reprogramming", texts.tabs.reprogramming],
          ["products", texts.tabs.products],
          ["invoices", texts.tabs.invoices],
        ] as const
      ).map(([id, label]) => ({
        id,
        label,
        controlId: `ppc-myweg-tabpanel-${id}`,
        tabId: `ppc-myweg-tab-${id}`,
        onSelect: () => setTab(id),
      })),
    [setTab, texts.tabs],
  );

  const columns = useMemo<DataTableColumn<MyWegNeedsRecord>[]>(
    () => [
      {
        key: "material_weg_tratado",
        header: texts.columns.material,
        render: (row) => row.material_weg_tratado || "—",
      },
      {
        key: "codigo_referencia_weg",
        header: texts.columns.informedCode,
        render: (row) => {
          const informed =
            row.sb1_resolution?.informed_product_code?.trim() ||
            row.codigo_referencia_weg?.trim();
          return informed || texts.referenciaEmpty;
        },
      },
      {
        key: "sb1_verified_code",
        header: texts.columns.verifiedCode,
        render: (row) =>
          row.sb1_resolution?.protheus_product_code?.trim() || "—",
      },
      {
        key: "sb1_verified_description",
        header: texts.columns.verifiedDescription,
        render: (row) =>
          row.sb1_resolution?.verified_description?.trim() || "—",
      },
      {
        key: "sb1_resolution",
        header: texts.columns.sb1,
        headerHint: helpTooltips.mywegNeedsSb1,
        render: (row) => {
          const label = sb1Label(row.sb1_resolution?.status);
          const reason = row.sb1_resolution?.reason?.trim();
          if (
            reason &&
            (row.sb1_resolution?.status === "divergent" ||
              row.sb1_resolution?.status === "ambiguous" ||
              row.sb1_resolution?.status === "unavailable")
          ) {
            return `${label} — ${reason}`;
          }
          return label;
        },
      },
      {
        key: "documento",
        header: texts.columns.documento,
        render: (row) => row.documento?.trim() || "—",
      },
      {
        key: "data_remessa",
        header: texts.columns.remessa,
        render: (row) => formatRemessa(row.data_remessa),
      },
      {
        key: "quantidade_original_un",
        header: texts.columns.qtyUn,
        align: "right",
        render: (row) => formatDecimalStringFixed(row.quantidade_original_un, 3),
      },
      {
        key: "quantidade_mi",
        header: texts.columns.qtyMi,
        align: "right",
        render: (row) => formatDecimalStringFixed(row.quantidade_mi, 3),
      },
    ],
    [texts],
  );

  if (branch !== "02") {
    return (
      <div className="ppc-page-stack ppc-page-stack--myweg-needs">
        <PpcWorkspaceHeader
          title={texts.title}
          subtitle={texts.subtitle}
          appearance="myweg"
          titleHint={helpTooltips.mywegNeeds}
          branch={branch}
          subpluginId="myweg-needs"
        />
        <div className="ppc-state ppc-myweg-needs__branch-gate" role="status">
          <p>{texts.branch01Message}</p>
          <button type="button" className="ppc-btn ppc-btn--primary" onClick={goToFilial02}>
            {texts.branch01Action}
          </button>
        </div>
      </div>
    );
  }

  const forbidden = status === 403;
  const notFound = status === 404;
  const showCompareTabs =
    activeTab === "reprogramming" || activeTab === "products";

  return (
    <div className="ppc-page-stack ppc-page-stack--myweg-needs">
      <PpcWorkspaceHeader
        title={texts.title}
        subtitle={texts.subtitle}
        appearance="myweg"
        titleHint={helpTooltips.mywegNeeds}
        period={
          selected && activeTab === "needs"
            ? texts.collectedAt(formatCollectedAt(selected.collectedAt))
            : null
        }
        stats={
          selected && activeTab === "needs" ? (
            <span className="ppc-header__stat">
              {texts.recordCount(selected.recordCount)}
            </span>
          ) : null
        }
        branch={branch}
        subpluginId="myweg-needs"
        mywegNeedsBatchId={batchId}
        mywegNeedsSearch={search}
        mywegNeedsRemessaFrom={remessaFrom}
        mywegNeedsRemessaTo={remessaTo}
        mywegNeedsPage={page}
        mywegNeedsView={activeTab}
        mywegNeedsAnalysis={myWegNeedsTabToAnalysis(activeTab)}
        onRefresh={() => void reload()}
        refreshBusy={refreshing}
      />

      <p className="ppc-myweg-needs__planning-note">
        {texts.hubNote}{" "}
        <HelpTooltip content={helpTooltips.mywegNeedsTabs} trigger="icon" />
      </p>

      <UnderlineNav
        items={tabItems}
        activeId={activeTab}
        mode="tabs"
        layout="wrap"
        density="compact"
        classNames={navClassNames}
        aria-label={texts.tabsAria}
      />

      {activeTab === "needs" ? (
        <section
          className="ppc-myweg-needs__view"
          id="ppc-myweg-tabpanel-needs"
          role="tabpanel"
          aria-labelledby="ppc-myweg-tab-needs"
          aria-label={texts.viewNeeds.sectionAria}
        >
          {loading ? <LoadingCard title={texts.loading} description={texts.loadingHint} /> : null}

          {forbidden ? (
            <div className="ppc-state ppc-state--error" role="alert">
              {texts.forbidden}
            </div>
          ) : null}

          {!forbidden && error && !loading ? (
            <div className="ppc-state ppc-state--error" role="alert">
              {notFound ? texts.notFound : error}
            </div>
          ) : null}

          {!forbidden && !loading && !error && !selected ? (
            <div className="ppc-state" role="status">
              {texts.emptyCollections}
            </div>
          ) : null}

          {selected ? (
            <>
              <section className="ppc-myweg-needs__summary" aria-label={texts.summaryAria}>
                <KpiCard
                  className="ppc-board-card ppc-myweg-needs__kpi-card"
                  title={texts.kpi.collectedAt}
                  icon={<CalendarDays size={20} strokeWidth={1.75} />}
                  value={formatCollectedAt(selected.collectedAt)}
                  footer={isLatest ? texts.latestBadge : texts.historyBadge}
                />
                <KpiCard
                  className="ppc-board-card ppc-myweg-needs__kpi-card"
                  title={texts.kpi.records}
                  icon={<Layers size={20} strokeWidth={1.75} />}
                  value={selected.recordCount.toLocaleString("pt-BR")}
                />
                <KpiCard
                  className="ppc-board-card ppc-myweg-needs__kpi-card"
                  title={texts.kpi.qtyMi}
                  icon={<Factory size={20} strokeWidth={1.75} />}
                  value={formatDecimalStringFixed(selected.totals.quantidade_mi, 3)}
                />
              </section>

              <div className="ppc-myweg-needs__ops">
                <MyWegNeedsHistoryChart
                  items={historyOptions}
                  selectedBatchId={selected.id}
                  latestBatchId={latest?.id ?? null}
                  onSelectBatch={selectBatch}
                />

                <section
                  className="ppc-myweg-needs__filters-card"
                  aria-label={texts.filtersAria}
                >
                  <header className="ppc-myweg-needs__filters-header">
                    <span className="ppc-myweg-needs__filters-icon" aria-hidden="true">
                      <Search size={18} strokeWidth={1.75} />
                    </span>
                    <h3 className="ppc-myweg-needs__filters-title">{texts.filtersTitle}</h3>
                  </header>

                  <div className="ppc-myweg-needs__filters-grid">
                    <fieldset className="ppc-myweg-needs__filters-period">
                      <legend>{texts.remessaPeriod}</legend>
                      <div className="ppc-myweg-needs__filters-period-row">
                        <label className="ppc-myweg-needs__date">
                          <span className="ppc-sr-only">{texts.remessaFrom}</span>
                          <input
                            type="date"
                            value={remessaFromDraft}
                            onChange={(event) => setRemessaFromDraft(event.target.value)}
                            aria-label={texts.remessaFrom}
                          />
                        </label>
                        <span className="ppc-myweg-needs__filters-period-sep" aria-hidden="true">
                          —
                        </span>
                        <label className="ppc-myweg-needs__date">
                          <span className="ppc-sr-only">{texts.remessaTo}</span>
                          <input
                            type="date"
                            value={remessaToDraft}
                            onChange={(event) => setRemessaToDraft(event.target.value)}
                            aria-label={texts.remessaTo}
                          />
                        </label>
                      </div>
                    </fieldset>

                    <label className="ppc-myweg-needs__search ppc-myweg-needs__filters-search">
                      <span>{texts.searchLabel}</span>
                      <input
                        type="search"
                        value={searchDraft}
                        placeholder={texts.searchPlaceholder}
                        onChange={(event) => setSearchDraft(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") applyFilters();
                        }}
                        aria-label={texts.searchAria}
                      />
                    </label>
                  </div>

                  <div className="ppc-myweg-needs__filters-actions">
                    <button
                      type="button"
                      className="ppc-btn ppc-btn--ghost"
                      onClick={clearFilters}
                    >
                      <Eraser size={15} strokeWidth={1.75} aria-hidden />
                      {texts.clearFilters}
                    </button>
                    <button
                      type="button"
                      className="ppc-btn ppc-btn--primary"
                      onClick={applyFilters}
                    >
                      <Search size={15} strokeWidth={1.75} aria-hidden />
                      {texts.applyFilters}
                    </button>
                  </div>
                </section>
              </div>

              <div data-testid="myweg-needs-table">
                <DataTableSection<MyWegNeedsRecord>
                  title={texts.tableTitle}
                  hint={texts.tableHint}
                  columns={columns}
                  rows={items?.items ?? []}
                  rowKey={(row) => row.id}
                  loading={loading}
                  refreshing={refreshing}
                  emptyMessage={texts.emptyItems}
                  hideSearch
                  columnPreferencesKey="production-control:myweg-needs:columns:v2"
                  serverPagination={{
                    page: items?.page ?? filters.page,
                    pageSize: items?.pageSize ?? filters.pageSize,
                    total: items?.total ?? 0,
                    onPageChange: (nextPage) =>
                      syncUrl({
                        branch: "02",
                        batchId,
                        search,
                        remessaFrom,
                        remessaTo,
                        page: nextPage,
                        tab: "needs",
                      }),
                    onPageSizeChange: () => {
                      /* pageSize fixo 50 nesta etapa */
                    },
                  }}
                />
              </div>
            </>
          ) : null}
        </section>
      ) : null}

      {showCompareTabs ? (
        <section
          className="ppc-myweg-needs__view ppc-myweg-needs__view--compare"
          id={
            activeTab === "products"
              ? "ppc-myweg-tabpanel-products"
              : "ppc-myweg-tabpanel-reprogramming"
          }
          role="tabpanel"
          aria-labelledby={
            activeTab === "products"
              ? "ppc-myweg-tab-products"
              : "ppc-myweg-tab-reprogramming"
          }
          aria-label={
            activeTab === "products"
              ? texts.viewProducts.sectionAria
              : texts.viewCompare.sectionAria
          }
        >
          {forbidden ? (
            <div className="ppc-state ppc-state--error" role="alert">
              {texts.forbidden}
            </div>
          ) : null}

          {!forbidden && error && !loading && historyOptions.length === 0 ? (
            <div className="ppc-state ppc-state--error" role="alert">
              {error}
            </div>
          ) : null}

          {!forbidden && historyOptions.length > 0 ? (
            <MyWegPlanningEvolutionPanel
              historyItems={historyOptions}
              selectedBatchId={selected?.id ?? batchId}
              analysis={compareAnalysis}
              hideAnalysisHub
            />
          ) : null}

          {!forbidden && !loading && historyOptions.length === 0 ? (
            <div className="ppc-state" role="status">
              {texts.emptyCollections}
            </div>
          ) : null}
        </section>
      ) : null}

      {activeTab === "invoices" ? (
        <section
          className="ppc-myweg-needs__view"
          id="ppc-myweg-tabpanel-invoices"
          role="tabpanel"
          aria-labelledby="ppc-myweg-tab-invoices"
        >
          <MyWegInvoiceObservationsPanel />
        </section>
      ) : null}
    </div>
  );
}
