import { EmptyState, SectionCard, type DataTableColumn } from "@delpi/plugin-ui/index";
import {
  CircleGauge,
  Clock3,
  PackageCheck,
  Percent,
  RefreshCw,
  Timer,
  Truck,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getSalesOrderOtdPanel, getSalesOrderOtdSeries } from "../../api/analyticsApi";
import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmSpeedometerGaugeRowClass,
  CommercialActionButton,
  CommercialDataTable,
  CommercialHorizontalValueBars,
  CommercialLoadingCard,
  CommercialMetricCard,
  CommercialPageHero,
  CommercialPagination,
  CommercialScopeChipBar,
  CommercialSectionHintLabel,
  CommercialSpeedometerGauge,
  CommercialTextField,
} from "../../app/commercialUi";
import { navigateAnalyticsOtdLine } from "../../app/pluginNavigation";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
import { CM_HELP } from "../../content/helpTooltips";
import type {
  SalesOrderOtdLineItem,
  SalesOrderOtdPanelData,
  SalesOrderOtdSeriesPoint,
} from "../../types/analytics";
import {
  ANALYTICS_OTD_COLUMN_HELP,
  withColumnHelp,
} from "../../utils/customersColumnHelp";
import { formatDisplayDate } from "../../utils/dates";
import { AnalyticsFilters } from "./components/AnalyticsFilters";
import { AnalyticsDeepPagePath } from "./components/AnalyticsDeepPagePath";
import { useAnalyticsFilters } from "./hooks/useAnalyticsFilters";
import { buildAnalyticsFilterSearchParams } from "./utils/analyticsFilterUrl";
import { ANALYTICS_OTD_SERIES_LABELS } from "./utils/analyticsBranchFilters";
import {
  defaultOtdListUrlState,
  parseOtdListUrlState,
  writeOtdListUrlState,
  type OtdListSortKey,
  type OtdListStatusFilter,
  type OtdListUrlState,
} from "./utils/otdListUrl";

const PAGE_SIZE = 30;

function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
}

function formatDays(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

function truncate(text: string | null | undefined, max = 48): string {
  const value = (text ?? "").trim();
  if (!value) return "—";
  return value.length > max ? `${value.slice(0, max - 1)}…` : value;
}

/** Dias civis até a data ISO (YYYY-MM-DD); negativo se já passou. */
function daysUntilIso(iso: string | null | undefined, today = new Date()): number | null {
  if (!iso) return null;
  const raw = iso.trim();
  const d = new Date(raw.includes("T") ? raw : `${raw}T12:00:00`);
  if (Number.isNaN(d.getTime())) return null;
  const start = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  const end = Date.UTC(d.getFullYear(), d.getMonth(), d.getDate());
  return Math.round((end - start) / 86_400_000);
}

/** Urgência para barra: quanto menor o prazo, maior a barra (janela ~60 dias). */
function upcomingUrgency(daysUntil: number | null): number {
  if (daysUntil == null) return 1;
  return Math.max(1, 60 - Math.min(59, Math.max(-5, daysUntil)));
}

type AnalyticsOtdPageProps = {
  basePath: string;
};

export function AnalyticsOtdPage({ basePath }: AnalyticsOtdPageProps) {
  const filters = useAnalyticsFilters();
  const [listState, setListState] = useState<OtdListUrlState>(() => parseOtdListUrlState());
  const [panel, setPanel] = useState<SalesOrderOtdPanelData | null>(null);
  const [series, setSeries] = useState<SalesOrderOtdSeriesPoint[]>([]);
  const [loadingPanel, setLoadingPanel] = useState(true);
  const [loadingSeries, setLoadingSeries] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    writeOtdListUrlState(listState);
  }, [listState]);

  useEffect(() => {
    const onPopState = () => setListState(parseOtdListUrlState());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const patchList = useCallback((patch: Partial<OtdListUrlState>) => {
    setListState((prev) => {
      const next = { ...prev, ...patch };
      if (
        patch.search !== undefined ||
        patch.status !== undefined ||
        patch.sortBy !== undefined ||
        patch.sortDir !== undefined
      ) {
        next.page = patch.page ?? 1;
      }
      return next;
    });
  }, []);

  const filterKey = [
    filters.apiParams.start_date,
    filters.apiParams.end_date,
    filters.apiParams.branch,
    filters.apiParams.customer_segment,
    filters.apiParams.seller_id,
  ].join("|");

  useEffect(() => {
    setListState((prev) => ({ ...prev, page: 1 }));
  }, [filterKey]);

  useEffect(() => {
    const controller = new AbortController();
    setLoadingSeries(true);
    void getSalesOrderOtdSeries(
      { ...filters.apiParams, granularity: "month" },
      controller.signal,
    )
      .then((seriesData) => {
        if (controller.signal.aborted) return;
        setSeries(seriesData.points ?? []);
      })
      .catch(() => {
        if (controller.signal.aborted) return;
        setSeries([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingSeries(false);
      });
    return () => controller.abort();
  }, [
    filters.apiParams.start_date,
    filters.apiParams.end_date,
    filters.apiParams.branch,
    filters.apiParams.customer_segment,
    filters.apiParams.seller_id,
    reloadKey,
  ]);

  useEffect(() => {
    const controller = new AbortController();
    setLoadingPanel(true);
    setError(null);
    void getSalesOrderOtdPanel(
      {
        ...filters.apiParams,
        page: listState.page,
        page_size: PAGE_SIZE,
        status: listState.status || undefined,
        search: listState.search.trim() || undefined,
        sort_by: listState.sortBy || undefined,
        sort_dir: listState.sortBy ? listState.sortDir : undefined,
      },
      controller.signal,
    )
      .then((panelData) => {
        if (controller.signal.aborted) return;
        setPanel(panelData);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar OTD.");
        setPanel(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingPanel(false);
      });
    return () => controller.abort();
  }, [
    filters.apiParams.start_date,
    filters.apiParams.end_date,
    filters.apiParams.branch,
    filters.apiParams.customer_segment,
    filters.apiParams.seller_id,
    listState.page,
    listState.search,
    listState.status,
    listState.sortBy,
    listState.sortDir,
    reloadKey,
  ]);

  const openLine = useCallback(
    (row: SalesOrderOtdLineItem) => {
      navigateAnalyticsOtdLine(row.branch, row.order_number, row.line_item, {
        basePath,
        search: buildAnalyticsFilterSearchParams(filters.filterState),
      });
    },
    [basePath, filters.filterState],
  );

  /** Último ponto da série (período mais recente) para os velocímetros. */
  const latestSeriesPoint = useMemo(() => {
    if (series.length === 0) return null;
    return [...series].sort((a, b) => a.sort_key.localeCompare(b.sort_key)).at(-1) ?? null;
  }, [series]);

  const handleSortChange = useCallback(
    (columnKey: string) => {
      const sortMap: Record<string, OtdListSortKey> = {
        order: "order_number",
        customer: "customer_name",
        product: "product_code",
        status: "status",
        promised: "promised_date",
        invoice: "invoice_date",
        daysDiff: "days_diff",
        qty: "qty_sold",
      };
      const sortBy = sortMap[columnKey];
      if (!sortBy) return;
      setListState((prev) => {
        if (prev.sortBy === sortBy) {
          return {
            ...prev,
            sortDir: prev.sortDir === "asc" ? "desc" : "asc",
            page: 1,
          };
        }
        return { ...prev, sortBy, sortDir: "asc", page: 1 };
      });
    },
    [],
  );

  const uiSortKey = useMemo(() => {
    const reverse: Record<string, string> = {
      order_number: "order",
      customer_name: "customer",
      product_code: "product",
      status: "status",
      promised_date: "promised",
      invoice_date: "invoice",
      days_diff: "daysDiff",
      qty_sold: "qty",
    };
    return listState.sortBy ? reverse[listState.sortBy] ?? null : null;
  }, [listState.sortBy]);

  const columns: DataTableColumn<SalesOrderOtdLineItem>[] = [
    {
      key: "order",
      header: "Pedido",
      sortable: true,
      render: (row) => (
        <button
          type="button"
          className="cm-link-button"
          onClick={(event) => {
            event.stopPropagation();
            openLine(row);
          }}
        >
          {row.order_number}/{row.line_item}
        </button>
      ),
    },
    {
      key: "customer",
      header: "Cliente",
      sortable: true,
      render: (row) => row.customer_name || row.customer_code || "—",
    },
    {
      key: "product",
      header: "Produto",
      sortable: true,
      render: (row) => row.product_code || "—",
    },
    {
      key: "productDesc",
      header: "Descrição",
      render: (row) => truncate(row.product_description),
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      render: (row) => (row.status === "on_time" ? "No prazo" : "Atrasado"),
    },
    {
      key: "promised",
      header: "Promessa",
      sortable: true,
      render: (row) => formatDisplayDate(row.promised_date),
    },
    {
      key: "invoice",
      header: "Fatura",
      sortable: true,
      render: (row) => formatDisplayDate(row.invoice_date),
    },
    {
      key: "daysDiff",
      header: "Dias",
      sortable: true,
      render: (row) => formatDays(row.days_diff),
    },
    {
      key: "qty",
      header: "Qtd",
      sortable: true,
      render: (row) =>
        row.qty_sold == null ? "—" : row.qty_sold.toLocaleString("pt-BR"),
    },
  ];

  const statusChips = (
    [
      { id: "" as OtdListStatusFilter, label: ANALYTICS_CONTENT.otd.statusAll },
      { id: "on_time" as OtdListStatusFilter, label: ANALYTICS_CONTENT.otd.statusOnTime },
      { id: "late" as OtdListStatusFilter, label: ANALYTICS_CONTENT.otd.statusLate },
    ] as const
  ).map((option) => ({
    id: option.id || "all",
    label: option.label,
    active: listState.status === option.id,
    onSelect: () => patchList({ status: option.id, page: 1 }),
  }));

  const summary = panel?.summary;
  const lines = panel?.lines;
  const totalPages = Math.max(1, lines?.total_pages ?? 1);

  return (
    <section className="cm-page-stack">
      <AnalyticsDeepPagePath
        basePath={basePath}
        current={ANALYTICS_CONTENT.otd.title}
        backTo="home"
        viewId="analytics_otd"
      />
      <CommercialPageHero
        aria-label={ANALYTICS_CONTENT.otd.title}
        title={
          <CommercialSectionHintLabel
            label={ANALYTICS_CONTENT.otd.title}
            hint={CM_HELP.analytics.otdPage}
          />
        }
        description={ANALYTICS_CONTENT.otd.subtitle}
        actions={
          <CommercialActionButton
            variant="ghost"
            onClick={() => {
              setListState(defaultOtdListUrlState());
              setReloadKey((v) => v + 1);
            }}
          >
            <RefreshCw size={16} aria-hidden="true" /> Atualizar
          </CommercialActionButton>
        }
      >
        <AnalyticsFilters
          dateStart={filters.dateStart}
          dateEnd={filters.dateEnd}
          competence={filters.competence}
          periodPreset={filters.periodPreset}
          branches={filters.branches}
          customerSegment={filters.customerSegment}
          sellerIds={filters.sellerIds}
          canFilterPortfolios={filters.canFilterPortfolios}
          canUseTeamScope={filters.canUseTeamScope}
          filterablePortfolios={filters.filterablePortfolios}
          onDateStart={filters.setDateStart}
          onDateEnd={filters.setDateEnd}
          onCompetence={filters.setCompetence}
          onPeriodPreset={filters.setPeriodPreset}
          onBranches={filters.setBranches}
          onCustomerSegment={filters.setCustomerSegment}
          onSellerIds={filters.setSellerIds}
        />
      </CommercialPageHero>

      {loadingPanel && !panel ? (
        <CommercialLoadingCard title="Carregando OTD…" variant="panel" />
      ) : null}
      {error ? (
        <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
      ) : null}

      {!loadingPanel && summary ? (
        <div className="cm-home-kpi-grid" aria-label="KPIs OTD">
          <CommercialMetricCard
            label="OTD %"
            titleHint={CM_HELP.analytics.otdKpi}
            value={formatPct(summary.sales_order_otd_pct)}
            icon={<CircleGauge size={22} />}
          />
          <CommercialMetricCard
            label="No prazo"
            titleHint={CM_HELP.analytics.otdKpi}
            value={(summary.on_time_lines ?? 0).toLocaleString("pt-BR")}
            icon={<PackageCheck size={22} />}
          />
          <CommercialMetricCard
            label="Atrasadas"
            titleHint={CM_HELP.analytics.otdKpi}
            value={(summary.late_lines ?? 0).toLocaleString("pt-BR")}
            icon={<Truck size={22} />}
          />
          <CommercialMetricCard
            label="% atraso"
            titleHint={CM_HELP.analytics.otdKpiLatePct}
            value={formatPct(summary.late_percentage)}
            icon={<Percent size={22} />}
          />
          <CommercialMetricCard
            label="Média dias atraso"
            titleHint={CM_HELP.analytics.otdKpiLateDays}
            value={formatDays(summary.avg_late_days)}
            icon={<Timer size={22} />}
          />
          <CommercialMetricCard
            label="P50 / P90 dias"
            titleHint={CM_HELP.analytics.otdKpiLateDays}
            value={`${formatDays(summary.p50_late_days)} / ${formatDays(summary.p90_late_days)}`}
            icon={<Clock3 size={22} />}
          />
        </div>
      ) : null}

      {!loadingPanel && panel?.insights ? (
        <div className="cm-home-kpi-grid" aria-label="Insights OTD">
          <SectionCard
            title={ANALYTICS_CONTENT.otd.insightsRecurrence}
            hint={CM_HELP.analytics.otdRecurrence}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <CommercialHorizontalValueBars
              aria-label={ANALYTICS_CONTENT.otd.insightsRecurrence}
              emptyMessage="Sem reincidência (≥2 atrasos) no período."
              items={(panel.insights.recurringCustomers ?? []).map((row) => ({
                id: row.customer_code,
                label: row.customer_name || row.customer_code || "—",
                value: row.late_count,
                valueLabel: `${row.late_count.toLocaleString("pt-BR")} atrasos`,
                meta: `∑ ${formatDays(row.total_late_days)} dias`,
              }))}
            />
          </SectionCard>
          <SectionCard
            title={ANALYTICS_CONTENT.otd.insightsWorst}
            hint={CM_HELP.analytics.otdWorstDelays}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <CommercialHorizontalValueBars
              aria-label={ANALYTICS_CONTENT.otd.insightsWorst}
              emptyMessage="Sem linhas atrasadas."
              items={(panel.insights.worstDelays ?? []).map((row) => ({
                id: `${row.branch}-${row.order_number}-${row.line_item}-worst`,
                label: `${row.order_number}/${row.line_item}`,
                value: Number(row.days_diff ?? 0),
                valueLabel: `${formatDays(row.days_diff)} dias`,
                meta: row.customer_name || row.customer_code || "—",
              }))}
              onItemClick={(item) => {
                const row = panel.insights?.worstDelays?.find(
                  (line) =>
                    `${line.branch}-${line.order_number}-${line.line_item}-worst` === item.id,
                );
                if (row) openLine(row);
              }}
            />
          </SectionCard>
          <SectionCard
            title={ANALYTICS_CONTENT.otd.insightsUpcoming}
            hint={CM_HELP.analytics.otdUpcomingPromises}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <CommercialHorizontalValueBars
              aria-label={ANALYTICS_CONTENT.otd.insightsUpcoming}
              emptyMessage="Sem promessas abertas no recorte."
              items={(panel.insights.upcomingPromises ?? []).map((row) => {
                const until = daysUntilIso(row.promised_date);
                return {
                  id: `${row.branch}-${row.order_number}-${row.line_item}-up`,
                  label: `${row.order_number}/${row.line_item}`,
                  value: upcomingUrgency(until),
                  valueLabel: formatDisplayDate(row.promised_date),
                  meta: row.customer_name || row.customer_code || "—",
                };
              })}
              onItemClick={(item) => {
                const row = panel.insights?.upcomingPromises?.find(
                  (line) =>
                    `${line.branch}-${line.order_number}-${line.line_item}-up` === item.id,
                );
                if (row) openLine(row);
              }}
            />
          </SectionCard>
        </div>
      ) : null}

      <SectionCard
        title={ANALYTICS_CONTENT.otd.seriesTitle}
        hint={CM_HELP.analytics.otdSeries}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {loadingSeries && series.length === 0 ? (
          <p className="cm-muted">Carregando série…</p>
        ) : !latestSeriesPoint ? (
          <p className="cm-muted">Sem pontos na série.</p>
        ) : (
          <div className="cm-page-stack" style={{ gap: "0.5rem" }}>
            <p className="cm-muted" style={{ margin: 0 }}>
              Período: {latestSeriesPoint.periodo}
            </p>
            <div className={cmSpeedometerGaugeRowClass} aria-label="Velocímetros OTD por unidade">
              <CommercialSpeedometerGauge
                value={latestSeriesPoint.otd_filial_01}
                label={ANALYTICS_OTD_SERIES_LABELS.unit01}
              />
              <CommercialSpeedometerGauge
                value={latestSeriesPoint.otd_filial_02}
                label={ANALYTICS_OTD_SERIES_LABELS.unit02}
              />
            </div>
          </div>
        )}
      </SectionCard>

      <SectionCard
        title="Linhas"
        hint={CM_HELP.analytics.otdLines}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-page-stack" style={{ gap: "0.75rem" }}>
          <CommercialTextField
            label="Buscar"
            hint={CM_HELP.analytics.otdLinesSearch}
            type="search"
            value={listState.search}
            onChange={(value) => patchList({ search: value, page: 1 })}
            placeholder={ANALYTICS_CONTENT.otd.linesSearchPlaceholder}
          />
          <CommercialScopeChipBar
            label={
              <CommercialSectionHintLabel
                label="Status"
                hint={CM_HELP.analytics.otdLinesStatus}
              />
            }
            aria-label="Filtro de status OTD"
            chips={statusChips}
          />
          {(lines?.items.length ?? 0) === 0 && !loadingPanel ? (
            <p className="cm-muted">{ANALYTICS_CONTENT.otd.emptyLines}</p>
          ) : (
            <CommercialDataTable
              rows={lines?.items ?? []}
              columns={withColumnHelp(columns, ANALYTICS_OTD_COLUMN_HELP)}
              rowKey={(row) => `${row.branch}-${row.order_number}-${row.line_item}`}
              layout="section"
              sortKey={uiSortKey}
              sortDirection={listState.sortDir}
              onSortChange={handleSortChange}
              onRowClick={openLine}
              rowClickRole="button"
            />
          )}
          {(lines?.total ?? 0) > PAGE_SIZE ? (
            <CommercialPagination
              page={lines?.page ?? listState.page}
              pageSize={PAGE_SIZE}
              total={lines?.total ?? 0}
              totalPages={totalPages}
              onPageChange={(page) => patchList({ page })}
              aria-label="Paginação das linhas OTD"
            />
          ) : null}
        </div>
      </SectionCard>
    </section>
  );
}
