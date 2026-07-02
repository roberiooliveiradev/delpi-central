import { useCallback, useState } from "react";
import { Maximize2 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  fetchDespesasRankingCentros,
  fetchDespesasRankingFornecedores,
} from "../api/despesasCentroCustoApi";
import type {
  DespesasQueryFilters,
  DespesasRankingCentroItem,
  DespesasRankingCentrosData,
  DespesasRankingFornecedorItem,
  DespesasRankingFornecedoresData,
  DespesasSerieData,
} from "../types/despesasCentroCusto";
import {
  formatCostCenterLabel,
  formatCurrencyBrl,
  formatInteger,
  formatMonthYearPtBr,
  formatPercent,
} from "../utils/formatters";
import { ChartCard } from "./ChartCard";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { FccModal } from "./FccModal";
import { LoadingState } from "./LoadingState";

const EXPANDED_RANKING_LIMIT = 50;
const PREVIEW_CHART_HEIGHT = 280;

type BarChartDatum = {
  name: string;
  total: number;
};

type HorizontalBarChartProps = {
  data: BarChartDatum[];
  height: number;
  barColor: string;
  yAxisWidth?: number;
};

function HorizontalBarChart({
  data,
  height,
  barColor,
  yAxisWidth = 120,
}: HorizontalBarChartProps) {
  return (
    <div className="fcc-chart fcc-chart--bar">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border, #e2e8f0)" />
          <XAxis
            type="number"
            tickFormatter={(value) => formatCurrencyBrl(Number(value))}
            tick={{ fontSize: 11 }}
          />
          <YAxis type="category" dataKey="name" width={yAxisWidth} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(value) => formatCurrencyBrl(Number(value))} />
          <Bar dataKey="total" fill={barColor} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function rankingChartHeight(itemCount: number): number {
  return Math.min(720, Math.max(PREVIEW_CHART_HEIGHT, itemCount * 34 + 48));
}

type ChartExpandButtonProps = {
  label: string;
  onClick: () => void;
  disabled?: boolean;
};

function ChartExpandButton({ label, onClick, disabled = false }: ChartExpandButtonProps) {
  return (
    <button
      type="button"
      className="fcc-btn fcc-btn--secondary fcc-chart-expand-btn"
      aria-label={label}
      title={label}
      onClick={onClick}
      disabled={disabled}
    >
      <Maximize2 size={15} aria-hidden="true" />
      <span>Expandir</span>
    </button>
  );
}

type MonthlyEvolutionChartProps = {
  serie: DespesasSerieData | null;
  loading?: boolean;
};

export function MonthlyEvolutionChart({ serie, loading = false }: MonthlyEvolutionChartProps) {
  const chartData = (serie?.serie ?? []).map((item) => ({
    mes: item.ano_mes,
    label: formatMonthYearPtBr(item.ano_mes),
    total: item.valor_total,
  }));

  return (
    <ChartCard title="Evolução mensal de despesas" className="fcc-chart-card--wide">
      {loading ? (
        <div className="fcc-chart-placeholder">Carregando gráfico…</div>
      ) : chartData.length === 0 ? (
        <EmptyState message="Não há despesas no período selecionado." />
      ) : (
        <div className="fcc-chart fcc-chart--line">
          <ResponsiveContainer width="100%" height={PREVIEW_CHART_HEIGHT}>
            <LineChart data={chartData} margin={{ top: 28, right: 16, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border, #e2e8f0)" />
              <XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis
                tickFormatter={(value) => formatCurrencyBrl(Number(value))}
                width={96}
                tick={{ fontSize: 11 }}
              />
              <Tooltip
                formatter={(value) => formatCurrencyBrl(Number(value))}
                labelFormatter={(label) => String(label)}
              />
              <Line
                type="monotone"
                dataKey="total"
                stroke="var(--primary, #2563eb)"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              >
                <LabelList
                  dataKey="total"
                  position="top"
                  offset={8}
                  formatter={(value) => formatCurrencyBrl(Number(value))}
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    fill: "var(--foreground, #0f172a)",
                  }}
                />
              </Line>
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </ChartCard>
  );
}

function RankingCentrosDetailTable({ items }: { items: DespesasRankingCentroItem[] }) {
  return (
    <div className="fcc-ranking-detail">
      <h3 className="fcc-ranking-detail__title">Detalhamento</h3>
      <div className="fcc-table-wrap">
        <table className="fcc-table fcc-ranking-detail__table">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Centro de custo</th>
              <th scope="col">Código</th>
              <th scope="col" className="fcc-table__numeric">
                Valor total
              </th>
              <th scope="col" className="fcc-table__numeric">
                Lançamentos
              </th>
              <th scope="col" className="fcc-table__numeric">
                % do período
              </th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={`${item.centro_custo_codigo}-${index}`}>
                <td>{index + 1}</td>
                <td>{item.centro_custo_descricao || "—"}</td>
                <td>{item.centro_custo_codigo || "—"}</td>
                <td className="fcc-table__numeric">{formatCurrencyBrl(item.valor_total)}</td>
                <td className="fcc-table__numeric">{formatInteger(item.quantidade_lancamentos)}</td>
                <td className="fcc-table__numeric">{formatPercent(item.percentual)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RankingFornecedoresDetailTable({ items }: { items: DespesasRankingFornecedorItem[] }) {
  return (
    <div className="fcc-ranking-detail">
      <h3 className="fcc-ranking-detail__title">Detalhamento</h3>
      <div className="fcc-table-wrap">
        <table className="fcc-table fcc-ranking-detail__table">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Fornecedor</th>
              <th scope="col">Código / loja</th>
              <th scope="col" className="fcc-table__numeric">
                Valor total
              </th>
              <th scope="col" className="fcc-table__numeric">
                Lançamentos
              </th>
              <th scope="col" className="fcc-table__numeric">
                % do período
              </th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={`${item.fornecedor_cliente_codigo}-${item.loja}-${index}`}>
                <td>{index + 1}</td>
                <td>{item.razao_social || "—"}</td>
                <td>
                  {item.fornecedor_cliente_codigo}
                  {item.loja ? ` / ${item.loja}` : ""}
                </td>
                <td className="fcc-table__numeric">{formatCurrencyBrl(item.valor_total)}</td>
                <td className="fcc-table__numeric">{formatInteger(item.quantidade_lancamentos)}</td>
                <td className="fcc-table__numeric">{formatPercent(item.percentual)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

type RankingCentrosChartProps = {
  ranking: DespesasRankingCentrosData | null;
  filters: DespesasQueryFilters;
  loading?: boolean;
};

export function RankingCentrosChart({
  ranking,
  filters,
  loading = false,
}: RankingCentrosChartProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [expandedRanking, setExpandedRanking] = useState<DespesasRankingCentrosData | null>(null);
  const [expandedLoading, setExpandedLoading] = useState(false);
  const [expandedError, setExpandedError] = useState<string | null>(null);

  const previewItems = ranking?.ranking ?? [];
  const previewChartData: BarChartDatum[] = previewItems.map((item) => ({
    name: formatCostCenterLabel(item.centro_custo_codigo, item.centro_custo_descricao),
    total: item.valor_total,
  }));

  const expandedItems = expandedRanking?.ranking ?? [];
  const expandedChartData: BarChartDatum[] = expandedItems.map((item) => ({
    name: formatCostCenterLabel(item.centro_custo_codigo, item.centro_custo_descricao),
    total: item.valor_total,
  }));

  const handleExpand = useCallback(async () => {
    setModalOpen(true);
    setExpandedLoading(true);
    setExpandedError(null);

    try {
      const data = await fetchDespesasRankingCentros(filters, EXPANDED_RANKING_LIMIT);
      setExpandedRanking(data);
    } catch (error) {
      setExpandedRanking(null);
      setExpandedError(error instanceof Error ? error.message : "Falha ao carregar ranking expandido.");
    } finally {
      setExpandedLoading(false);
    }
  }, [filters]);

  const handleCloseModal = useCallback(() => {
    setModalOpen(false);
  }, []);

  const canExpand = !loading && previewChartData.length > 0;

  return (
    <>
      <ChartCard
        title="Ranking de centros de custo"
        hint="Top 10 no período"
        headerActions={
          canExpand ? (
            <ChartExpandButton
              label="Expandir ranking de centros de custo"
              onClick={() => void handleExpand()}
            />
          ) : null
        }
      >
        {loading ? (
          <div className="fcc-chart-placeholder">Carregando gráfico…</div>
        ) : previewChartData.length === 0 ? (
          <EmptyState message="Nenhum centro de custo no período." />
        ) : (
          <HorizontalBarChart
            data={previewChartData}
            height={PREVIEW_CHART_HEIGHT}
            barColor="var(--primary, #2563eb)"
          />
        )}
      </ChartCard>

      <FccModal
        open={modalOpen}
        title="Ranking de centros de custo"
        subtitle={`Top ${EXPANDED_RANKING_LIMIT} centros de custo no período filtrado`}
        onClose={handleCloseModal}
      >
        {expandedLoading ? (
          <LoadingState message="Carregando detalhes…" />
        ) : expandedError ? (
          <ErrorState message={expandedError} onRetry={() => void handleExpand()} />
        ) : expandedChartData.length === 0 ? (
          <EmptyState message="Nenhum centro de custo no período." />
        ) : (
          <div className="fcc-ranking-modal">
            <HorizontalBarChart
              data={expandedChartData}
              height={rankingChartHeight(expandedChartData.length)}
              barColor="var(--primary, #2563eb)"
              yAxisWidth={200}
            />
            <RankingCentrosDetailTable items={expandedItems} />
          </div>
        )}
      </FccModal>
    </>
  );
}

type RankingFornecedoresChartProps = {
  ranking: DespesasRankingFornecedoresData | null;
  filters: DespesasQueryFilters;
  loading?: boolean;
};

export function RankingFornecedoresChart({
  ranking,
  filters,
  loading = false,
}: RankingFornecedoresChartProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [expandedRanking, setExpandedRanking] = useState<DespesasRankingFornecedoresData | null>(null);
  const [expandedLoading, setExpandedLoading] = useState(false);
  const [expandedError, setExpandedError] = useState<string | null>(null);

  const previewItems = ranking?.ranking ?? [];
  const previewChartData: BarChartDatum[] = previewItems.map((item) => ({
    name: item.razao_social || `${item.fornecedor_cliente_codigo}/${item.loja}`,
    total: item.valor_total,
  }));

  const expandedItems = expandedRanking?.ranking ?? [];
  const expandedChartData: BarChartDatum[] = expandedItems.map((item) => ({
    name: item.razao_social || `${item.fornecedor_cliente_codigo}/${item.loja}`,
    total: item.valor_total,
  }));

  const handleExpand = useCallback(async () => {
    setModalOpen(true);
    setExpandedLoading(true);
    setExpandedError(null);

    try {
      const data = await fetchDespesasRankingFornecedores(filters, EXPANDED_RANKING_LIMIT);
      setExpandedRanking(data);
    } catch (error) {
      setExpandedRanking(null);
      setExpandedError(error instanceof Error ? error.message : "Falha ao carregar ranking expandido.");
    } finally {
      setExpandedLoading(false);
    }
  }, [filters]);

  const handleCloseModal = useCallback(() => {
    setModalOpen(false);
  }, []);

  const canExpand = !loading && previewChartData.length > 0;

  return (
    <>
      <ChartCard
        title="Ranking de fornecedores"
        hint="Top 10 no período"
        headerActions={
          canExpand ? (
            <ChartExpandButton
              label="Expandir ranking de fornecedores"
              onClick={() => void handleExpand()}
            />
          ) : null
        }
      >
        {loading ? (
          <div className="fcc-chart-placeholder">Carregando gráfico…</div>
        ) : previewChartData.length === 0 ? (
          <EmptyState message="Nenhum fornecedor no período." />
        ) : (
          <HorizontalBarChart
            data={previewChartData}
            height={PREVIEW_CHART_HEIGHT}
            barColor="var(--accent, #0d9488)"
          />
        )}
      </ChartCard>

      <FccModal
        open={modalOpen}
        title="Ranking de fornecedores"
        subtitle={`Top ${EXPANDED_RANKING_LIMIT} fornecedores no período filtrado`}
        onClose={handleCloseModal}
      >
        {expandedLoading ? (
          <LoadingState message="Carregando detalhes…" />
        ) : expandedError ? (
          <ErrorState message={expandedError} onRetry={() => void handleExpand()} />
        ) : expandedChartData.length === 0 ? (
          <EmptyState message="Nenhum fornecedor no período." />
        ) : (
          <div className="fcc-ranking-modal">
            <HorizontalBarChart
              data={expandedChartData}
              height={rankingChartHeight(expandedChartData.length)}
              barColor="var(--accent, #0d9488)"
              yAxisWidth={220}
            />
            <RankingFornecedoresDetailTable items={expandedItems} />
          </div>
        )}
      </FccModal>
    </>
  );
}
