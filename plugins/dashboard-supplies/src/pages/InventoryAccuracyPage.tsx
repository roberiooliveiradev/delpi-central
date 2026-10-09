import { useEffect, useMemo, useState } from "react";
import {
  ArrowDownCircle,
  ArrowUpCircle,
  CheckCircle2,
  ClipboardCheck,
  XCircle,
} from "lucide-react";
import { ToolbarSelectField } from "@delpi/plugin-ui/index";

import {
  getInventoryAccuracyItems,
  getInventoryAccuracySummary,
  type InventoryAccuracyParams,
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
import type { InventoryAccuracyItem } from "../types/supplies";
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

const OUTCOME_LABELS: Record<string, string> = {
  accurate: "Correta",
  divergent: "Divergente",
  excluded: "Excluída",
};

const OUTCOME_OPTIONS = [
  { value: "accurate", label: "Corretas" },
  { value: "divergent", label: "Divergentes" },
  { value: "excluded", label: "Excluídas" },
] as const;

function outcomeLabel(outcome: string | null | undefined): string {
  if (!outcome) return "—";
  return OUTCOME_LABELS[outcome] ?? outcome;
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
          <ToolbarSelectField
            label="Resultado"
            title={SUPPLIES_HELP_TOOLTIPS.filters.accuracyOutcome}
            value={outcomeFilter}
            onChange={setOutcomeFilter}
            options={OUTCOME_OPTIONS}
            placeholderOption="Todos"
          />
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
