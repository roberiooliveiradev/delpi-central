import {
  EmptyState,
  OPERATIONAL_UNIT_COLUMN_LABEL,
  SectionCard,
  formatOperationalUnitCode,
} from "@delpi/plugin-ui/index";
import { useEffect, useState } from "react";

import { getSalesOrderOtdLineDetail } from "../../api/analyticsApi";
import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialDetailFieldGrid,
  CommercialLoadingCard,
  CommercialPagePath,
  CommercialPageHero,
} from "../../app/commercialUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
import type { SalesOrderOtdLineDetailData } from "../../types/analytics";
import { formatDisplayDate } from "../../utils/dates";
import { useAnalyticsFilters } from "./hooks/useAnalyticsFilters";
import { buildAnalyticsFilterSearchParams } from "./utils/analyticsFilterUrl";

type AnalyticsOtdLineDetailPageProps = {
  basePath: string;
  branch: string;
  orderNumber: string;
  lineItem: string;
};

export function AnalyticsOtdLineDetailPage({
  basePath,
  branch,
  orderNumber,
  lineItem,
}: AnalyticsOtdLineDetailPageProps) {
  const filters = useAnalyticsFilters();
  const [data, setData] = useState<SalesOrderOtdLineDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const backHref = buildPluginPath(
    "analytics_otd",
    basePath,
    buildAnalyticsFilterSearchParams(filters.filterState),
  );

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void getSalesOrderOtdLineDetail(
      branch,
      orderNumber,
      lineItem,
      {
        start_date: filters.apiParams.start_date,
        end_date: filters.apiParams.end_date,
        customer_segment: filters.apiParams.customer_segment,
      },
      controller.signal,
    )
      .then((result) => {
        if (!controller.signal.aborted) setData(result);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar linha.");
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    branch,
    orderNumber,
    lineItem,
    filters.apiParams.start_date,
    filters.apiParams.end_date,
    filters.apiParams.customer_segment,
  ]);

  const line = data?.line;

  return (
    <section className="cm-page-stack">
      <CommercialPagePath
        back={{
          label: "OTD",
          href: backHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginPath(backHref);
          },
        }}
        current={`Pedido ${orderNumber} · item ${lineItem}`}
      />
      <CommercialPageHero
        aria-label={ANALYTICS_CONTENT.otd.lineDetail}
        title={ANALYTICS_CONTENT.otd.lineDetail}
        description={`${formatOperationalUnitCode(branch)} · ${orderNumber} · ${lineItem}`}
      />

      {loading ? <CommercialLoadingCard title="Carregando detalhe…" variant="panel" /> : null}
      {error ? (
        <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
      ) : null}

      {!loading && line ? (
        <SectionCard
          title="Linha do pedido"
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <CommercialDetailFieldGrid
            fields={[
              {
                label: OPERATIONAL_UNIT_COLUMN_LABEL,
                value: formatOperationalUnitCode(line.branch),
              },
              { label: "Pedido", value: line.order_number },
              { label: "Item", value: line.line_item },
              { label: "Cliente", value: line.customer_name || line.customer_code || "—" },
              { label: "Produto", value: line.product_code || "—" },
              { label: "Descrição", value: line.product_description || "—" },
              {
                label: "Status",
                value: line.status === "on_time" ? "No prazo" : "Atrasado",
              },
              { label: "Promessa", value: formatDisplayDate(line.promised_date) },
              { label: "Faturamento", value: formatDisplayDate(line.invoice_date) },
              {
                label: "Qtd vendida",
                value: line.qty_sold != null ? String(line.qty_sold) : "—",
              },
              {
                label: "Qtd entregue",
                value: line.qty_delivered != null ? String(line.qty_delivered) : "—",
              },
              {
                label: "Diferença (dias)",
                value: line.days_diff != null ? String(line.days_diff) : "—",
              },
            ]}
          />
        </SectionCard>
      ) : null}
    </section>
  );
}
