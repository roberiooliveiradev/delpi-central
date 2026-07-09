import { useMemo } from "react";
import { ArrowLeft, PackageCheck, Truck } from "lucide-react";

import { getSalesOrderOtdLineDetail } from "../api/commercialApi";
import { DetailCard } from "../components/DetailCard";
import { DetailFieldGrid } from "../components/DetailFieldGrid";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { TotvsSourceBanner } from "../components/TotvsSourceBanner";
import { COMMERCIAL_ROUTES } from "../constants/routes";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useCommercialFilters } from "../hooks/useCommercialFilters";
import { useCommercialResource } from "../hooks/useCommercialResource";
import { useLoadingProgress, EMPTY_REQUEST_PROGRESS } from "../hooks/useSimulatedLoadingProgress";
import { appendFiltersToPath } from "../utils/filterUrl";
import { formatDisplayDate } from "../utils/dates";
import { formatDecimal, formatInteger } from "../utils/format";
import { navigateCommercialBack } from "../utils/navigation";
import { formatOperationalUnitCode } from "../utils/operationalUnitLabels";

type SalesOrderOtdLineDetailPageProps = {
  branch: string;
  orderNumber: string;
  lineItem: string;
};

export function SalesOrderOtdLineDetailPage({
  branch,
  orderNumber,
  lineItem,
}: SalesOrderOtdLineDetailPageProps) {
  const { apiParams, filterState } = useCommercialFilters();

  const { data, loading, error, reload } = useCommercialResource(
    (signal) =>
      getSalesOrderOtdLineDetail(
        branch,
        orderNumber,
        lineItem,
        {
          start_date: apiParams.start_date,
          end_date: apiParams.end_date,
          customer_segment: apiParams.customer_segment,
        },
        signal
      ),
    [
      branch,
      orderNumber,
      lineItem,
      apiParams.start_date,
      apiParams.end_date,
      apiParams.customer_segment,
    ]
  );

  const line = data?.line;
  const initialLoadingProgress = useLoadingProgress(
    loading && !line,
    EMPTY_REQUEST_PROGRESS
  );
  const backPath = appendFiltersToPath(COMMERCIAL_ROUTES.salesOrderOtd, filterState);

  const invoicedLabel = useMemo(() => {
    if (!line) return "—";
    return line.invoice_date ? "Sim" : "Não";
  }, [line]);

  return (
    <div className="dashboard-commercial dashboard-page">
      <header className="dc-page-header dc-screen-only">
        <div className="dc-page-header__brand">
          <button
            type="button"
            className="dc-ghost-btn dc-detail-back"
            onClick={() => navigateCommercialBack(backPath, filterState)}
          >
            <ArrowLeft size={16} />
            Voltar ao painel OTD
          </button>
          <div>
            <p className="dc-eyebrow">DELPI • Comercial • OTD</p>
            <h1>
              Pedido {orderNumber} · linha {lineItem}
            </h1>
            <span className="dc-page-subtitle">
              Unidade {formatOperationalUnitCode(branch)} · SC5/SC6 TOTVS
            </span>
          </div>
        </div>
        <div className="dc-header-actions">
          <button className="dc-primary-btn" type="button" onClick={reload}>
            Atualizar
          </button>
        </div>
      </header>

      <TotvsSourceBanner />

      {error ? (
        <div className="dc-state dc-state--error" role="alert">
          <p>{error}</p>
          <button className="dc-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {loading && !line ? (
        <LoadingActivityCard
          title="Carregando linha do pedido"
          description="Consultando SC6, cliente e produto."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      {line ? (
        <>
          <section className="dc-kpi-grid">
            <KpiCard
              title="Status OTD"
              value={line.status === "on_time" ? "No prazo" : "Atrasado"}
              icon={<PackageCheck size={22} />}
            />
            <KpiCard
              title="Entrega prometida"
              value={formatDisplayDate(line.promised_date)}
              icon={<Truck size={22} />}
            />
            <KpiCard
              title="Faturamento"
              value={formatDisplayDate(line.invoice_date) || "Não faturado"}
              subtitle={invoicedLabel === "Sim" ? "Linha faturada" : "Aguardando faturamento"}
              icon={<Truck size={22} />}
            />
            <KpiCard
              title="Dias vs. prazo"
              value={formatInteger(line.days_diff)}
              subtitle={
                line.status === "late"
                  ? "Após a data prometida"
                  : "Dentro ou antes do prazo"
              }
              icon={<PackageCheck size={22} />}
            />
          </section>

          <DetailCard title="Pedido de venda" titleHint={COMMERCIAL_HELP_TOOLTIPS.otd.detail.order}>
            <DetailFieldGrid
              fields={[
                { label: "Unidade", value: formatOperationalUnitCode(line.branch) },
                { label: "Pedido", value: line.order_number },
                { label: "Linha", value: line.line_item },
                { label: "Cliente", value: line.customer_name ?? line.customer_code ?? "—" },
                { label: "Código cliente", value: line.customer_code ?? "—" },
                { label: "Qtd. vendida", value: formatDecimal(line.qty_sold) },
                { label: "Qtd. entregue", value: formatDecimal(line.qty_delivered) },
              ]}
            />
          </DetailCard>

          <DetailCard title="Produto" titleHint={COMMERCIAL_HELP_TOOLTIPS.otd.detail.product}>
            <DetailFieldGrid
              fields={[
                { label: "Código", value: line.product_code ?? "—" },
                { label: "Descrição", value: line.product_description ?? "—" },
              ]}
            />
          </DetailCard>
        </>
      ) : null}
    </div>
  );
}
