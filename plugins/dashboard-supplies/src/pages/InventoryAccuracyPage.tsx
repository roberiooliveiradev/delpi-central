import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowDownCircle,
  ArrowUpCircle,
  CheckCircle2,
  ClipboardCheck,
  XCircle,
} from "lucide-react";
import type { DataTableSelection } from "@delpi/plugin-ui/index";

import {
  getInventoryAccuracyItems,
  getInventoryAccuracySummary,
  type InventoryAccuracyParams,
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
import type { InventoryAccuracyItem } from "../types/supplies";
import { GHOST_BTN } from "../ui/ghostChrome";
import { formatBranchFilterLabel } from "../utils/branchClientFilters";
import {
  formatDisplayDate,
  formatPeriodLabel,
  getPreviousCompetenceValue,
  inputDateToApi,
  monthKeyToLabel,
} from "../utils/dates";
import {
  formatCurrency,
  formatDecimal,
  formatInteger,
  formatPercent,
} from "../utils/format";

type InventoryAccuracyPageProps = { pathname?: string };

const COMPETENCE_PATTERN = /^\d{4}-\d{2}$/;
const EXPORT_MAX_ROWS = 5000;

const COLUMN_PREFERENCES_KEY = "supplies.inventory-accuracy.columns";
const COLUMN_WIDTHS_KEY = "supplies.inventory-accuracy.columnWidths";
const FONT_SIZE_KEY = "supplies.inventory-accuracy.fontSize";
const VIEW_LAYOUT_KEY = "supplies.inventory-accuracy.viewLayout";

const OUTCOME_LABELS: Record<string, string> = {
  accurate: "Correta",
  divergent: "Divergente",
  excluded: "Excluída",
};

const OUTCOME_OPTIONS = [
  { value: "accurate", label: "Corretas" },
  { value: "divergent", label: "Divergentes" },
  { value: "excluded", label: "Excluídas" },
];

function outcomeLabel(outcome: string | null | undefined): string {
  if (!outcome) return "—";
  return OUTCOME_LABELS[outcome] ?? outcome;
}

function itemToExportRecord(row: InventoryAccuracyItem) {
  return {
    count_date: formatDisplayDate(row.count_date),
    product_code: row.product_code,
    description: row.description ?? "",
    branch: row.branch,
    warehouse: row.warehouse,
    counted: row.counted_quantity,
    theoretical: row.theoretical_quantity,
    divergence: row.divergence_quantity,
    outcome: outcomeLabel(row.outcome),
    document: row.inventory_document ?? "",
  };
}

function selectionCount(selection: DataTableSelection | null): number {
  if (!selection) return 0;
  if (selection.kind === "row") return selection.indices.length;
  if (selection.kind === "column") return selection.keys.length;
  return selection.cells.length;
}

export function InventoryAccuracyPage({
  pathname,
}: InventoryAccuracyPageProps) {
  const {
    dateStart,
    dateEnd,
    competence,
    branches,
    apiBranches,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    filterState,
  } = useSuppliesFilters({
    defaultPeriod: { competence: getPreviousCompetenceValue() },
  });

  const [outcomeFilter, setOutcomeFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const debouncedSearch = useDebouncedValue(searchInput.trim(), 400);
  const [selection, setSelection] = useState<DataTableSelection | null>(null);
  const [visibleColumnKeys, setVisibleColumnKeys] = useState<string[]>([]);
  const { columnWidths, onColumnWidthsChange } =
    useTableColumnWidths(COLUMN_WIDTHS_KEY);

  const serverTable = useServerTable({
    defaultSortKey: "count_date",
    defaultSortDirection: "desc",
  });

  useEffect(() => {
    serverTable.resetPage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch, outcomeFilter, dateStart, dateEnd, competence, branches]);

  // `competence` é a competência canônica: quando preenchida, governa o
  // período enviado (o FilterBar deriva as datas do mês selecionado).
  const competenceParam = COMPETENCE_PATTERN.test(competence)
    ? competence
    : undefined;

  const baseParams = useMemo<InventoryAccuracyParams>(
    () =>
      competenceParam
        ? { month: competenceParam, branches: apiBranches }
        : {
            start_date: inputDateToApi(dateStart),
            end_date: inputDateToApi(dateEnd),
            branches: apiBranches,
          },
    [competenceParam, dateStart, dateEnd, apiBranches]
  );

  const { data, loading, refreshing, requestProgress, error, reload } =
    useSuppliesResource(
      (signal) => getInventoryAccuracySummary(baseParams, signal),
      [baseParams]
    );

  const itemsParams = useMemo<InventoryAccuracyParams>(
    () => ({
      ...baseParams,
      outcome: outcomeFilter || undefined,
      search: debouncedSearch || undefined,
      page: serverTable.query.page,
      page_size: serverTable.query.pageSize,
      sort: serverTable.query.sortKey
        ? `${serverTable.query.sortKey}_${serverTable.query.sortDirection}`
        : "count_date_desc",
    }),
    [baseParams, outcomeFilter, debouncedSearch, serverTable.query]
  );

  const items = useSuppliesResource(
    (signal) => getInventoryAccuracyItems(itemsParams, signal),
    [itemsParams]
  );

  const periodLabel = competenceParam
    ? monthKeyToLabel(competenceParam)
    : formatPeriodLabel(dateStart, dateEnd);
  const branchLabel = formatBranchFilterLabel(branches);

  const isBusy = loading || refreshing;
  const unavailable = data?.summary.status === "unavailable";

  const columns = useMemo<DataTableColumn<InventoryAccuracyItem>[]>(
    () => [
      {
        key: "count_date",
        header: "Data",
        sortable: true,
        render: (row) => formatDisplayDate(row.count_date),
      },
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
        key: "counted",
        header: "Contado",
        className: "ds-table__col--numeric",
        render: (row) =>
          `${formatDecimal(row.counted_quantity)} ${
            row.unit_of_measure ?? ""
          }`.trim(),
      },
      {
        key: "theoretical",
        header: "Teórico",
        className: "ds-table__col--numeric",
        render: (row) =>
          `${formatDecimal(row.theoretical_quantity)} ${
            row.unit_of_measure ?? ""
          }`.trim(),
      },
      {
        key: "divergence",
        header: "Divergência",
        className: "ds-table__col--numeric",
        render: (row) => formatDecimal(row.divergence_quantity),
      },
      {
        key: "outcome",
        header: "Resultado",
        render: (row) => outcomeLabel(row.outcome),
      },
      {
        key: "document",
        header: "Ajuste",
        render: (row) => row.inventory_document ?? "—",
      },
    ],
    []
  );

  const selectedCount = selectionCount(selection);
  const activeFilterCount =
    (outcomeFilter ? 1 : 0) + (debouncedSearch ? 1 : 0);

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
    setOutcomeFilter("");
    setSearchInput("");
  }, []);

  const resolveExportPayload =
    useCallback(async (): Promise<TableExportPayload> => {
      const all: InventoryAccuracyItem[] = [];
      const pageSize = 500;
      let page = 1;
      let total = Number.MAX_SAFE_INTEGER;
      while (all.length < total && all.length < EXPORT_MAX_ROWS) {
        const res = await getInventoryAccuracyItems({
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
        title: "Acuracidade do inventário",
        columns: exportColumns,
        rows: all.map(itemToExportRecord),
      };
    }, [itemsParams, columns, visibleColumnKeys]);

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        title="Acuracidade do inventário"
        subtitle="Contagens oficiais avaliadas pelo processamento do inventário"
        currentPath={pathname ?? SUPPLIES_ROUTES.inventoryAccuracy}
        filterState={filterState}
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        location=""
        showLocationFilter={false}
        onCompetenceChange={setCompetence}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
        onLocationChange={() => {}}
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
        refreshTitle="Atualizando acuracidade"
      />

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Acuracidade"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.inventoryAccuracy}
          value={formatPercent(data?.summary.accuracy_percentage)}
          subtitle={`${periodLabel} · ${branchLabel} · universo: contagens oficiais`}
          icon={<ClipboardCheck size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Contagens corretas"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.accuracyAccurate}
          value={formatInteger(data?.summary.accurate_count)}
          subtitle={
            data
              ? `de ${formatInteger(
                  data.summary.evaluable_count_total
                )} avaliáveis`
              : "Processadas sem ajuste"
          }
          icon={<CheckCircle2 size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Contagens divergentes"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.accuracyDivergent}
          value={formatInteger(data?.summary.divergent_count)}
          subtitle={
            data
              ? `${formatInteger(
                  data.summary.valid_count_total
                )} válidas · ${formatInteger(
                  data.summary.valid_count_total -
                    data.summary.evaluable_count_total
                )} excluídas do denominador`
              : "Processadas com ajuste"
          }
          icon={<XCircle size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Cobertura avaliável"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.accuracyCoverage}
          value={formatPercent(data?.summary.coverage_percentage)}
          subtitle={
            data
              ? `${formatInteger(
                  data.summary.evaluable_count_total
                )} de ${formatInteger(
                  data.summary.valid_count_total
                )} contagens válidas`
              : "Avaliáveis ÷ válidas"
          }
          icon={<ClipboardCheck size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Ajustes de furo"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.accuracyShortage}
          value={formatCurrency(data?.summary.shortage_value_total)}
          subtitle="Saídas de inventário (RE0)"
          icon={<ArrowDownCircle size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Ajustes de sobra"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.accuracySurplus}
          value={formatCurrency(data?.summary.surplus_value_total)}
          subtitle="Entradas de inventário (DE0)"
          icon={<ArrowUpCircle size={22} />}
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
        title="Detalhamento das contagens"
        columns={columns}
        rows={items.data?.items ?? []}
        rowKey={(row) =>
          `${row.branch}-${row.product_code}-${row.warehouse}-${row.count_date}-${row.counted_quantity}`
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
              id: "count_date",
              label: "Data",
              value: formatDisplayDate(row.count_date),
            },
            {
              id: "counted",
              label: "Contado",
              value: `${formatDecimal(row.counted_quantity)} ${
                row.unit_of_measure ?? ""
              }`.trim(),
            },
            {
              id: "theoretical",
              label: "Teórico",
              value: `${formatDecimal(row.theoretical_quantity)} ${
                row.unit_of_measure ?? ""
              }`.trim(),
            },
            {
              id: "divergence",
              label: "Divergência",
              value: formatDecimal(row.divergence_quantity),
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
              id: "document",
              label: "Ajuste",
              value: row.inventory_document ?? "—",
            },
          ];
          return (
            <DataRecordCard
              title={row.product_code}
              subtitle={row.description ?? "—"}
              status={outcomeLabel(row.outcome)}
              fields={cardFields}
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
              payload={{
                title: "Acuracidade do inventário",
                columns: [],
                rows: [],
              }}
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
              label="Resultado"
              hint={SUPPLIES_HELP_TOOLTIPS.filters.accuracyOutcome}
              value={outcomeFilter}
              onChange={handleTableChange(setOutcomeFilter)}
              options={OUTCOME_OPTIONS}
              allowEmpty
              emptyLabel="Todos"
            />
          </FiltersRow>
        }
      />

      {data ? (
        <p className="ds-footnote">
          Divergência = teórico − contado (positivo = falta, negativo =
          sobra) · Acuracidade mede apenas o universo contado oficialmente
          no período, não o estoque total
          {data.exclusions.pending_processing > 0 ||
          data.exclusions.cancelled > 0
            ? ` · ${formatInteger(
                data.exclusions.pending_processing
              )} pendentes de processamento e ${formatInteger(
                data.exclusions.cancelled
              )} canceladas ficam fora das válidas`
            : ""}
          .
        </p>
      ) : null}
    </div>
  );
}
