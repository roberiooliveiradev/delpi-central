import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Lightbulb } from "lucide-react";

import { getTransformaProcesses } from "../api/engineeringApi";
import { ChartCard } from "../components/ChartCard";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { EngineeringStatusAlerts } from "../components/EngineeringStatusAlerts";
import { CHART_COLORS } from "../constants/chartColors";
import { ENGINEERING_ROUTES } from "../constants/routes";
import { useEngineeringFilters } from "../hooks/useEngineeringFilters";
import { useEngineeringResource } from "../hooks/useEngineeringResource";
import type { TransformaProcess } from "../types/engineering";
import { formatPeriodLabel } from "../utils/dates";
import { formatCurrency, formatDecimal } from "../utils/format";

const CHART_HEIGHT = 320;

type ProcessesPageProps = { pathname?: string };

export function ProcessesPage({ pathname }: ProcessesPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    filterState,
  } = useEngineeringFilters();

  const [statusFilter, setStatusFilter] = useState("");

  const listParams = useMemo(
    () => ({
      ...apiParams,
      status: statusFilter || undefined,
    }),
    [apiParams, statusFilter]
  );

  const { data, loading, refreshing, error, reload } = useEngineeringResource(
    (signal) => getTransformaProcesses(listParams, signal),
    [
      listParams.branch,
      listParams.end_date,
      listParams.filial_id,
      listParams.start_date,
      listParams.status,
    ]
  );

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const items = data?.items ?? [];

  const topSavingsChart = useMemo(
    () =>
      [...items]
        .filter((item) => (item.daily_savings ?? 0) > 0)
        .sort((a, b) => (b.daily_savings ?? 0) - (a.daily_savings ?? 0))
        .slice(0, 10)
        .map((item) => ({
          name:
            item.name_process.length > 28
              ? `${item.name_process.slice(0, 28)}…`
              : item.name_process,
          value: item.daily_savings ?? 0,
        })),
    [items]
  );

  const columns = useMemo<DataTableColumn<TransformaProcess>[]>(
    () => [
      {
        key: "name",
        header: "Processo",
        className: "ds-table__col--wide",
        render: (row) => row.name_process || "—",
      },
      {
        key: "filial",
        header: "Filial",
        render: (row) => row.filial_id ?? "—",
      },
      {
        key: "sector",
        header: "Setor",
        render: (row) => row.sector_name ?? "—",
      },
      {
        key: "status",
        header: "Status",
        render: (row) => row.status ?? "—",
      },
      {
        key: "daily",
        header: "Economia/dia",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.daily_savings),
      },
      {
        key: "payback",
        header: "Payback (meses)",
        className: "ds-table__col--numeric",
        render: (row) => formatDecimal(row.payback_months, 1),
      },
      {
        key: "impl",
        header: "Implantação",
        render: (row) => row.implementetion_date ?? "—",
      },
    ],
    []
  );

  const isBusy = loading || refreshing;

  return (
    <div className="dashboard-engineering dashboard-page">
      <FilterBar
        title="Processos Transforma+"
        subtitle="Melhorias, automações e correções cadastradas na planilha"
        currentPath={pathname ?? ENGINEERING_ROUTES.processes}
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
      <EngineeringStatusAlerts
        error={error}
        loading={loading}
        hasData={data !== null}
        onRetry={reload}
      />

      <section className="ds-filters-row">
        <div className="ds-filter-box">
          <label htmlFor="de-status">Status do processo</label>
          <input
            id="de-status"
            type="text"
            value={statusFilter}
            placeholder="Todos"
            onChange={(e) => setStatusFilter(e.target.value)}
          />
        </div>
      </section>

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Processos no recorte"
          value={String(data?.total ?? items.length)}
          subtitle={periodLabel}
          icon={<Lightbulb size={22} />}
          loading={isBusy && !data}
        />
      </section>

      {topSavingsChart.length > 0 ? (
        <section className="ds-charts-grid ds-charts-grid--single">
          <ChartCard title="Top economia diária" hint="10 maiores no filtro atual">
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={topSavingsChart} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(v) => formatCurrency(Number(v))} />
                <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="value" radius={[0, 8, 8, 0]} maxBarSize={28}>
                  {topSavingsChart.map((_, index) => (
                    <Cell
                      key={index}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </section>
      ) : null}

      <section className="ds-table-section">
        <ChartCard title="Lista de processos" hint={periodLabel}>
          <DataTable
            columns={columns}
            rows={items}
            rowKey={(row) => row.id}
            loading={isBusy && !data}
            emptyMessage="Nenhum processo encontrado para os filtros."
          />
        </ChartCard>
      </section>
    </div>
  );
}
