import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { fetchInadimplenciaClientes } from "../../api/inadimplenciaApi";
import { ChartCard } from "../../components/ChartCard";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import type { InadimplenciaClienteItem } from "../../types/inadimplencia";
import {
  formatCurrencyBrl,
  formatInteger,
  formatMonthYearPtBr,
  formatPercent,
} from "../../utils/formatters";
import { getCurrentMonthRange } from "../../utils/period";
import { isExcludedCustomer } from "../../utils/customerScope";

type TopLateCustomersChartProps = {
  onOpenRanking?: () => void;
};

type ChartPoint = {
  label: string;
  titulos_atraso: number;
  valor_atraso: number;
  percentual_em_dia_qtd: number;
  cliente_codigo: string;
  loja: string;
  nome_reduzido: string;
};

const TOP_CHART_LIMIT = 8;

function buildChartPoint(item: InadimplenciaClienteItem): ChartPoint {
  const shortName = item.nome_reduzido?.trim() || item.nome_cliente?.trim() || "—";
  return {
    label: shortName.length > 18 ? `${shortName.slice(0, 16)}…` : shortName,
    titulos_atraso: item.titulos_atraso,
    valor_atraso: item.valor_atraso,
    percentual_em_dia_qtd: item.percentual_em_dia_qtd,
    cliente_codigo: item.cliente_codigo,
    loja: item.loja,
    nome_reduzido: shortName,
  };
}

function RankingTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload?: ChartPoint }>;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  if (!row) return null;

  return (
    <div className="fi-chart-tooltip">
      <strong>{row.nome_reduzido}</strong>
      <div>
        {row.cliente_codigo}/{row.loja}
      </div>
      <div>Títulos atrasados: {formatInteger(row.titulos_atraso)}</div>
      <div>Valor atrasado: {formatCurrencyBrl(row.valor_atraso)}</div>
      <div>Pontualidade (qtd): {formatPercent(row.percentual_em_dia_qtd)}</div>
    </div>
  );
}

export function TopLateCustomersChart({ onOpenRanking }: TopLateCustomersChartProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<ChartPoint[]>([]);
  const monthRange = getCurrentMonthRange();
  const monthLabel = formatMonthYearPtBr(monthRange.startDate);

  useEffect(() => {
    let cancelled = false;

    queueMicrotask(() => {
      void (async () => {
        setLoading(true);
        setError(null);
        try {
          const response = await fetchInadimplenciaClientes({
            startDate: monthRange.startDate,
            endDate: monthRange.endDate,
            page: 1,
            pageSize: 25,
            sortBy: "late_titles",
            sortDir: "desc",
            onlyWithDelays: true,
          });
          if (cancelled) return;
          setItems(
            response.items
              .filter((item) => !isExcludedCustomer(item.cliente_codigo))
              .slice(0, TOP_CHART_LIMIT)
              .map(buildChartPoint),
          );
        } catch (err) {
          if (cancelled) return;
          setItems([]);
          setError(err instanceof Error ? err.message : "Falha ao carregar ranking.");
        } finally {
          if (!cancelled) setLoading(false);
        }
      })();
    });

    return () => {
      cancelled = true;
    };
  }, [monthRange.startDate, monthRange.endDate]);

  return (
    <ChartCard
      title="Clientes inadimplentes"
      hint={`Top ${TOP_CHART_LIMIT} do mês atual (${monthLabel}) por títulos em atraso.`}
      headerActions={
        onOpenRanking ? (
          <button
            type="button"
            className="fi-btn fi-btn--secondary"
            onClick={onOpenRanking}
            disabled={loading}
          >
            Ver ranking
          </button>
        ) : undefined
      }
    >
      {loading ? <LoadingState message="Carregando ranking…" /> : null}
      {!loading && error ? <ErrorState message={error} /> : null}
      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title="Sem inadimplência no mês"
          message="Nenhum cliente com título atrasado no mês atual."
        />
      ) : null}
      {!loading && !error && items.length > 0 ? (
        <div className="fi-chart fi-chart--compact" aria-hidden="true">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              data={items}
              layout="vertical"
              margin={{ top: 4, right: 36, left: 4, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="var(--fi-chart-grid)" />
              <XAxis
                type="number"
                allowDecimals={false}
                tick={{ fontSize: 11, fill: "var(--fi-chart-axis)" }}
              />
              <YAxis
                type="category"
                dataKey="label"
                width={108}
                tick={{ fontSize: 11, fill: "var(--fi-chart-axis)" }}
              />
              <Tooltip content={<RankingTooltip />} />
              <Bar
                dataKey="titulos_atraso"
                name="Títulos atrasados"
                fill="var(--fi-danger, #b42318)"
                radius={[0, 4, 4, 0]}
              >
                <LabelList
                  dataKey="titulos_atraso"
                  position="right"
                  formatter={(value) => formatInteger(Number(value))}
                  style={{ fontSize: 11, fill: "var(--fi-title)" }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </ChartCard>
  );
}
