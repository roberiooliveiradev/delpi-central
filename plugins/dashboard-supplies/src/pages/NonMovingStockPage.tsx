import { useEffect, useMemo, useState } from "react";
import { PackageX, Percent, ShieldAlert, TrendingDown } from "lucide-react";
import { ToolbarSelectField } from "@delpi/plugin-ui/index";

import {
  getNonMovingStockItems,
  getNonMovingStockSummary,
  type NonMovingStockParams,
} from "../api/suppliesApi";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { SuppliesStatusAlerts } from "../components/SuppliesStatusAlerts";
import { SUPPLIES_ROUTES } from "../constants/routes";
import { SUPPLIES_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useServerTable } from "../hooks/useServerTable";
import { useSuppliesFilters } from "../hooks/useSuppliesFilters";
import { useSuppliesResource } from "../hooks/useSuppliesResource";
import type { NonMovingStockItem } from "../types/supplies";
import { formatBranchFilterLabel } from "../utils/branchClientFilters";
import {
  formatDisplayDate,
  formatPeriodLabel,
  getRollingMonthsAgoInputValue,
  getTodayInputValue,
  inputDateToApi,
} from "../utils/dates";
import {
  formatCurrency,
  formatInteger,
  formatPercent,
} from "../utils/format";

type NonMovingStockPageProps = { pathname?: string };

const APPROVED_WAREHOUSES = new Set(["01", "99"]);

const STATUS_LABELS: Record<string, string> = {
  WITH_CONSUMPTION: "Com consumo",
  NO_CONSUMPTION_12M: "Sem giro (12m)",
  NO_CONSUMPTION_IN_PERIOD: "Sem giro no período",
  INSUFFICIENT_HISTORY: "Histórico insuficiente",
};

const STATUS_OPTIONS = [
  { value: "NO_CONSUMPTION_12M", label: "Sem giro (12m)" },
  { value: "NO_CONSUMPTION_IN_PERIOD", label: "Sem giro no período" },
  { value: "WITH_CONSUMPTION", label: "Com consumo" },
  { value: "INSUFFICIENT_HISTORY", label: "Histórico insuficiente" },
] as const;

const BLOCKED_OPTIONS = [
  { value: "true", label: "Bloqueados" },
  { value: "false", label: "Não bloqueados" },
] as const;

const WAREHOUSE_OPTIONS = [
  { value: "01", label: "Armazém 01" },
  { value: "99", label: "Armazém 99" },
] as const;

function statusLabel(status: string | null | undefined): string {
  if (!status) return "—";
  return STATUS_LABELS[status] ?? status;
}

export function NonMovingStockPage({ pathname }: NonMovingStockPageProps) {
  const {
    dateStart,
    dateEnd,
    competence,
    branches,
    location,
    apiBranches,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    setLocation,
    filterState,
  } = useSuppliesFilters({
    defaultPeriod: {
      dateStart: getRollingMonthsAgoInputValue(12),
      dateEnd: getTodayInputValue(),
      competence: "",
    },
  });

  const [statusFilter, setStatusFilter] = useState("");
  const [blockedFilter, setBlockedFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const debouncedSearch = useDebouncedValue(searchInput.trim(), 400);

  const serverTable = useServerTable({
    defaultSortKey: "stock_value",
    defaultSortDirection: "desc",
  });

  useEffect(() => {
    serverTable.resetPage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    debouncedSearch,
    statusFilter,
    blockedFilter,
    dateStart,
    dateEnd,
    branches,
    location,
  ]);

  const isDefaultWindow =
    dateStart === getRollingMonthsAgoInputValue(12) &&
    dateEnd === getTodayInputValue();

  const warehouse = APPROVED_WAREHOUSES.has(location) ? location : "";

  const baseParams = useMemo<NonMovingStockParams>(
    () => ({
      ...(isDefaultWindow
        ? {}
        : {
            start_date: inputDateToApi(dateStart),
            end_date: inputDateToApi(dateEnd),
          }),
      branches: apiBranches,
      warehouse: warehouse || undefined,
    }),
    [isDefaultWindow, dateStart, dateEnd, apiBranches, warehouse]
  );

  const { data, loading, refreshing, requestProgress, error, reload } =
    useSuppliesResource(
      (signal) => getNonMovingStockSummary(baseParams, signal),
      [baseParams]
    );

  const itemsParams = useMemo<NonMovingStockParams>(
    () => ({
      ...baseParams,
      turnover_status: statusFilter || undefined,
      blocked:
        blockedFilter === "" ? undefined : blockedFilter === "true",
      search: debouncedSearch || undefined,
      page: serverTable.query.page,
      page_size: serverTable.query.pageSize,
      sort: serverTable.query.sortKey
        ? `${serverTable.query.sortKey}_${serverTable.query.sortDirection}`
        : "stock_value_desc",
    }),
    [
      baseParams,
      statusFilter,
      blockedFilter,
      debouncedSearch,
      serverTable.query,
    ]
  );

  const items = useSuppliesResource(
    (signal) => getNonMovingStockItems(itemsParams, signal),
    [itemsParams]
  );

  const periodLabel = isDefaultWindow
    ? "Últimos 12 meses"
    : formatPeriodLabel(dateStart, dateEnd);
  const branchLabel = formatBranchFilterLabel(branches);
  const locationLabel = warehouse ? `Armazém ${warehouse}` : "01 + 99";

  const isBusy = loading || refreshing;
  const unavailable = data?.summary.status === "unavailable";

  const columns = useMemo<DataTableColumn<NonMovingStockItem>[]>(
    () => [
      {
        key: "product_code",
        header: "Produto",
        sortable: true,
        render: (row) => row.product_code,
      },
      {
        key: "description",
        header: "Descrição",
        render: (row) => row.description ?? "—",
      },
      {
        key: "branch",
        header: "Filial",
        render: (row) => row.branch,
      },
      {
        key: "warehouse",
        header: "Armazém",
        render: (row) => row.warehouse,
      },
      {
        key: "quantity",
        header: "Quantidade",
        className: "ds-table__col--numeric",
        sortable: true,
        render: (row) =>
          `${formatInteger(row.quantity)} ${row.unit_of_measure ?? ""}`.trim(),
      },
      {
        key: "stock_value",
        header: "Valor (R$)",
        className: "ds-table__col--numeric",
        sortable: true,
        render: (row) =>
          row.unit_cost === 0
            ? `${formatCurrency(row.stock_value)} · sem custo`
            : formatCurrency(row.stock_value),
      },
      {
        key: "blocked",
        header: "Bloqueado",
        render: (row) => (row.blocked ? "Sim" : "—"),
      },
      {
        key: "turnover_status",
        header: "Status",
        render: (row) => statusLabel(row.turnover_status),
      },
      {
        key: "last_utilization",
        header: "Última utilização",
        sortable: true,
        render: (row) => formatDisplayDate(row.last_effective_utilization),
      },
    ],
    []
  );

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        title="Matérias-primas sem giro"
        subtitle="Estoque de MP sem utilização efetiva na janela de consumo"
        currentPath={pathname ?? SUPPLIES_ROUTES.nonMovingStock}
        filterState={filterState}
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        location={location}
        showLocationFilter={false}
        onCompetenceChange={setCompetence}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
        onLocationChange={setLocation}
        onRefresh={reload}
        refreshing={refreshing}
      />
      <SuppliesStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={data !== null}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando estoque sem giro"
      />

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Estoque sem giro"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.nonMovingStockValue}
          value={formatCurrency(data?.summary.no_consumption_stock_value)}
          subtitle={`${branchLabel} · ${locationLabel} · ${periodLabel}`}
          icon={<PackageX size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="% sem giro (financeiro)"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.nonMovingPercentage}
          value={formatPercent(data?.summary.non_moving_percentage)}
          subtitle={
            data
              ? `${formatCurrency(
                  data.summary.no_consumption_stock_value
                )} de ${formatCurrency(
                  data.summary.evaluable_stock_value
                )} avaliável · ${formatInteger(
                  data.counts.no_consumption
                )} produtos`
              : "Valor sem giro ÷ valor avaliável"
          }
          icon={<TrendingDown size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Cobertura histórica"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.nonMovingCoverage}
          value={formatPercent(data?.summary.coverage_percentage)}
          subtitle={
            data
              ? `${formatCurrency(
                  data.summary.insufficient_history_stock_value
                )} sem histórico (${formatInteger(
                  data.counts.insufficient_history
                )} produtos)`
              : "Estoque avaliável ÷ elegível"
          }
          icon={<Percent size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Materiais bloqueados"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.blockedStockValue}
          value={formatCurrency(data?.summary.blocked_stock_value)}
          subtitle={
            data
              ? `${formatInteger(data.counts.blocked_products)} produtos · ${formatCurrency(
                  data.summary.blocked_no_consumption_stock_value
                )} sem giro`
              : "B1_MSBLQL no universo"
          }
          icon={<ShieldAlert size={22} />}
          loading={isBusy}
        />
      </section>

      {unavailable ? (
        <section className="ds-panel" role="status">
          <p>
            Indicador indisponível para o recorte selecionado
            {data?.summary.unavailable_reason
              ? ` (${data.summary.unavailable_reason})`
              : ""}
            .
          </p>
        </section>
      ) : null}

      <DataTableSection
        title="Materiais por situação de giro"
        columns={columns}
        rows={items.data?.items ?? []}
        rowKey={(row) =>
          `${row.branch}-${row.product_code}-${row.warehouse}`
        }
        loading={items.loading}
        refreshing={items.refreshing}
        searchPlaceholder="Buscar por código ou descrição…"
        searchHint={SUPPLIES_HELP_TOOLTIPS.filters.tableSearch}
        serverSearch={{ value: searchInput, onChange: setSearchInput }}
        serverPagination={{
          page: items.data?.page ?? serverTable.query.page,
          pageSize: items.data?.page_size ?? serverTable.query.pageSize,
          total: items.data?.total ?? 0,
          onPageChange: serverTable.setPage,
          onPageSizeChange: serverTable.setPageSize,
        }}
        serverSort={{
          sortKey: serverTable.query.sortKey,
          sortDirection: serverTable.query.sortDirection,
          onSortChange: serverTable.handleSortChange,
        }}
        toolbarFilters={
          <>
            <ToolbarSelectField
              label="Status de giro"
              title={SUPPLIES_HELP_TOOLTIPS.filters.turnoverStatus}
              value={statusFilter}
              onChange={setStatusFilter}
              options={STATUS_OPTIONS}
              placeholderOption="Todos"
            />
            <ToolbarSelectField
              label="Bloqueio"
              title={SUPPLIES_HELP_TOOLTIPS.filters.blockedFilter}
              value={blockedFilter}
              onChange={setBlockedFilter}
              options={BLOCKED_OPTIONS}
              placeholderOption="Todos"
            />
            <ToolbarSelectField
              label="Armazém"
              title={SUPPLIES_HELP_TOOLTIPS.filters.warehouse}
              value={warehouse}
              onChange={setLocation}
              options={WAREHOUSE_OPTIONS}
              placeholderOption="Todos"
            />
          </>
        }
      />

      {data ? (
        <p className="ds-footnote">
          Janela de consumo:{" "}
          {formatDisplayDate(data.reference.consumption_window_start)} a{" "}
          {formatDisplayDate(data.reference.consumption_window_end)} ·
          Valoração: estoque atual (SB2) · Produto × filial para giro,
          produto × filial × armazém para valor
          {data.counts.zero_cost_items > 0
            ? ` · ${formatInteger(
                data.counts.zero_cost_items
              )} itens com custo médio zero (valor não mensurável)`
            : ""}
          .
        </p>
      ) : null}
    </div>
  );
}
