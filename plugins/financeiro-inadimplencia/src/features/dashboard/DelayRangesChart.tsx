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

import type { InadimplenciaFaixasData } from "../../types/inadimplencia";
import {
  formatCurrencyBrl,
  formatInteger,
  formatPercent,
} from "../../utils/formatters";
import { ChartCard } from "../../components/ChartCard";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";

type DelayRangesChartProps = {
  faixas: InadimplenciaFaixasData | null;
  loading?: boolean;
};

export function DelayRangesChart({ faixas, loading = false }: DelayRangesChartProps) {
  const items = [...(faixas?.items ?? [])].sort((a, b) => a.ordem - b.ordem);
  const chartData = items.map((item) => ({
    ...item,
    fill:
      item.codigo === "ATRASO_ACIMA_30_DIAS"
        ? "var(--fi-danger, #b42318)"
        : item.codigo === "EM_DIA"
          ? "var(--fi-accent)"
          : "var(--fi-alert, #b45309)",
  }));

  return (
    <ChartCard
      title="Distribuição por faixa"
      hint="Quantidade e valor por faixa de atraso (ordem oficial)."
    >
      {loading ? <LoadingState message="Carregando faixas…" /> : null}
      {!loading && items.length === 0 ? (
        <EmptyState
          title="Sem distribuição"
          message="Nenhum título encontrado para o período selecionado."
        />
      ) : null}
      {!loading && items.length > 0 ? (
        <>
          <div className="fi-chart fi-chart--compact" aria-hidden="true">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 4, right: 16, left: 4, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--fi-chart-grid)" />
                <XAxis type="number" tick={{ fontSize: 11, fill: "var(--fi-chart-axis)" }} />
                <YAxis
                  type="category"
                  dataKey="rotulo"
                  width={110}
                  tick={{ fontSize: 11, fill: "var(--fi-chart-axis)" }}
                />
                <Tooltip
                  formatter={(value, _name, item) => {
                    const row = item?.payload as (typeof chartData)[number] | undefined;
                    if (!row) return formatInteger(Number(value));
                    return [
                      `${formatInteger(row.quantidade)} (${formatPercent(row.percentual_quantidade)}) · ${formatCurrencyBrl(row.valor)} (${formatPercent(row.percentual_valor)})`,
                      row.rotulo,
                    ];
                  }}
                />
                <Bar dataKey="quantidade" name="Quantidade" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry) => (
                    <Cell key={entry.codigo} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ul className="fi-faixas-list fi-faixas-list--compact">
            {items.map((item) => (
              <li key={item.codigo} className={item.codigo === "ATRASO_ACIMA_30_DIAS" ? "fi-faixas-list__item--danger" : undefined}>
                <strong>{item.rotulo}</strong>
                <span>
                  {formatInteger(item.quantidade)} ({formatPercent(item.percentual_quantidade)})
                </span>
                <span>
                  {formatCurrencyBrl(item.valor)} ({formatPercent(item.percentual_valor)})
                </span>
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </ChartCard>
  );
}
