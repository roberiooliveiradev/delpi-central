import { useEffect, useMemo, useState } from "react";
import { ClipboardCheck, Percent, Scale, TriangleAlert } from "lucide-react";

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
import { useCompetenceLinkedDates } from "../hooks/useCompetenceLinkedDates";
import { useServerTable } from "../hooks/useServerTable";
import { useSuppliesResource } from "../hooks/useSuppliesResource";
import type { InventoryAccuracyItem } from "../types/supplies";
import {
  formatBranchFilterLabel,
  resolveApiBranch,
} from "../utils/branchClientFilters";
import {
  competenceToDateRange,
  isValidCompetence,
} from "../utils/competenceFilters";
import {
  formatDisplayDate,
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
import { readSuppliesFilters } from "../utils/filterUrl";

type InventoryAccuracyPageProps = { pathname?: string };

const OUTCOME_LABELS: Record<string, string> = {
  accurate: "Correta",
  divergent: "Divergente",
  excluded: "Excluída",
};

const OUTCOME_OPTIONS = [
  { value: "", label: "Todos os resultados" },
  { value: "accurate", label: "Corretas" },
  { value: "divergent", label: "Divergentes" },
  { value: "excluded", label: "Excluídas" },
] as const;

const EXCLUSION_LABELS: Record<string, string> = {
  pending_processing: "Pendente de processamento",
};

function outcomeLabel(outcome: string | null | undefined): string {
  if (!outcome) return "—";
  return OUTCOME_LABELS[outcome] ?? outcome;
}

export function InventoryAccuracyPage({
  pathname,
}: InventoryAccuracyPageProps) {
  const initialCompetence = useMemo(
    () => getPreviousCompetenceValue(),
    []
  );
  const initialRange = useMemo(
    () => competenceToDateRange(initialCompetence),
    [initialCompetence]
  );

  const {
    dateStart,
    dateEnd,
    competence,
    setDateStart,
    setDateEnd,
    setCompetence,
  } = useCompetenceLinkedDates({
    dateStart: initialRange.dateStart,
    dateEnd: initialRange.dateEnd,
    competence: initialCompetence,
  });
  const [branches, setBranches] = useState(
    () => readSuppliesFilters().branches
  );
  const [outcomeFilter, setOutcomeFilter] = useState("");

  const serverTable = useServerTable({
    defaultSortKey: "count_date",
    defaultSortDirection: "desc",
  });

  useEffect(() => {
    serverTable.resetPage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [outcomeFilter, dateStart, dateEnd, competence, branches]);

  const baseParams = useMemo<InventoryAccuracyParams>(() => {
    const branch = resolveApiBranch(branches);
    if (competence && isValidCompetence(competence)) {
      return { month: competence, branch };
    }
    return {
      start_date: inputDateToApi(dateStart),
      end_date: inputDateToApi(dateEnd),
      branch,
    };
  }, [competence, dateStart, dateEnd, branches]);

  const { data, loading, refreshing, requestProgress, error, reload } =
    useSuppliesResource(
      (signal) => getInventoryAccuracySummary(baseParams, signal),
      [baseParams]
    );

  const itemsParams = useMemo<InventoryAccuracyParams>(
    () => ({
      ...baseParams,
      outcome: outcomeFilter || undefined,
      page: serverTable.query.page,
      page_size: serverTable.query.pageSize,
      sort: serverTable.query.sortKey
        ? `${serverTable.query.sortKey}_${serverTable.query.sortDirection}`
        : "count_date_desc",
    }),
    [baseParams, outcomeFilter, serverTable.query]
  );

  const items = useSuppliesResource(
    (signal) => getInventoryAccuracyItems(itemsParams, signal),
    [itemsParams]
  );

  const branchLabel = formatBranchFilterLabel(branches);
  const periodLabel = data?.reference.reference_month
    ? `Competência ${monthKeyToLabel(data.reference.reference_month)}`
    : data
      ? `${formatDisplayDate(data.reference.period_start)} a ${formatDisplayDate(
          data.reference.period_end_exclusive
        )} (exclusivo)`
      : "Último mês fechado";

  const isBusy = loading || refreshing;
  const unavailable = data?.summary.status === "unavailable";

  const columns = useMemo<DataTableColumn<InventoryAccuracyItem>[]>(
    () => [
      {
        key: "count_date",
        header: "Data",
        sortable: true,
        sortKey: "count_date",
        render: (row) => formatDisplayDate(row.count_date),
      },
      {
        key: "product_code",
        header: "Produto",
        sortable: true,
        sortKey: "product_code",
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
        key: "counted_quantity",
        header: "Contado",
        className: "ds-table__col--numeric",
        render: (row) =>
          `${formatDecimal(row.counted_quantity, 3)} ${
            row.unit_of_measure ?? ""
          }`.trim(),
      },
      {
        key: "theoretical_quantity",
        header: "Teórico",
        className: "ds-table__col--numeric",
        render: (row) => formatDecimal(row.theoretical_quantity, 3),
      },
      {
        key: "divergence_quantity",
        header: "Divergência",
        className: "ds-table__col--numeric",
        render: (row) => formatDecimal(row.divergence_quantity, 3),
      },
      {
        key: "outcome",
        header: "Resultado",
        render: (row) =>
          row.outcome === "excluded" && row.exclusion_reason
            ? `${outcomeLabel(row.outcome)} · ${
                EXCLUSION_LABELS[row.exclusion_reason] ??
                row.exclusion_reason
              }`
            : outcomeLabel(row.outcome),
      },
      {
        key: "inventory_document",
        header: "Doc. inventário",
        render: (row) => row.inventory_document ?? "—",
      },
    ],
    []
  );

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        title="Acuracidade do inventário"
        subtitle="Contagens oficiais avaliadas pelo processamento Protheus (MATA270)"
        currentPath={pathname ?? SUPPLIES_ROUTES.inventoryAccuracy}
        filterState={{
          dateStart,
          dateEnd,
          competence,
          branches,
          location: "",
        }}
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
        onLocationChange={() => undefined}
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
        refreshTitle="Atualizando acuracidade de inventário"
      />

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Acuracidade"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.inventoryAccuracy}
          value={formatPercent(data?.summary.accuracy_percentage)}
          subtitle={`${branchLabel} · ${periodLabel}`}
          icon={<ClipboardCheck size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Contagens corretas"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.accuracyAccurate}
          value={formatInteger(data?.summary.accurate_count)}
          subtitle={
            data
              ? `${formatInteger(data.summary.evaluable_count_total)} avaliáveis`
              : "Contagens processadas sem ajuste"
          }
          icon={<Percent size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Contagens divergentes"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.accuracyDivergent}
          value={formatInteger(data?.summary.divergent_count)}
          subtitle={
            data
              ? `${formatInteger(data.exclusions.pending_processing)} pendentes · ${formatInteger(
                  data.exclusions.cancelled
                )} canceladas`
              : "Contagens com ajuste INVENT"
          }
          icon={<TriangleAlert size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Faltas × sobras"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.accuracyShortage}
          value={
            data
              ? `${formatCurrency(data.summary.shortage_value_total)} · ${formatCurrency(
                  data.summary.surplus_value_total
                )}`
              : "—"
          }
          subtitle="Ajustes RE0 (furos) e DE0 (sobras) do período"
          icon={<Scale size={22} />}
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
        title="Eventos de contagem do período"
        columns={columns}
        rows={items.data?.items ?? []}
        rowKey={(row) =>
          `${row.branch}-${row.product_code}-${row.warehouse}-${row.count_date}`
        }
        loading={items.loading}
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
        headerActions={
          <select
            aria-label="Filtrar por resultado da contagem"
            value={outcomeFilter}
            onChange={(event) => setOutcomeFilter(event.target.value)}
          >
            {OUTCOME_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        }
      />

      {data ? (
        <p className="ds-footnote">
          Período: {formatDisplayDate(data.reference.period_start)} a{" "}
          {formatDisplayDate(data.reference.period_end_exclusive)} (exclusivo)
          {data.reference.period_closed
            ? " · mês fechado"
            : " · período ainda aberto"}
          {" · "}
          {formatPercent(data.summary.coverage_percentage)} de cobertura ·
          Fonte: veredito oficial MATA270 (tolerância zero).
        </p>
      ) : null}
    </div>
  );
}
