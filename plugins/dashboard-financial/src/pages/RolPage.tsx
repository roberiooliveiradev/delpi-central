import { useMemo } from "react";
import { TrendingUp } from "lucide-react";

import { getRol } from "../api/financialApi";
import { DataSourceBanner } from "../components/DataSourceBanner";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { FinancialStatusAlerts } from "../components/FinancialStatusAlerts";
import { FINANCIAL_ROUTES } from "../constants/routes";
import { useFinancialFilters } from "../hooks/useFinancialFilters";
import { useFinancialResource } from "../hooks/useFinancialResource";
import { formatPeriodLabel } from "../utils/dates";
import { formatBranchFilterLabel } from "../utils/branchClientFilters";
import { formatCurrency } from "../utils/format";
import { FINANCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";

type RolRow = { label: string; value: number };

type RolPageProps = { pathname?: string };

export function RolPage({ pathname }: RolPageProps) {
  const {
    dateStart,
    dateEnd,
    competence,
    branches,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    apiParams,
    filterState,
  } = useFinancialFilters();

  const { data, loading, refreshing, requestProgress, error, reload } = useFinancialResource(
    (signal) => getRol(apiParams, signal),
    [apiParams.branch, apiParams.end_date, apiParams.start_date]
  );

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const breakdownRows = useMemo<RolRow[]>(() => {
    if (!data) return [];
    return [
      { label: "Faturamento bruto", value: data.gross_revenue },
      { label: "Outros valores", value: data.other_values },
      { label: "Itens sem TES", value: data.items_without_tes },
      { label: "Devoluções", value: data.returns },
      { label: "Descontos", value: data.discounts },
      { label: "ICMS", value: data.icms },
      { label: "ISS", value: data.iss },
      { label: "PIS", value: data.pis },
      { label: "COFINS", value: data.cofins },
      { label: "IPI destacado", value: data.ipi_separated },
      { label: "Impostos ROL", value: data.rol_taxes },
      { label: "ROL", value: data.rol },
      { label: "Títulos financeiros", value: data.financial_titles },
      { label: "Saldo financeiro", value: data.financial_balance },
    ];
  }, [data]);

  const columns = useMemo<DataTableColumn<RolRow>[]>(
    () => [
      {
        key: "label",
        header: "Componente",
        className: "ds-table__col--wide",
        render: (row) => row.label,
      },
      {
        key: "value",
        header: "Valor (R$)",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.value),
      },
    ],
    []
  );

  const isBusy = loading || refreshing;

  return (
    <div className="dashboard-financial dashboard-page">
      <FilterBar
        title="ROL"
        subtitle="Composição da receita operacional líquida"
        currentPath={pathname ?? FINANCIAL_ROUTES.rol}
        filterState={filterState}
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        onCompetenceChange={setCompetence}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
        onRefresh={reload}
        refreshing={refreshing}
      />
      <DataSourceBanner variant="totvs" />
      <FinancialStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={data !== null}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando ROL"
      />
      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="ROL"
          titleHint={FINANCIAL_HELP_TOOLTIPS.kpis.rol}
          value={formatCurrency(data?.rol)}
          subtitle={periodLabel}
          icon={<TrendingUp size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="ROL"
          titleHint={FINANCIAL_HELP_TOOLTIPS.kpis.rolWithIpiDetail}
          value={formatCurrency(data?.rol_with_ipi)}
          subtitle={formatBranchFilterLabel(branches)}
          icon={<TrendingUp size={22} />}
          loading={isBusy}
        />
      </section>
      <DataTableSection
        columnPreferencesKey="dashboard-financial:RolPage:detalhamento-da-rol:v1"
        title="Detalhamento da ROL"
        hint={periodLabel}
        columns={columns}
        rows={breakdownRows}
        rowKey={(row) => row.label}
        loading={loading && breakdownRows.length === 0}
        refreshing={refreshing}
        emptyMessage="Sem dados de ROL para o período."
        pageSize={10}
        hideSearch
      />
    </div>
  );
}