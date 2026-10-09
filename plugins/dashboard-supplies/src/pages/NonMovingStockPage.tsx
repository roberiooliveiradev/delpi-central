import { useCallback, useEffect, useMemo, useState } from "react";
import { PackageX, Percent, ShieldAlert, TrendingDown } from "lucide-react";
import type { DataTableSelection } from "@delpi/plugin-ui/index";

import {
  getNonMovingStockItems,
  getNonMovingStockSummary,
  type NonMovingStockParams,
} from "../api/suppliesApi";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import {
  DataRecordCard,
  type DataRecordCardField,
} from "../components/DataRecordCard";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { SelectField } from "../components/SelectField";
import { FiltersRow } from "../components/dashboardFiltersUi";
import { SuppliesStatusAlerts } from "../components/SuppliesStatusAlerts";
import { SUPPLIES_ROUTES } from "../constants/routes";
import { SUPPLIES_HELP_TOOLTIPS } from "../content/helpTooltips";
import { exportAlert } from "../export/exportUtils";
import { SuppliesExportButtons } from "../export/SuppliesExportButtons";
import type { TableExportPayload } from "../export/types";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useServerTable } from "../hooks/useServerTable";
import { useSuppliesFilters } from "../hooks/useSuppliesFilters";
import { useSuppliesResource } from "../hooks/useSuppliesResource";
import { useTableColumnWidths } from "../hooks/useTableColumnWidths";
import type { NonMovingStockItem } from "../types/supplies";
import { GHOST_BTN } from "../ui/ghostChrome";
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
const EXPORT_MAX_ROWS = 5000;

const COLUMN_PREFERENCES_KEY = "supplies.non-moving-stock.columns";
const COLUMN_WIDTHS_KEY = "supplies.non-moving-stock.columnWidths";
const FONT_SIZE_KEY = "supplies.non-moving-stock.fontSize";
const VIEW_LAYOUT_KEY = "supplies.non-moving-stock.viewLayout";

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
];

const BLOCKED_OPTIONS = [
  { value: "true", label: "Bloqueados" },
  { value: "false", label: "Não bloqueados" },
];

const WAREHOUSE_OPTIONS = [
  { value: "01", label: "Armazém 01" },
  { value: "99", label: "Armazém 99" },
];

function statusLabel(status: string | null | undefined): string {
  if (!status) return "—";
  return STATUS_LABELS[status] ?? status;
}

function itemToExportRecord(row: NonMovingStockItem) {
  return {
    product_code: row.product_code,
    description: row.description ?? "",
    branch: row.branch,
    warehouse: row.warehouse,
    quantity: row.quantity,
    stock_value: row.stock_value,
    blocked: row.blocked ? "Sim" : "Não",
    turnover_status: statusLabel(row.turnover_status),
    last_utilization: formatDisplayDate(row.last_effective_utilization),
  };
}

function selectionCount(selection: DataTableSelection | null): number {
  if (!selection) return 0;
  if (selection.kind === "row") return selection.indices.length;
  if (selection.kind === "column") return selection.keys.length;
  return selection.cells.length;
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
  const [selection, setSelection] = useState<DataTableSelection | null>(null);
  const [visibleColumnKeys, setVisibleColumnKeys] = useState<string[]>([]);
  const { columnWidths, onColumnWidthsChange } =
    useTableColumnWidths(COLUMN_WIDTHS_KEY);

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
        render: (row) =>
          row.description ? (
            <span title={row.description}>{row.description}</span>
          ) : (
            "—"
          ),
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

  const selectedCount = selectionCount(selection);
  const activeFilterCount =
    (statusFilter ? 1 : 0) +
    (blockedFilter ? 1 : 0) +
    (warehouse ? 1 : 0) +
    (debouncedSearch ? 1 : 0);

  const handleTableChange = useCallback(
    <T,>(apply: (v: T) => void) =>
      (v: T) => {
        setSelection(null);
        apply(v);
      },
    []
  );

  const handleSortChange = useCallback(
    (key: string) => {
      setSelection(null);
      serverTable.handleSortChange(key);
    },
    [serverTable]
  );

  const handlePageSizeChange = useCallback(
    (size: number) => {
      setSelection(null);
      serverTable.setPageSize(size);
    },
    [serverTable]
  );

  const handlePageChange = useCallback(
    (page: number) => {
      setSelection(null);
      serverTable.setPage(page);
    },
    [serverTable]
  );

  const clearTableFilters = useCallback(() => {
    setStatusFilter("");
    setBlockedFilter("");
    setSearchInput("");
    if (warehouse) setLocation("");
  }, [warehouse, setLocation]);

  const resolveExportPayload =
    useCallback(async (): Promise<TableExportPayload> => {
      const all: NonMovingStockItem[] = [];
      const pageSize = 500;
      let page = 1;
      let total = Number.MAX_SAFE_INTEGER;
      while (all.length < total && all.length < EXPORT_MAX_ROWS) {
        const res = await getNonMovingStockItems({
          ...itemsParams,
          page,
          page_size: pageSize,
        });
        all.push(...res.items);
        total = res.total;
        if (res.items.length < pageSize) break;
        page += 1;
      }
      if (total > all.length) {
        exportAlert(
          `Exportação limitada aos primeiros ${all.length} de ${total} registros do filtro atual.`
        );
      }
      const exportColumns = columns
        .filter((column) =>
          visibleColumnKeys.length
            ? visibleColumnKeys.includes(column.key)
            : true
        )
        .map((column) => ({ key: column.key, label: column.header }));
      return {
        title: "Matérias-primas sem giro",
        columns: exportColumns,
        rows: all.map(itemToExportRecord),
      };
    }, [itemsParams, columns, visibleColumnKeys]);

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
        onLocationChange={handleTableChange(setLocation)}
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
        serverSearch={{ value: searchInput, onChange: handleTableChange(setSearchInput) }}
        serverPagination={{
          page: items.data?.page ?? serverTable.query.page,
          pageSize: items.data?.page_size ?? serverTable.query.pageSize,
          total: items.data?.total ?? 0,
          onPageChange: handlePageChange,
          onPageSizeChange: handlePageSizeChange,
        }}
        serverSort={{
          sortKey: serverTable.query.sortKey,
          sortDirection: serverTable.query.sortDirection,
          onSortChange: handleSortChange,
        }}
        selection={selection}
        onSelectionChange={setSelection}
        columnWidths={columnWidths}
        onColumnWidthsChange={onColumnWidthsChange}
        resizableColumns
        columnPreferencesKey={COLUMN_PREFERENCES_KEY}
        onVisibleColumnKeysChange={setVisibleColumnKeys}
        fontSizePreferencesKey={FONT_SIZE_KEY}
        viewLayoutPreferencesKey={VIEW_LAYOUT_KEY}
        viewLayoutMobileMaxWidthPx={768}
        renderCard={(row) => {
          const cardFields: DataRecordCardField[] = [
            {
              id: "quantity",
              label: "Quantidade",
              value: `${formatInteger(row.quantity)} ${
                row.unit_of_measure ?? ""
              }`.trim(),
            },
            {
              id: "stock_value",
              label: "Valor",
              value: formatCurrency(row.stock_value),
            },
            {
              id: "branch",
              label: "Filial",
              value: row.branch,
            },
            {
              id: "warehouse",
              label: "Armazém",
              value: row.warehouse,
            },
            {
              id: "last_utilization",
              label: "Última utilização",
              value: formatDisplayDate(row.last_effective_utilization),
            },
          ];
          return (
            <DataRecordCard
              title={row.product_code}
              subtitle={row.description ?? "—"}
              status={statusLabel(row.turnover_status)}
              fields={cardFields}
              context={row.blocked ? "Bloqueado" : undefined}
            />
          );
        }}
        toolbarExtra={
          <>
            {selectedCount > 0 ? (
              <button
                type="button"
                className="delpi-ui-table-toolbar-action"
                onClick={() => setSelection(null)}
              >
                {selectedCount} selecionada(s) nesta página · limpar
              </button>
            ) : null}
            <SuppliesExportButtons
              variant="table"
              payload={{ title: "Matérias-primas sem giro", columns: [], rows: [] }}
              resolvePayload={resolveExportPayload}
            />
          </>
        }
        toolbarFilters={
          <FiltersRow
            ariaLabel="Filtros do detalhamento"
            trailing={
              <>
                {activeFilterCount > 0 ? (
                  <span className="ds-filter-count" role="status">
                    {activeFilterCount} filtro(s) ativo(s)
                  </span>
                ) : null}
                <button
                  type="button"
                  className={GHOST_BTN}
                  onClick={clearTableFilters}
                  disabled={activeFilterCount === 0}
                >
                  Limpar filtros
                </button>
              </>
            }
          >
            <SelectField
              label="Status de giro"
              hint={SUPPLIES_HELP_TOOLTIPS.filters.turnoverStatus}
              value={statusFilter}
              onChange={handleTableChange(setStatusFilter)}
              options={STATUS_OPTIONS}
              allowEmpty
              emptyLabel="Todos"
            />
            <SelectField
              label="Bloqueio"
              hint={SUPPLIES_HELP_TOOLTIPS.filters.blockedFilter}
              value={blockedFilter}
              onChange={handleTableChange(setBlockedFilter)}
              options={BLOCKED_OPTIONS}
              allowEmpty
              emptyLabel="Todos"
            />
            <SelectField
              label="Armazém"
              hint={SUPPLIES_HELP_TOOLTIPS.filters.warehouse}
              value={warehouse}
              onChange={handleTableChange(setLocation)}
              options={WAREHOUSE_OPTIONS}
              allowEmpty
              emptyLabel="Todos"
            />
          </FiltersRow>
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
