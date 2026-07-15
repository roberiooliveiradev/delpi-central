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
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { FiModal } from "../../components/FiModal";
import { LoadingState } from "../../components/LoadingState";
import type { InadimplenciaClienteItem } from "../../types/inadimplencia";
import {
  formatCurrencyBrl,
  formatInteger,
  formatMonthYearPtBr,
  formatPercent,
} from "../../utils/formatters";
import { getCurrentMonthRange } from "../../utils/period";

type TopLateCustomersModalProps = {
  open: boolean;
  onClose: () => void;
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

function buildChartPoint(item: InadimplenciaClienteItem): ChartPoint {
  const shortName = item.nome_reduzido?.trim() || item.nome_cliente?.trim() || "—";
  return {
    label: shortName,
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

export function TopLateCustomersModal({ open, onClose }: TopLateCustomersModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<ChartPoint[]>([]);
  const monthRange = getCurrentMonthRange();
  const monthLabel = formatMonthYearPtBr(monthRange.startDate);

  useEffect(() => {
    if (!open) return;

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
          setItems(response.items.map(buildChartPoint));
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
  }, [open, monthRange.startDate, monthRange.endDate]);

  const chartHeight = Math.max(320, items.length * 36);

  return (
    <FiModal
      open={open}
      title="Clientes inadimplentes do mês"
      subtitle={`${monthLabel} · ordenado pela quantidade de títulos em atraso (maior → menor)`}
      onClose={onClose}
    >
      {loading ? <LoadingState message="Carregando ranking do mês…" /> : null}

      {error ? <ErrorState message={error} /> : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title="Sem inadimplência no mês"
          message="Nenhum cliente com título atrasado no mês atual."
        />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <div className="fi-chart fi-chart--ranking" aria-hidden="true">
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart
              data={items}
              layout="vertical"
              margin={{ top: 8, right: 48, left: 8, bottom: 8 }}
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
                width={140}
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
    </FiModal>
  );
}
