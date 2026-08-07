import { ActionButton, DataTable, EmptyState, SectionCard, type DataTableColumn } from "@delpi/plugin-ui/index";
import { CircleGauge, PackageCheck, RefreshCw, Truck } from "lucide-react";
import { useEffect, useState } from "react";

import { getSalesOrderOtdPanel, getSalesOrderOtdSeries } from "../../api/gestaoApi";
import {
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialLoadingCard,
  CommercialTitleWithHelp,
} from "../../app/commercialUi";
import { navigateAnalyticsOtdLine } from "../../app/pluginNavigation";
import { KpiCard } from "../../components/KpiCard";
import { GESTAO_CONTENT } from "../../content/analyticsContent";
import type { SalesOrderOtdLineItem, SalesOrderOtdPanelData, SalesOrderOtdSeriesPoint } from "../../types/gestao";
import { formatDisplayDate } from "../../utils/dates";
import { GestaoFilters } from "./components/GestaoFilters";
import { useGestaoFilters } from "./hooks/useGestaoFilters";
import { buildGestaoFilterSearchParams } from "./utils/gestaoFilterUrl";

function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
}

type GestaoOtdPageProps = {
  basePath: string;
};

export function GestaoOtdPage({ basePath }: GestaoOtdPageProps) {
  const filters = useGestaoFilters();
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
          onClick={() =>
            navigateAnalyticsOtdLine(row.branch, row.order_number, row.line_item, {
              basePath,
              search: buildGestaoFilterSearchParams(filters.filterState),
            })
          }
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
      <header className="cm-page-header-row">
        <CommercialTitleWithHelp
          title={GESTAO_CONTENT.otd.title}
          hint={GESTAO_CONTENT.otd.subtitle}
        />
        <ActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
          <RefreshCw size={16} aria-hidden="true" /> Atualizar
        </ActionButton>
      </header>

      <GestaoFilters
        dateStart={filters.dateStart}
        dateEnd={filters.dateEnd}
        competence={filters.competence}
        branches={filters.branches}
        customerSegment={filters.customerSegment}
        onDateStart={filters.setDateStart}
        onDateEnd={filters.setDateEnd}
        onCompetence={filters.setCompetence}
        onBranches={filters.setBranches}
        onCustomerSegment={filters.setCustomerSegment}
      />

      {loading ? <CommercialLoadingCard title="Carregando OTD…" variant="panel" /> : null}
      {error ? (
        <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
      ) : null}

      {!loading && summary ? (
        <div className="cm-home-kpi-grid" aria-label="KPIs OTD">
          <KpiCard
            title="OTD %"
            value={formatPct(summary.sales_order_otd_pct)}
            icon={<CircleGauge size={22} />}
          />
          <KpiCard
            title="No prazo"
            value={(summary.on_time_lines ?? 0).toLocaleString("pt-BR")}
            icon={<PackageCheck size={22} />}
          />
          <KpiCard
            title="Atrasadas"
            value={(summary.late_lines ?? 0).toLocaleString("pt-BR")}
            icon={<Truck size={22} />}
          />
        </div>
      ) : null}

      <SectionCard
        title="Série OTD (tabela)"
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {series.length === 0 ? (
          <p className="cm-muted">Sem pontos na série.</p>
        ) : (
          <DataTable
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
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
          />
        )}
      </SectionCard>

      <SectionCard
        title="Linhas"
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <DataTable
          rows={panel?.lines.items ?? []}
          columns={columns}
          rowKey={(row) => `${row.branch}-${row.order_number}-${row.line_item}`}
          classNames={cmDataTableClassNames}
          labels={cmDataTableLabels}
          layout="section"
        />
      </SectionCard>
    </section>
  );
}
