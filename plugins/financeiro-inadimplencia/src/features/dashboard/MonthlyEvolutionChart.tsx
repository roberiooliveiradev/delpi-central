import { useEffect, useMemo, useState } from "react";
import {
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
  fetchInadimplenciaClientes,
  fetchInadimplenciaMensal,
} from "../../api/inadimplenciaApi";
import type {
  InadimplenciaClienteItem,
  InadimplenciaMensalData,
  PeriodFilter,
} from "../../types/inadimplencia";
import {
  formatCurrencyBrl,
  formatInteger,
  formatMonthYearPtBr,
  formatPercent,
} from "../../utils/formatters";
import { ChartCard } from "../../components/ChartCard";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";

type MonthlyEvolutionChartProps = {
  period: PeriodFilter;
  mensal: InadimplenciaMensalData | null;
  loading?: boolean;
};

type CustomerOption = {
  key: string;
  cliente_codigo: string;
  loja: string;
  label: string;
};

type ChartPoint = {
  mesLabel: string;
  total_titulos: number;
  titulos_em_dia: number;
  titulos_atraso: number;
  percentual_em_dia_qtd: number;
  percentual_em_dia_valor: number;
  valor_total: number;
  valor_atraso: number;
  percentLabel: string;
};

type TooltipPayloadItem = {
  payload?: ChartPoint;
};

function encodeCustomerKey(codigo: string, loja: string): string {
  return `${codigo}::${loja}`;
}

function parseCustomerKey(key: string): { customerCode: string; storeCode: string } | null {
  if (!key) return null;
  const [customerCode, storeCode] = key.split("::");
  if (!customerCode || storeCode == null || storeCode === "") return null;
  return { customerCode, storeCode };
}

function toCustomerOption(item: InadimplenciaClienteItem): CustomerOption {
  const shortName = item.nome_reduzido?.trim() || item.nome_cliente?.trim() || "—";
  return {
    key: encodeCustomerKey(item.cliente_codigo, item.loja),
    cliente_codigo: item.cliente_codigo,
    loja: item.loja,
    label: `${shortName} (${item.cliente_codigo}/${item.loja})`,
  };
}

function MonthlyTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayloadItem[] }) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  if (!row) return null;

  return (
    <div className="fi-chart-tooltip">
      <strong>{row.mesLabel}</strong>
      <div>Total de títulos: {formatInteger(row.total_titulos)}</div>
      <div>Em dia: {formatInteger(row.titulos_em_dia)}</div>
      <div>Atrasados: {formatInteger(row.titulos_atraso)}</div>
      <div>Pontualidade (qtd): {formatPercent(row.percentual_em_dia_qtd)}</div>
      <div>Pontualidade (valor): {formatPercent(row.percentual_em_dia_valor)}</div>
      <div>Valor total: {formatCurrencyBrl(row.valor_total)}</div>
      <div>Valor atrasado: {formatCurrencyBrl(row.valor_atraso)}</div>
    </div>
  );
}

type MonthAxisTickProps = {
  x?: number;
  y?: number;
  payload?: { value?: string };
  chartData: ChartPoint[];
};

function MonthAxisTick({ x = 0, y = 0, payload, chartData }: MonthAxisTickProps) {
  const monthLabel = payload?.value ?? "";
  const point = chartData.find((item) => item.mesLabel === monthLabel);
  const percent = point ? point.percentLabel : "";

  return (
    <g transform={`translate(${x},${y})`}>
      <text dy={14} textAnchor="middle" fill="var(--fi-chart-axis)" fontSize={11}>
        {monthLabel}
      </text>
      <text dy={30} textAnchor="middle" fill="var(--fi-title)" fontSize={11} fontWeight={600}>
        {percent}
      </text>
    </g>
  );
}

export function MonthlyEvolutionChart({
  period,
  mensal,
  loading = false,
}: MonthlyEvolutionChartProps) {
  const periodStart = period.startDate ?? "";
  const periodEnd = period.endDate ?? "";

  const [customerKey, setCustomerKey] = useState("");
  const [optionsPeriodKey, setOptionsPeriodKey] = useState(`${periodStart}|${periodEnd}`);
  const [customerOptions, setCustomerOptions] = useState<CustomerOption[]>([]);
  const [optionsLoading, setOptionsLoading] = useState(false);
  const [filteredMensal, setFilteredMensal] = useState<InadimplenciaMensalData | null>(null);
  const [filteredLoading, setFilteredLoading] = useState(false);
  const [filteredError, setFilteredError] = useState<string | null>(null);

  const periodKey = `${periodStart}|${periodEnd}`;
  if (periodKey !== optionsPeriodKey) {
    setOptionsPeriodKey(periodKey);
    setCustomerKey("");
    setFilteredMensal(null);
    setFilteredError(null);
  }

  const selectedCustomer = useMemo(() => parseCustomerKey(customerKey), [customerKey]);

  useEffect(() => {
    let cancelled = false;

    queueMicrotask(() => {
      void (async () => {
        setOptionsLoading(true);
        try {
          const response = await fetchInadimplenciaClientes({
            startDate: periodStart || undefined,
            endDate: periodEnd || undefined,
            page: 1,
            pageSize: 100,
            sortBy: "customer_name",
            sortDir: "asc",
            onlyWithDelays: false,
          });
          if (cancelled) return;
          setCustomerOptions(response.items.map(toCustomerOption));
        } catch {
          if (cancelled) return;
          setCustomerOptions([]);
        } finally {
          if (!cancelled) setOptionsLoading(false);
        }
      })();
    });

    return () => {
      cancelled = true;
    };
  }, [periodStart, periodEnd]);

  useEffect(() => {
    if (!selectedCustomer) {
      return;
    }

    let cancelled = false;
    queueMicrotask(() => {
      void (async () => {
        setFilteredLoading(true);
        setFilteredError(null);
        try {
          const response = await fetchInadimplenciaMensal({
            startDate: periodStart || undefined,
            endDate: periodEnd || undefined,
            customerCode: selectedCustomer.customerCode,
            storeCode: selectedCustomer.storeCode,
          });
          if (cancelled) return;
          setFilteredMensal(response);
        } catch (err) {
          if (cancelled) return;
          setFilteredMensal(null);
          setFilteredError(
            err instanceof Error ? err.message : "Falha ao carregar série do cliente.",
          );
        } finally {
          if (!cancelled) setFilteredLoading(false);
        }
      })();
    });

    return () => {
      cancelled = true;
    };
  }, [selectedCustomer, periodStart, periodEnd]);

  const activeMensal = selectedCustomer ? filteredMensal : mensal;
  const isLoading = selectedCustomer ? filteredLoading : loading;
  const items = activeMensal?.items ?? [];
  const chartData: ChartPoint[] = items.map((item) => ({
    ...item,
    mesLabel: formatMonthYearPtBr(item.ano_mes || item.mes),
    percentLabel: formatPercent(item.percentual_em_dia_qtd),
  }));

  const selectedOption = customerOptions.find((option) => option.key === customerKey);
  const hint = selectedOption
    ? `Pontualidade por quantidade de ${selectedOption.label}.`
    : "Pontualidade por quantidade (todos os clientes). Passe o ponteiro sobre o mês para ver o detalhamento.";

  return (
    <ChartCard
      title="Evolução mensal"
      hint={hint}
      headerActions={
        <label className="fi-field fi-field--chart-filter">
          <span>Cliente</span>
          <select
            value={customerKey}
            disabled={optionsLoading || loading}
            onChange={(event) => {
              const nextKey = event.target.value;
              setCustomerKey(nextKey);
              if (!nextKey) {
                setFilteredMensal(null);
                setFilteredError(null);
                setFilteredLoading(false);
              }
            }}
            aria-label="Filtrar evolução mensal por cliente"
          >
            <option value="">Todos os clientes</option>
            {customerOptions.map((option) => (
              <option key={option.key} value={option.key}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      }
    >
      {isLoading ? <LoadingState message="Carregando série mensal…" /> : null}

      {!isLoading && filteredError ? (
        <EmptyState title="Não foi possível filtrar" message={filteredError} />
      ) : null}

      {!isLoading && !filteredError && items.length === 0 ? (
        <EmptyState
          title="Sem evolução no período"
          message={
            selectedCustomer
              ? "Nenhum título encontrado para este cliente no período selecionado."
              : "Nenhum título encontrado para o período selecionado."
          }
        />
      ) : null}

      {!isLoading && !filteredError && items.length > 0 ? (
        <>
          <div className="fi-chart" aria-hidden="true">
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData} margin={{ top: 28, right: 16, left: 4, bottom: 28 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--fi-chart-grid)" />
                <XAxis
                  dataKey="mesLabel"
                  height={48}
                  interval={0}
                  tick={<MonthAxisTick chartData={chartData} />}
                />
                <YAxis
                  domain={[0, 100]}
                  tickFormatter={(value) => `${value}%`}
                  tick={{ fontSize: 11, fill: "var(--fi-chart-axis)" }}
                />
                <Tooltip content={<MonthlyTooltip />} />
                <Line
                  type="monotone"
                  dataKey="percentual_em_dia_qtd"
                  name="Pontualidade (qtd)"
                  stroke="var(--fi-accent)"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: "var(--fi-accent)" }}
                  activeDot={{ r: 5 }}
                >
                  <LabelList
                    dataKey="percentLabel"
                    position="top"
                    offset={10}
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      fill: "var(--fi-title)",
                    }}
                  />
                </Line>
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="fi-chart-summary">
            {items.length} mês(es) com{" "}
            {formatInteger(items.reduce((acc, item) => acc + item.total_titulos, 0))} títulos
            liquidados
            {selectedOption ? ` · ${selectedOption.label}` : ""}.
          </p>
        </>
      ) : null}
    </ChartCard>
  );
}
