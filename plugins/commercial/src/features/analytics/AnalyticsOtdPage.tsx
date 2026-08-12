import { EmptyState, SectionCard, type DataTableColumn } from "@delpi/plugin-ui/index";
import { CircleGauge, PackageCheck, RefreshCw, Truck } from "lucide-react";
import { useEffect, useState } from "react";

import { getSalesOrderOtdPanel, getSalesOrderOtdSeries } from "../../api/analyticsApi";
import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialActionButton,
  CommercialDataTable,
  CommercialLoadingCard,
  CommercialMetricCard,
  CommercialPageHero,
  CommercialSectionHintLabel,
} from "../../app/commercialUi";
import { navigateAnalyticsOtdLine } from "../../app/pluginNavigation";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
import { CM_HELP } from "../../content/helpTooltips";
import type { SalesOrderOtdLineItem, SalesOrderOtdPanelData, SalesOrderOtdSeriesPoint } from "../../types/analytics";
import { formatDisplayDate } from "../../utils/dates";
import { AnalyticsFilters } from "./components/AnalyticsFilters";
import { AnalyticsDeepPagePath } from "./components/AnalyticsDeepPagePath";
import { useAnalyticsFilters } from "./hooks/useAnalyticsFilters";
import { buildAnalyticsFilterSearchParams } from "./utils/analyticsFilterUrl";

function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
}

type AnalyticsOtdPageProps = {
  basePath: string;
};

export function AnalyticsOtdPage({ basePath }: AnalyticsOtdPageProps) {
  const filters = useAnalyticsFilters();
  const [panel, setPanel] = useState<SalesOrderOtdPanelData | null>(null);
  const [series, setSeries] = useState<SalesOrderOtdSeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void Promise.all([
      getSalesOrderOtdPanel(
        { ...filters.apiParams, page: 1, page_size: 30 },
        controller.signal,
      ),
      getSalesOrderOtdSeries(
        { ...filters.apiParams, granularity: "month" },
        controller.signal,
      ),
    ])
      .then(([panelData, seriesData]) => {
        if (controller.signal.aborted) return;
        setPanel(panelData);
        setSeries(seriesData.points ?? []);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar OTD.");
        setPanel(null);
        setSeries([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
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

  const columns: DataTableColumn<SalesOrderOtdLineItem>[] = [
    {
      key: "order",
      header: "Pedido",
      render: (row) => (
        <button
          type="button"
          className="cm-link-button"
          onClick={(event) => {
            event.stopPropagation();
            navigateAnalyticsOtdLine(row.branch, row.order_number, row.line_item, {
              basePath,
              search: buildAnalyticsFilterSearchParams(filters.filterState),
            });
          }}
        >
          {row.order_number}/{row.line_item}
        </button>
      ),
    },
    { key: "customer", header: "Cliente", render: (row) => row.customer_name || row.customer_code || "—" },
    { key: "product", header: "Produto", render: (row) => row.product_code || "—" },
    {
      key: "status",
      header: "Status",
      render: (row) => (row.status === "on_time" ? "No prazo" : "Atrasado"),
    },
    {
      key: "promised",
      header: "Promessa",
      render: (row) => formatDisplayDate(row.promised_date),
    },
  ];

  const summary = panel?.summary;

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
          <CommercialActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
            <RefreshCw size={16} aria-hidden="true" /> Atualizar
          </CommercialActionButton>
        }
      >
      <AnalyticsFilters
        dateStart={filters.dateStart}
        dateEnd={filters.dateEnd}
        competence={filters.competence}
        branches={filters.branches}
        customerSegment={filters.customerSegment}
        sellerId={filters.sellerId}
        canFilterPortfolios={filters.canFilterPortfolios}
        canUseTeamScope={filters.canUseTeamScope}
        filterablePortfolios={filters.filterablePortfolios}
        onDateStart={filters.setDateStart}
        onDateEnd={filters.setDateEnd}
        onCompetence={filters.setCompetence}
        onBranches={filters.setBranches}
        onCustomerSegment={filters.setCustomerSegment}
        onSellerId={filters.setSellerId}
      />
      </CommercialPageHero>

      {loading ? <CommercialLoadingCard title="Carregando OTD…" variant="panel" /> : null}
      {error ? (
        <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
      ) : null}

      {!loading && summary ? (
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
        </div>
      ) : null}

      <SectionCard
        title="Série OTD (tabela)"
        hint={CM_HELP.analytics.otdSeries}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {series.length === 0 ? (
          <p className="cm-muted">Sem pontos na série.</p>
        ) : (
          <CommercialDataTable
            rows={series}
            columns={[
              { key: "periodo", header: "Período", render: (row) => row.periodo },
              {
                key: "otd01",
                header: "OTD SC",
                render: (row) => formatPct(row.otd_filial_01),
              },
              {
                key: "otd02",
                header: "OTD ES",
                render: (row) => formatPct(row.otd_filial_02),
              },
            ]}
            rowKey={(row) => row.sort_key}
            layout="section"
          />
        )}
      </SectionCard>

      <SectionCard
        title="Linhas"
        hint={CM_HELP.analytics.otdLines}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <CommercialDataTable
          rows={panel?.lines.items ?? []}
          columns={columns}
          rowKey={(row) => `${row.branch}-${row.order_number}-${row.line_item}`}
          layout="section"
          onRowClick={(row) =>
            navigateAnalyticsOtdLine(row.branch, row.order_number, row.line_item, {
              basePath,
              search: buildAnalyticsFilterSearchParams(filters.filterState),
            })
          }
          rowClickRole="button"
        />
      </SectionCard>
    </section>
  );
}
