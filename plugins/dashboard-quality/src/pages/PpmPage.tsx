import { useEffect, useMemo, useState } from "react";
import { Download, Factory, Truck } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "../components/ChartCard";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { KpiCard } from "../components/KpiCard";
import { Pagination } from "../components/Pagination";
import { PpmTypeToggle } from "../components/PpmTypeToggle";
import { QualityFilters } from "../components/QualityFilters";
import { QualityPageHeader } from "../components/QualityPageHeader";
import { QUALITY_ROUTES } from "../constants/routes";
import { CHART_COLORS } from "../constants/chartColors";
import { usePpmPage } from "../hooks/usePpmPage";
import { useQualityFilters } from "../hooks/useQualityFilters";
import type { PpmItem, PpmType } from "../types/ppm";
import { downloadCsv } from "../utils/csv";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import { formatDecimal, formatPpm } from "../utils/format";

const CHART_HEIGHT = 320;

type PpmPageProps = {
  pathname?: string;
};

export function PpmPage({ pathname }: PpmPageProps) {
  const [ppmType, setPpmType] = useState<PpmType>("internal");
  const [page, setPage] = useState(1);

  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
  } = useQualityFilters();

  const { summary, page: tablePage, chartData, loading, refreshing, error, reload } =
    usePpmPage({
      type: ppmType,
      filters: apiParams,
      page,
    });

  useEffect(() => {
    setPage(1);
  }, [ppmType, apiParams.branch, apiParams.date_start, apiParams.date_end]);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const columns = useMemo<DataTableColumn<PpmItem>[]>(
    () => [
      {
        key: "registered_date",
        header: "Data",
        render: (row) => formatDisplayDate(row.registered_date),
      },
      {
        key: "branch",
        header: "Filial",
        render: (row) => row.branch,
      },
      {
        key: "code",
        header: "Código",
        render: (row) => row.code,
      },
      {
        key: "item_code",
        header: "Item",
        render: (row) => row.item_code ?? "—",
      },
      {
        key: "description",
        header: "Descrição",
        className: "dq-table__col--wide",
        render: (row) => row.description ?? "—",
      },
      {
        key: "returned_quantity_un",
        header: "Qtd. devolvida (un)",
        className: "dq-table__col--numeric",
        render: (row) => formatDecimal(row.returned_quantity_un),
      },
    ],
    []
  );

  const handleExportCsv = () => {
    const items = tablePage?.items ?? [];
    if (items.length === 0) return;

    downloadCsv(
      `ppm-${ppmType}-pagina-${page}.csv`,
      [
        "Data",
        "Filial",
        "Código",
        "Revisão",
        "Item",
        "Descrição",
        "Qtd devolvida (un)",
      ],
      items.map((row) => [
        formatDisplayDate(row.registered_date),
        row.branch,
        row.code,
        row.revision,
        row.item_code ?? "",
        row.description ?? "",
        String(row.returned_quantity_un ?? ""),
      ])
    );
  };

  const isBusy = loading || refreshing;
  const typeLabel = ppmType === "internal" ? "interno" : "externo";

  return (
    <div className="dashboard-quality dashboard-page">
      <QualityPageHeader
        title="PPM"
        subtitle={`Detalhamento ${typeLabel} — listagem e evolução mensal`}
        currentPath={pathname ?? QUALITY_ROUTES.ppm}
        onRefresh={reload}
        refreshing={refreshing}
        actions={
          <button
            type="button"
            className="dq-ghost-btn"
            onClick={handleExportCsv}
            disabled={!tablePage?.items.length}
          >
            <Download size={16} />
            Exportar CSV
          </button>
        }
      />

      <QualityFilters
        idPrefix="ppm"
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
      />

      <div className="dq-ppm-toolbar">
        <PpmTypeToggle value={ppmType} onChange={setPpmType} />
      </div>

      {error ? (
        <div className="dq-state dq-state--error" role="alert">
          <p>{error}</p>
          <button className="dq-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      <section className="dq-kpi-grid dq-kpi-grid--single-row" aria-busy={isBusy}>
        <KpiCard
          title={`PPM ${typeLabel}`}
          value={formatPpm(summary?.ppm)}
          subtitle={`Produzido: ${formatDecimal(summary?.total_produzido_un)} un · ${periodLabel}`}
          icon={
            ppmType === "internal" ? (
              <Factory size={22} />
            ) : (
              <Truck size={22} />
            )
          }
          loading={isBusy && !summary}
        />
        <KpiCard
          title="Total devolvido"
          value={formatDecimal(summary?.total_devolvido_un)}
          subtitle={`Milheiro produzido: ${formatDecimal(summary?.total_produzido_milheiro)}`}
          icon={ppmType === "internal" ? <Factory size={22} /> : <Truck size={22} />}
          loading={isBusy && !summary}
        />
      </section>

      <section className="dq-chart-section" aria-busy={isBusy}>
        <ChartCard
          title="Devoluções por mês"
          hint="Agregado dos registros carregados para o gráfico (amostra do período)."
        >
          {chartData.length === 0 && !loading ? (
            <div className="dq-state-box">Sem dados para o gráfico no período.</div>
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="periodo" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value) => [
                    formatDecimal(Number(value)),
                    "Qtd. devolvida (un)",
                  ]}
                />
                <Bar
                  dataKey="devolvido"
                  fill={CHART_COLORS[0]}
                  radius={[6, 6, 0, 0]}
                  name="Devolvido (un)"
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </section>

      <section className="dq-table-section dq-card" aria-busy={isBusy}>
        <div className="dq-table-section__header">
          <h2 className="dq-section-title">Registros de PPM</h2>
        </div>

        <DataTable
          columns={columns}
          rows={tablePage?.items ?? []}
          rowKey={(row) => `${row.code}-${row.revision}-${row.registered_date}`}
          loading={loading && !tablePage}
        />

        {tablePage ? (
          <Pagination
            page={tablePage.page}
            pageSize={tablePage.page_size}
            total={tablePage.total}
            onPageChange={setPage}
          />
        ) : null}
      </section>
    </div>
  );
}
