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

import { getSalesOrderOtdPanel, getSalesOrderOtdSeries, getSalesOrderOtd } from "../../api/analyticsApi";
import {
  CommercialEntityLink,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialActionButton,
  CommercialDataTable,
  CommercialLoadingCard,
  CommercialMetricCard,
  CommercialPageHero,
  CommercialPagination,
  CommercialScopeChipBar,
  CommercialSectionHintLabel,
  CommercialSpeedometerGauge,
  CommercialTextField,
} from "../../app/commercialUi";
import {
  buildAnalyticsOtdLinePath,
  navigateAnalyticsOtdLine,
} from "../../app/pluginNavigation";
import { otdLineLinkTitle } from "../../content/entityLinkHints";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
import { CM_HELP } from "../../content/helpTooltips";
import {
  customerAvatarKey,
  useCustomerAvatarPresence,
} from "../../hooks/useCustomerAvatarPresence";
import type {
  SalesOrderOtdData,
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
import { AnalyticsOtdInsightBarChart } from "./components/AnalyticsOtdInsightBarChart";
import { OtdCustomerIdentityCell } from "./components/OtdCustomerIdentityCell";
import { useAnalyticsFilters } from "./hooks/useAnalyticsFilters";
import { buildAnalyticsFilterSearchParams } from "./utils/analyticsFilterUrl";
import {
  ANALYTICS_OTD_SERIES_LABELS,
  OPERATIONAL_UNIT_COLUMN_LABEL,
  formatOperationalUnitCode,
} from "./utils/analyticsBranchFilters";
import { fetchPerBranchMetricSlices } from "../overview/goalDisplay";
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

type AnalyticsOtdPageProps = {
  basePath: string;
};

export function AnalyticsOtdPage({ basePath }: AnalyticsOtdPageProps) {
  const filters = useAnalyticsFilters();
  const [listState, setListState] = useState<OtdListUrlState>(() => parseOtdListUrlState());
  const [panel, setPanel] = useState<SalesOrderOtdPanelData | null>(null);
  const [series, setSeries] = useState<SalesOrderOtdSeriesPoint[]>([]);
  const [otdGoalByBranch, setOtdGoalByBranch] = useState<{
    "01": number | null;
    "02": number | null;
  }>({ "01": null, "02": null });
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
    void fetchPerBranchMetricSlices(
      (branch, signal) =>
        getSalesOrderOtd({ ...filters.apiParams, branch }, signal ?? controller.signal),
      (data: SalesOrderOtdData) => data.sales_order_otd_pct,
      controller.signal,
    )
      .then((slices) => {
        if (controller.signal.aborted) return;
        const goalOf = (slice: { goal?: SalesOrderOtdData | null } | null) => {
          const goal = slice?.goal;
          if (!goal) return null;
          const raw = goal.comparable_goal ?? goal.target;
          return raw == null || Number.isNaN(Number(raw)) ? null : Number(raw);
        };
        setOtdGoalByBranch({
          "01": goalOf(slices.filial01),
          "02": goalOf(slices.filial02),
        });
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setOtdGoalByBranch({ "01": null, "02": null });
        }
      });
    return () => controller.abort();
  }, [
    filters.apiParams.start_date,
    filters.apiParams.end_date,
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

  const avatarPairs = useMemo(() => {
    const insights = panel?.insights;
    const pairs: Array<{ customer_code: string; customer_store: string }> = [];
    const push = (code?: string | null, store?: string | null) => {
      const c = (code ?? "").trim();
      const s = (store ?? "").trim();
      if (!c || !s) return;
      pairs.push({ customer_code: c, customer_store: s });
    };
    for (const row of insights?.recurringCustomers ?? []) {
      push(row.customer_code, row.customer_store);
    }
    for (const row of insights?.worstDelays ?? []) {
      push(row.customer_code, row.customer_store);
    }
    for (const row of insights?.upcomingPromises ?? []) {
      push(row.customer_code, row.customer_store);
    }
    for (const row of panel?.lines?.items ?? []) {
      push(row.customer_code, row.customer_store);
    }
    return pairs;
  }, [panel]);

  const avatarByKey = useCustomerAvatarPresence(avatarPairs);

  const customerIdentity = useCallback(
    (row: {
      customer_code?: string | null;
      customer_store?: string | null;
      customer_name?: string | null;
      customer_short_name?: string | null;
    }) => {
      const code = (row.customer_code ?? "").trim();
      const store = (row.customer_store ?? "").trim();
      return {
        code,
        store,
        name: row.customer_name,
        shortName: row.customer_short_name,
        hasAvatar: code && store ? Boolean(avatarByKey.get(customerAvatarKey(code, store))) : false,
      };
    },
    [avatarByKey],
  );

  const handleSortChange = useCallback(
    (columnKey: string) => {
      const sortMap: Record<string, OtdListSortKey> = {
        branch: "branch",
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
      branch: "branch",
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
      key: "branch",
      header: OPERATIONAL_UNIT_COLUMN_LABEL,
      sortable: true,
      render: (row) => formatOperationalUnitCode(row.branch) || row.branch || "—",
    },
    {
      key: "order",
      header: "Pedido",
      sortable: true,
      render: (row) => {
        const href =
          buildAnalyticsOtdLinePath(
            basePath,
            row.branch,
            row.order_number,
            row.line_item,
            buildAnalyticsFilterSearchParams(filters.filterState),
          ) ?? "#";
        const label = `${row.order_number}/${row.line_item}`;
        return (
          <CommercialEntityLink
            href={href}
            title={otdLineLinkTitle(row.order_number, row.line_item)}
            className="cm-link-button"
            onNavigate={() => openLine(row)}
          >
            {label}
          </CommercialEntityLink>
        );
      },
    },
    {
      key: "customer",
      header: "Cliente",
      sortable: true,
      render: (row) => <OtdCustomerIdentityCell customer={customerIdentity(row)} />,
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
            <AnalyticsOtdInsightBarChart
              valueLabel="Atrasos"
              emptyMessage="Sem reincidência (≥2 atrasos) no período."
              rows={(panel.insights.recurringCustomers ?? []).map((row) => ({
                id: `${row.customer_code}|${row.customer_store ?? ""}`,
                value: row.late_count,
                customer: customerIdentity(row),
              }))}
              formatValue={(value) =>
                `${value.toLocaleString("pt-BR")} atrasos`
              }
            />
          </SectionCard>
          <SectionCard
            title={ANALYTICS_CONTENT.otd.insightsWorst}
            hint={CM_HELP.analytics.otdWorstDelays}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <AnalyticsOtdInsightBarChart
              valueLabel="Dias de atraso"
              emptyMessage="Sem linhas atrasadas."
              rows={(panel.insights.worstDelays ?? []).map((row) => ({
                id: `${row.branch}-${row.order_number}-${row.line_item}-worst`,
                value: Number(row.days_diff ?? 0),
                axisLabel: `${row.order_number}/${row.line_item}`,
                customer: customerIdentity(row),
              }))}
              formatValue={(value) => `${formatDays(value)} dias`}
              onRowClick={(item) => {
                const row = panel.insights?.worstDelays?.find(
                  (line) =>
                    `${line.branch}-${line.order_number}-${line.line_item}-worst` ===
                    item.id,
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
            {(panel.insights.upcomingPromises?.length ?? 0) === 0 ? (
              <p className="cm-muted">Sem promessas abertas no recorte.</p>
            ) : (
              <CommercialDataTable
                rows={panel.insights.upcomingPromises}
                columns={[
                  {
                    key: "order",
                    header: "Pedido",
                    render: (row) => {
                      const href =
                        buildAnalyticsOtdLinePath(
                          basePath,
                          row.branch,
                          row.order_number,
                          row.line_item,
                          buildAnalyticsFilterSearchParams(filters.filterState),
                        ) ?? "#";
                      const label = `${row.order_number}/${row.line_item}`;
                      return (
                        <CommercialEntityLink
                          href={href}
                          title={otdLineLinkTitle(row.order_number, row.line_item)}
                          className="cm-link-button"
                          onNavigate={() => openLine(row)}
                        >
                          {label}
                        </CommercialEntityLink>
                      );
                    },
                  },
                  {
                    key: "customer",
                    header: "Cliente",
                    render: (row) => (
                      <OtdCustomerIdentityCell customer={customerIdentity(row)} />
                    ),
                  },
                  {
                    key: "promised",
                    header: "Promessa",
                    render: (row) => formatDisplayDate(row.promised_date),
                  },
                ]}
                rowKey={(row) => `${row.branch}-${row.order_number}-${row.line_item}-up`}
                layout="section"
                onRowClick={openLine}
                rowClickRole="button"
              />
            )}
          </SectionCard>
        </div>
      ) : null}

      {loadingSeries && series.length === 0 ? (
        <SectionCard
          title={ANALYTICS_CONTENT.otd.seriesTitle}
          hint={CM_HELP.analytics.otdSeries}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <p className="cm-muted">Carregando série…</p>
        </SectionCard>
      ) : !latestSeriesPoint ? (
        <SectionCard
          title={ANALYTICS_CONTENT.otd.seriesTitle}
          hint={CM_HELP.analytics.otdSeries}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <p className="cm-muted">Sem pontos na série.</p>
        </SectionCard>
      ) : (
        <div className="cm-otd-series-grid" aria-label="Série OTD por unidade">
          <SectionCard
            title={ANALYTICS_OTD_SERIES_LABELS.unit01}
            hint={CM_HELP.analytics.otdSeries}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <p className="cm-muted" style={{ margin: "0 0 0.35rem" }}>
              Período: {latestSeriesPoint.periodo}
            </p>
            <CommercialSpeedometerGauge
              size={280}
              value={latestSeriesPoint.otd_filial_01}
              goal={otdGoalByBranch["01"]}
              showZonesLegend
              tip={`${ANALYTICS_OTD_SERIES_LABELS.unit01} em ${latestSeriesPoint.periodo}`}
            />
          </SectionCard>
          <SectionCard
            title={ANALYTICS_OTD_SERIES_LABELS.unit02}
            hint={CM_HELP.analytics.otdSeries}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <p className="cm-muted" style={{ margin: "0 0 0.35rem" }}>
              Período: {latestSeriesPoint.periodo}
            </p>
            <CommercialSpeedometerGauge
              size={280}
              value={latestSeriesPoint.otd_filial_02}
              goal={otdGoalByBranch["02"]}
              showZonesLegend
              tip={`${ANALYTICS_OTD_SERIES_LABELS.unit02} em ${latestSeriesPoint.periodo}`}
            />
          </SectionCard>
        </div>
      )}

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
