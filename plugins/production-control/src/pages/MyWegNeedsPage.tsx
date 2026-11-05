import { createDashboardLoadingActivityCard, HelpTooltip } from "@delpi/plugin-ui/index";
import { ClipboardList, GitCompareArrows } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { DataTableSection, type DataTableColumn } from "../components/dataTableUi";
import { MyWegPlanningEvolutionPanel } from "../components/MyWegPlanningEvolutionPanel";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useMyWegNeeds } from "../hooks/useMyWegNeeds";
import type { MyWegNeedsRecord, PpcBranch } from "../types";
import { formatDecimalString } from "../utils/formatDecimalString";
import { formatRefreshedAt } from "../utils/formatRefreshedAt";
import {
  buildPpcHref,
  navigatePpc,
  resolveMyWegCompareAnalysis,
  resolveMyWegNeedsView,
  type MyWegCompareAnalysis,
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
  view?: MyWegNeedsView | null;
  analysis?: MyWegCompareAnalysis | null;
}) {
  navigatePpc(
    buildPpcHref({
      subpluginId: "myweg-needs",
      branch: input.branch,
      mywegNeedsBatchId: input.batchId ?? null,
      mywegNeedsSearch: input.search || null,
      mywegNeedsRemessaFrom: input.remessaFrom ?? null,
      mywegNeedsRemessaTo: input.remessaTo ?? null,
      mywegNeedsPage: input.page && input.page > 1 ? input.page : null,
      mywegNeedsView: input.view ?? null,
      mywegNeedsAnalysis:
        input.view === "compare" ? input.analysis ?? null : null,
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
  const activeView = resolveMyWegNeedsView(view);
  const activeAnalysis = resolveMyWegCompareAnalysis(analysis);
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
    useMyWegNeeds(branch, filters);

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
      view: activeView,
      analysis: activeView === "compare" ? activeAnalysis : null,
    });
  }, [activeAnalysis, activeView, batchId, remessaFromDraft, remessaToDraft, searchDraft]);

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
      view: activeView,
      analysis: activeView === "compare" ? activeAnalysis : null,
    });
  }, [activeAnalysis, activeView, batchId]);

  const selectBatch = useCallback(
    (nextBatchId: string) => {
      syncUrl({
        branch: "02",
        batchId: nextBatchId === latest?.id ? null : nextBatchId,
        search: search ?? null,
        remessaFrom,
        remessaTo,
        page: 1,
        view: activeView,
        analysis: activeView === "compare" ? activeAnalysis : null,
      });
    },
    [activeAnalysis, activeView, latest?.id, remessaFrom, remessaTo, search],
  );

  const setView = useCallback(
    (next: MyWegNeedsView) => {
      syncUrl({
        branch: "02",
        batchId,
        search: search ?? null,
        remessaFrom,
        remessaTo,
        page: activeView === "needs" ? page : 1,
        view: next,
        analysis: next === "compare" ? activeAnalysis : null,
      });
    },
    [activeAnalysis, batchId, remessaFrom, remessaTo, search, page, activeView],
  );

  const setAnalysis = useCallback(
    (next: MyWegCompareAnalysis) => {
      syncUrl({
        branch: "02",
        batchId,
        search: search ?? null,
        remessaFrom,
        remessaTo,
        page: 1,
        view: "compare",
        analysis: next,
      });
    },
    [batchId, remessaFrom, remessaTo, search],
  );

  const goToFilial02 = useCallback(() => {
    syncUrl({
      branch: "02",
      batchId: null,
      search: null,
      remessaFrom: null,
      remessaTo: null,
      page: 1,
      view: "needs",
      analysis: null,
    });
  }, []);

  const isLatest = Boolean(selected && latest && selected.id === latest.id);
  const historyOptions = history?.items ?? [];
  const historyReady = historyOptions.length >= 2;

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
        render: (row) => formatDecimalString(row.quantidade_original_un),
      },
      {
        key: "quantidade_mi",
        header: texts.columns.qtyMi,
        align: "right",
        render: (row) => formatDecimalString(row.quantidade_mi),
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
  const latestWhen = latest ? formatCollectedAt(latest.collectedAt) : null;

  return (
    <div className="ppc-page-stack ppc-page-stack--myweg-needs">
      <PpcWorkspaceHeader
        title={texts.title}
        subtitle={texts.subtitle}
        titleHint={helpTooltips.mywegNeeds}
        period={
          selected && activeView === "needs"
            ? texts.collectedAt(formatCollectedAt(selected.collectedAt))
            : null
        }
        stats={
          selected && activeView === "needs" ? (
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
        mywegNeedsView={activeView}
        mywegNeedsAnalysis={activeView === "compare" ? activeAnalysis : null}
        onRefresh={() => void reload()}
        refreshBusy={refreshing}
      />

      <p className="ppc-myweg-needs__planning-note">
        {texts.hubNote}{" "}
        <HelpTooltip content={helpTooltips.mywegNeeds} trigger="icon" />
      </p>

      <nav className="ppc-myweg-needs__hub" aria-label={texts.hubAria}>
        <button
          type="button"
          className={
            activeView === "needs"
              ? "ppc-myweg-needs__hub-card ppc-myweg-needs__hub-card--active"
              : "ppc-myweg-needs__hub-card"
          }
          aria-label={`${texts.viewNeeds.cardTitle} — ${texts.viewNeeds.cardAction}`}
          aria-pressed={activeView === "needs"}
          onClick={() => setView("needs")}
        >
          <span className="ppc-myweg-needs__hub-icon" aria-hidden="true">
            <ClipboardList size={20} strokeWidth={1.75} />
          </span>
          <span className="ppc-myweg-needs__hub-body">
            <span className="ppc-myweg-needs__hub-title-row">
              <span className="ppc-myweg-needs__hub-title">{texts.viewNeeds.cardTitle}</span>
              <span className="ppc-myweg-needs__hub-action">{texts.viewNeeds.cardAction}</span>
            </span>
            <span className="ppc-myweg-needs__hub-desc">{texts.viewNeeds.cardDescription}</span>
            <span className="ppc-myweg-needs__hub-meta">
              {latestWhen
                ? texts.viewNeeds.cardMetaLatest(latestWhen)
                : texts.viewNeeds.cardMetaEmpty}
              {latest ? ` · ${texts.viewNeeds.cardMetaRecords(latest.recordCount)}` : ""}
            </span>
          </span>
        </button>

        <button
          type="button"
          className={
            activeView === "compare"
              ? "ppc-myweg-needs__hub-card ppc-myweg-needs__hub-card--active ppc-myweg-needs__hub-card--compare"
              : "ppc-myweg-needs__hub-card ppc-myweg-needs__hub-card--compare"
          }
          aria-label={`${texts.viewCompare.cardTitle} — ${texts.viewCompare.cardAction}`}
          aria-pressed={activeView === "compare"}
          onClick={() => setView("compare")}
        >
          <span className="ppc-myweg-needs__hub-icon" aria-hidden="true">
            <GitCompareArrows size={20} strokeWidth={1.75} />
          </span>
          <span className="ppc-myweg-needs__hub-body">
            <span className="ppc-myweg-needs__hub-title-row">
              <span className="ppc-myweg-needs__hub-title">{texts.viewCompare.cardTitle}</span>
              <span className="ppc-myweg-needs__hub-action">{texts.viewCompare.cardAction}</span>
            </span>
            <span className="ppc-myweg-needs__hub-desc">{texts.viewCompare.cardDescription}</span>
            <span className="ppc-myweg-needs__hub-meta">
              {latestWhen
                ? texts.viewCompare.cardMetaCurrent(latestWhen)
                : texts.viewNeeds.cardMetaEmpty}
              {` · ${
                historyReady
                  ? texts.viewCompare.cardMetaHistoryReady
                  : texts.viewCompare.cardMetaHistoryShort
              }`}
            </span>
          </span>
        </button>
      </nav>

      {activeView === "needs" ? (
        <section className="ppc-myweg-needs__view" aria-label={texts.viewNeeds.sectionTitle}>
          <h2 className="ppc-myweg-needs__view-title">{texts.viewNeeds.sectionTitle}</h2>

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
                <article className="ppc-myweg-needs__kpi">
                  <h3>{texts.kpi.collectedAt}</h3>
                  <p>{formatCollectedAt(selected.collectedAt)}</p>
                  <span className="ppc-myweg-needs__kpi-tag">
                    {isLatest ? texts.latestBadge : texts.historyBadge}
                  </span>
                </article>
                <article className="ppc-myweg-needs__kpi">
                  <h3>{texts.kpi.records}</h3>
                  <p>{selected.recordCount.toLocaleString("pt-BR")}</p>
                </article>
                <article className="ppc-myweg-needs__kpi">
                  <h3>{texts.kpi.qtyUn}</h3>
                  <p>{formatDecimalString(selected.totals.quantidade_original_un)}</p>
                </article>
                <article className="ppc-myweg-needs__kpi">
                  <h3>{texts.kpi.qtyMi}</h3>
                  <p>{formatDecimalString(selected.totals.quantidade_mi)}</p>
                </article>
                <article className="ppc-myweg-needs__kpi">
                  <h3>{texts.kpi.branch}</h3>
                  <p>{texts.branch02Label}</p>
                </article>
              </section>

              <div className="ppc-myweg-needs__toolbar" aria-label={texts.viewNeeds.sectionTitle}>
                <label className="ppc-myweg-needs__history">
                  <span>{texts.historyLabel}</span>
                  <select
                    value={selected.id}
                    onChange={(event) => selectBatch(event.target.value)}
                    aria-label={texts.historyAria}
                  >
                    {historyOptions.map((batch) => (
                      <option key={batch.id} value={batch.id}>
                        {formatCollectedAt(batch.collectedAt)}
                        {latest?.id === batch.id ? ` — ${texts.latestBadge}` : ""}
                        {` (${batch.recordCount.toLocaleString("pt-BR")})`}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="ppc-myweg-needs__search">
                  <span className="ppc-sr-only">{texts.searchAria}</span>
                  <input
                    type="search"
                    value={searchDraft}
                    placeholder={texts.searchPlaceholder}
                    onChange={(event) => setSearchDraft(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") applyFilters();
                    }}
                  />
                </label>

                <label className="ppc-myweg-needs__date">
                  <span>{texts.remessaFrom}</span>
                  <input
                    type="date"
                    value={remessaFromDraft}
                    onChange={(event) => setRemessaFromDraft(event.target.value)}
                  />
                </label>
                <label className="ppc-myweg-needs__date">
                  <span>{texts.remessaTo}</span>
                  <input
                    type="date"
                    value={remessaToDraft}
                    onChange={(event) => setRemessaToDraft(event.target.value)}
                  />
                </label>

                <button type="button" className="ppc-btn ppc-btn--secondary" onClick={applyFilters}>
                  {texts.applyFilters}
                </button>
                <button type="button" className="ppc-btn ppc-btn--ghost" onClick={clearFilters}>
                  {texts.clearFilters}
                </button>
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
                      view: "needs",
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
      ) : (
        <section className="ppc-myweg-needs__view" aria-label={texts.viewCompare.sectionTitle}>
          <div className="ppc-myweg-needs__view-heading">
            <h2 className="ppc-myweg-needs__view-title">{texts.viewCompare.sectionTitle}</h2>
            <HelpTooltip content={helpTooltips.mywegNeedsEvolution} trigger="icon" />
          </div>

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
              analysis={activeAnalysis}
              onAnalysisChange={setAnalysis}
            />
          ) : null}

          {!forbidden && !loading && historyOptions.length === 0 ? (
            <div className="ppc-state" role="status">
              {texts.emptyCollections}
            </div>
          ) : null}
        </section>
      )}
    </div>
  );
}
