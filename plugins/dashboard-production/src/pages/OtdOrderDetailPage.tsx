import { useMemo } from "react";
import {
  ArrowLeft,
  Boxes,
  ClipboardList,
  Factory,
  Package,
  Truck,
} from "lucide-react";

import { useIntermediateOrderColumns } from "../components/IntermediateOrdersTable";
import { DataTableSection } from "../components/DataTableSection";
import { DetailCard } from "../components/DetailCard";
import { DetailFieldGrid } from "../components/DetailFieldGrid";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { OtdStatusBadge } from "../components/OtdStatusBadge";
import { ProductStructureTree } from "../components/ProductStructureTree";
import { ProductionPageHeader } from "../components/ProductionPageHeader";
import { PRODUCTION_ROUTES } from "../constants/routes";
import { useProductionOrderDetail } from "../hooks/useProductionOrderDetail";
import { useServerTable } from "../hooks/useServerTable";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import type {
  IntermediateProductionOrderRow,
  ProductPriceItem,
  ProductStockItem,
  ProductionOrderProductType,
} from "../types/production";
import { formatDisplayDate } from "../utils/dates";
import { formatDecimal, formatInteger } from "../utils/format";
import { appendFiltersToPath, readProductionFilters } from "../utils/filterUrl";
import { navigateProduction, navigateProductionBack } from "../utils/navigation";
import { buildOtdOrderPath } from "../utils/routeParser";
import { normalizeOperationalUnitCode } from "../utils/operationalUnitLabels";
import { readProductField } from "../utils/productFields";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode } from "../utils/operationalUnitLabels";

type OtdOrderDetailPageProps = {
  productionOrder: string;
  branch?: string;
  productType?: ProductionOrderProductType;
  pathname?: string;
};

export function OtdOrderDetailPage({
  productionOrder,
  branch,
  productType,
  pathname,
}: OtdOrderDetailPageProps) {
  const filterState = readProductionFilters();
  const linkedOrdersTable = useServerTable();
  const detail = useProductionOrderDetail(productionOrder, {
    branch,
    productType,
    linkedSortBy: linkedOrdersTable.query.sortKey,
    linkedSortDir: linkedOrdersTable.query.sortDirection,
  });

  const order = detail.orderData?.order;
  const product = detail.productData?.product;
  const stockItems = detail.productData?.stock ?? [];
  const priceItems = detail.productData?.prices ?? [];

  const initialFetchProgress = useTrackedSingleFetchProgress(detail.loading);
  const initialLoadingProgress = useLoadingProgress(
    detail.loading,
    initialFetchProgress
  );

  const backPath = appendFiltersToPath(PRODUCTION_ROUTES.otd, filterState);

  const handleBack = () => {
    navigateProductionBack(backPath, filterState);
  };

  const handleIntermediateOrderClick = (row: IntermediateProductionOrderRow) => {
    const rowProductType: ProductionOrderProductType =
      row.product_type?.trim().toUpperCase() === "PA" ? "PA" : "PI";

    navigateProduction(
      buildOtdOrderPath(
        row.production_order,
        normalizeOperationalUnitCode(row.branch),
        filterState,
        rowProductType
      ),
      filterState
    );
  };

  const intermediateHint =
    detail.orderData?.link_summary
      ? `${detail.intermediateSummary.on_time} no prazo · ${detail.intermediateSummary.late} atrasadas · ${detail.intermediateSummary.open} em aberto · Nº OP ${detail.orderData.link_summary.order_number}`
      : detail.intermediateOrders.length > 0
        ? `${detail.intermediateSummary.on_time} no prazo · ${detail.intermediateSummary.late} atrasadas · ${detail.intermediateSummary.open} em aberto`
        : order?.product_type === "PI"
          ? "Demais OPs vinculadas pelo mesmo número de OP (C2_NUM)"
          : "OPs de PI vinculadas pelo mesmo número de OP (C2_NUM) da ordem do PA";

  const orderFields = useMemo(
    () =>
      order
        ? [
            {
              label: "Status OTD",
              value: <OtdStatusBadge status={order.otd_status} />,
            },
            { label: OPERATIONAL_UNIT_COLUMN_LABEL, value: formatOperationalUnitCode(order.branch) },
            { label: "OP (C2_OP)", value: order.production_order },
            { label: "Nº OP", value: order.order_number },
            { label: "Item", value: order.order_item },
            { label: "Sequência", value: order.order_sequence },
            { label: "Status OP", value: order.order_status || "—" },
            { label: "Prioridade", value: order.priority || "—" },
            { label: "Emissão", value: formatDisplayDate(order.issue_date) },
            {
              label: "Início previsto",
              value: formatDisplayDate(order.planned_start_date),
            },
            {
              label: "Entrega prevista",
              value: formatDisplayDate(order.due_date),
            },
            {
              label: "Finalização",
              value: formatDisplayDate(order.finish_date),
            },
            {
              label: "Dias (previsto × real)",
              value: formatInteger(order.days_diff),
            },
            { label: "Qtd. planejada", value: formatDecimal(order.planned_qty) },
            { label: "Qtd. produzida", value: formatDecimal(order.produced_qty) },
            { label: "Armazém", value: order.warehouse || "—" },
            {
              label: "Observação",
              value: order.observation || "—",
              wide: true,
            },
          ]
        : [],
    [order]
  );

  const productFields = useMemo(
    () => [
      { label: "Código", value: readProductField(product, "code", "B1_COD") },
      {
        label: "Descrição",
        value: readProductField(product, "description", "B1_DESC"),
        wide: true,
      },
      { label: "Tipo", value: readProductField(product, "type", "B1_TIPO") },
      { label: "Unidade", value: readProductField(product, "unit", "B1_UM") },
      { label: "Grupo", value: readProductField(product, "group", "B1_GRUPO") },
      {
        label: "Família",
        value: readProductField(product, "family", "B1_FAMILIA"),
      },
      {
        label: "Origem",
        value: readProductField(product, "origin", "B1_ORIGEM"),
      },
      {
        label: "Revisão",
        value: readProductField(product, "revision", "B1_REVISAO"),
      },
      {
        label: "NCM",
        value: readProductField(product, "ncm", "B1_POSIPI"),
      },
      {
        label: "Armazém padrão",
        value: readProductField(product, "default_warehouse", "B1_LOCPAD"),
      },
    ],
    [product]
  );

  const intermediateOrderColumns = useIntermediateOrderColumns();

  const stockColumns = useMemo(
    () => [
      {
        key: "branch",
        header: OPERATIONAL_UNIT_COLUMN_LABEL,
        render: (row: ProductStockItem) => formatOperationalUnitCode(row.branch),
      },
      {
        key: "warehouse",
        header: "Armazém",
        render: (row: ProductStockItem) => row.warehouse ?? "—",
      },
      {
        key: "balance",
        header: "Saldo",
        className: "dp-table__col--numeric",
        render: (row: ProductStockItem) => formatDecimal(row.balance as number | null),
      },
    ],
    []
  );

  const priceColumns = useMemo(
    () => [
      {
        key: "table",
        header: "Tabela",
        render: (row: ProductPriceItem) => row.table ?? "—",
      },
      {
        key: "price",
        header: "Preço",
        className: "dp-table__col--numeric",
        render: (row: ProductPriceItem) => formatDecimal(row.price as number | null),
      },
    ],
    []
  );

  const pageTitle = order
    ? `OP ${order.production_order}`
    : `OP ${productionOrder}`;

  const pageSubtitle = order
    ? `${order.product_code} · ${order.product_description} · ${formatOperationalUnitCode(order.branch)}`
    : branch
      ? formatOperationalUnitCode(branch, branch)
      : "Detalhe da ordem de produção";

  return (
    <div className="dashboard-production dashboard-page">
      <ProductionPageHeader
        title={pageTitle}
        subtitle={pageSubtitle}
        currentPath={pathname ?? PRODUCTION_ROUTES.otd}
        filterState={filterState}
        onRefresh={detail.reload}
        refreshing={detail.loading && Boolean(order)}
        actions={
          <button type="button" className="dp-ghost-btn" onClick={handleBack}>
            <ArrowLeft size={16} aria-hidden="true" />
            Voltar
          </button>
        }
      />

      <DataSourceBanner />

      {detail.error ? (
        <div className="dp-state dp-state--error" role="alert">
          <p>{detail.error}</p>
          <button
            className="dp-primary-btn"
            type="button"
            onClick={detail.reload}
          >
            Tentar novamente
          </button>
        </div>
      ) : null}

      {detail.loading && !order ? (
        <LoadingActivityCard
          title="Carregando detalhe da OP"
          description="Consultando ordem de produção, cadastro, estrutura e OPs dos intermediários."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      {order ? (
        <>
          <section className="dp-kpi-grid" aria-busy={detail.loading}>
            <KpiCard
              title="Status OTD"
              value={order.otd_status === "on_time" ? "No prazo" : order.otd_status === "late" ? "Atrasado" : "Em aberto"}
              subtitle={`Previsto ${formatDisplayDate(order.due_date)}`}
              icon={<Truck size={22} />}
              loading={detail.loading}
            />
            <KpiCard
              title="Qtd. planejada"
              value={formatDecimal(order.planned_qty)}
              subtitle={`Produzida: ${formatDecimal(order.produced_qty)}`}
              icon={<ClipboardList size={22} />}
              loading={detail.loading}
            />
            <KpiCard
              title="Dias"
              value={formatInteger(order.days_diff)}
              subtitle="Diferença entre previsto e finalização"
              icon={<Factory size={22} />}
              loading={detail.loading}
            />
            <KpiCard
              title="OPs de PI"
              value={formatInteger(detail.intermediateSummary.total)}
              subtitle={intermediateHint}
              icon={<Boxes size={22} />}
              loading={detail.loading}
            />
          </section>

          <section className="dp-detail-layout">
            <DetailCard
              title="Ordem de produção"
              hint="Cadastro SC2010 — sequência 001 preferencial"
              icon={<Factory size={20} />}
            >
              <DetailFieldGrid fields={orderFields} />
            </DetailCard>

            <DetailCard
              title="Produto"
              hint="Cadastro SB1010 e resumo operacional"
              icon={<Package size={20} />}
            >
              <DetailFieldGrid fields={productFields} />
            </DetailCard>
          </section>

          <DetailCard
            title="Estrutura do produto"
            hint="BOM / estrutura analítica com níveis aninhados"
            icon={<Boxes size={20} />}
            className="dp-detail-card--full"
          >
            <ProductStructureTree structure={detail.structureData} />
          </DetailCard>

          <DataTableSection
            title={
              order?.product_type === "PI"
                ? "OPs vinculadas (mesmo C2_NUM)"
                : "OPs dos intermediários (PI)"
            }
            hint={`${intermediateHint}. Clique em uma linha para abrir o detalhe da OP.`}
            columns={intermediateOrderColumns}
            rows={detail.intermediateOrders}
            rowKey={(row) => row.key}
            hideSearch
            emptyMessage="Nenhuma OP de PI vinculada a esta ordem do PA (mesmo C2_NUM)."
            loading={detail.loading && detail.intermediateOrders.length === 0}
            refreshing={detail.linkedOrdersRefreshing}
            serverSort={{
              sortKey: linkedOrdersTable.query.sortKey,
              sortDirection: linkedOrdersTable.query.sortDirection,
              onSortChange: linkedOrdersTable.handleSortChange,
            }}
            onRowClick={handleIntermediateOrderClick}
          />

          {stockItems.length > 0 ? (
            <DataTableSection
              title="Estoque do produto"
              hint="Saldos por unidade e armazém"
              columns={stockColumns}
              rows={stockItems}
              rowKey={(row) =>
                `${String(row.branch ?? "branch")}-${String(row.warehouse ?? "wh")}-${String(row.balance ?? "")}`
              }
              hideSearch
              pageSize={10}
            />
          ) : null}

          {priceItems.length > 0 ? (
            <DataTableSection
              title="Preços do produto"
              hint="Tabelas de preço cadastradas"
              columns={priceColumns}
              rows={priceItems}
              rowKey={(row) => `${String(row.table ?? "table")}-${String(row.price ?? "")}`}
              hideSearch
              pageSize={10}
            />
          ) : null}
        </>
      ) : null}
    </div>
  );
}
