import { useMemo } from "react";
import { TrendingUp } from "lucide-react";

import { getRol } from "../api/financialApi";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { ChartCard } from "../components/ChartCard";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { FinancialStatusAlerts } from "../components/FinancialStatusAlerts";
import { FINANCIAL_ROUTES } from "../constants/routes";
import { useFinancialFilters } from "../hooks/useFinancialFilters";
import { useFinancialResource } from "../hooks/useFinancialResource";
import { formatPeriodLabel } from "../utils/dates";
import { formatCurrency } from "../utils/format";

type RolRow = { label: string; value: number };

type RolPageProps = { pathname?: string };

export function RolPage({ pathname }: RolPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    filterState,
  } = useFinancialFilters();

  const { data, loading, refreshing, error, reload } = useFinancialResource(
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
      { label: "ROL com IPI", value: data.rol_with_ipi },
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
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onRefresh={reload}
        refreshing={refreshing}
      />
      <DataSourceBanner />
      <FinancialStatusAlerts
        error={error}
        loading={loading}
        hasData={data !== null}
        onRetry={reload}
      />
      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="ROL"
          value={formatCurrency(data?.rol)}
          subtitle={periodLabel}
          icon={<TrendingUp size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="ROL com IPI"
          value={formatCurrency(data?.rol_with_ipi)}
          subtitle={branch ? `Filial ${branch}` : "Consolidado"}
          icon={<TrendingUp size={22} />}
          loading={isBusy && !data}
        />
      </section>
      <section className="ds-table-section">
        <ChartCard title="Detalhamento da ROL" hint={periodLabel}>
          <DataTable
            columns={columns}
            rows={breakdownRows}
            rowKey={(row) => row.label}
            loading={isBusy && !data}
            emptyMessage="Sem dados de ROL para o período."
          />
        </ChartCard>
      </section>
    </div>
  );
}
