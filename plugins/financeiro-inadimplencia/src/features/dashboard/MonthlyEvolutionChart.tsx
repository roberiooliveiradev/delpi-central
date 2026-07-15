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
import {
  isExcludedCustomer,
  isNovosNegociosCustomer,
} from "../../utils/customerScope";
import { ChartCard } from "../../components/ChartCard";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { MultiSelectField } from "../../components/MultiSelectField";

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

function customerParamFromKey(key: string): string | null {
  const [customerCode, storeCode] = key.split("::");
  if (!customerCode || storeCode == null || storeCode === "") return null;
  return `${customerCode}/${storeCode}`;
}

function toCustomerOption(item: InadimplenciaClienteItem): CustomerOption | null {
  if (isExcludedCustomer(item.cliente_codigo)) return null;
  const shortName = item.nome_reduzido?.trim() || item.nome_cliente?.trim() || "—";
  return {
    key: encodeCustomerKey(item.cliente_codigo, item.loja),
    cliente_codigo: item.cliente_codigo,
    loja: item.loja,
    label: `${shortName} (${item.cliente_codigo}/${item.loja})`,
  };
}

async function fetchAllCustomerOptions(
  periodStart: string,
  periodEnd: string,
): Promise<CustomerOption[]> {
  const pageSize = 100;
  let page = 1;
  const items: CustomerOption[] = [];

  while (true) {
    const response = await fetchInadimplenciaClientes({
      startDate: periodStart || undefined,
      endDate: periodEnd || undefined,
      page,
      pageSize,
      sortBy: "customer_name",
      sortDir: "asc",
      onlyWithDelays: false,
    });
    for (const item of response.items) {
      const option = toCustomerOption(item);
      if (option) items.push(option);
    }
    if (items.length >= response.total_items || response.items.length < pageSize) {
      break;
    }
    page += 1;
  }

  return items;
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

  const [novosNegocios, setNovosNegocios] = useState(false);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [selectionSyncedFor, setSelectionSyncedFor] = useState("");
  const [optionsPeriodKey, setOptionsPeriodKey] = useState(`${periodStart}|${periodEnd}`);
  const [customerOptions, setCustomerOptions] = useState<CustomerOption[]>([]);
  const [optionsLoading, setOptionsLoading] = useState(false);
  const [filteredMensal, setFilteredMensal] = useState<InadimplenciaMensalData | null>(null);
  const [filteredLoading, setFilteredLoading] = useState(false);
  const [filteredError, setFilteredError] = useState<string | null>(null);

  const periodKey = `${periodStart}|${periodEnd}`;
  if (periodKey !== optionsPeriodKey) {
    setOptionsPeriodKey(periodKey);
    setSelectedKeys([]);
    setSelectionSyncedFor("");
    setNovosNegocios(false);
    setFilteredMensal(null);
    setFilteredError(null);
  }

  useEffect(() => {
    let cancelled = false;

    queueMicrotask(() => {
      void (async () => {
        setOptionsLoading(true);
        try {
          const options = await fetchAllCustomerOptions(periodStart, periodEnd);
          if (cancelled) return;
          setCustomerOptions(options);
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

  const visibleOptions = useMemo(
    () =>
      novosNegocios
        ? customerOptions.filter((option) => isNovosNegociosCustomer(option.cliente_codigo))
        : customerOptions,
    [customerOptions, novosNegocios],
  );

  const visibleKeys = useMemo(
    () => visibleOptions.map((option) => option.key),
    [visibleOptions],
  );

  useEffect(() => {
    if (!customerOptions.length) return;
    if (selectionSyncedFor === periodKey) return;
    setSelectedKeys(customerOptions.map((option) => option.key));
    setSelectionSyncedFor(periodKey);
  }, [customerOptions, periodKey, selectionSyncedFor]);

  const allSelected =
    visibleKeys.length > 0 &&
    selectedKeys.length === visibleKeys.length &&
    visibleKeys.every((key) => selectedKeys.includes(key));
  const noneSelected = selectedKeys.length === 0;
  const isPartialSelection = !allSelected && !noneSelected;
  const needsCustomFetch = novosNegocios || isPartialSelection;

  const customersFilter = useMemo(() => {
    if (!isPartialSelection) return null;
    return selectedKeys
      .map(customerParamFromKey)
      .filter((value): value is string => Boolean(value));
  }, [isPartialSelection, selectedKeys]);

  useEffect(() => {
    if (!needsCustomFetch) {
      return;
    }
    if (noneSelected) {
      return;
    }
    if (isPartialSelection && !customersFilter?.length) {
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
            customers: customersFilter ?? undefined,
            novosNegocios: novosNegocios || undefined,
          });
          if (cancelled) return;
          setFilteredMensal(response);
        } catch (err) {
          if (cancelled) return;
          setFilteredMensal(null);
          setFilteredError(
            err instanceof Error ? err.message : "Falha ao carregar série dos clientes.",
          );
        } finally {
          if (!cancelled) setFilteredLoading(false);
        }
      })();
    });

    return () => {
      cancelled = true;
    };
  }, [
    needsCustomFetch,
    noneSelected,
    isPartialSelection,
    customersFilter,
    novosNegocios,
    periodStart,
    periodEnd,
  ]);

  const activeMensal = needsCustomFetch ? filteredMensal : mensal;
  const isLoading = optionsLoading || (needsCustomFetch ? filteredLoading : loading);
  const items = noneSelected ? [] : (activeMensal?.items ?? []);
  const chartData: ChartPoint[] = items.map((item) => ({
    ...item,
    mesLabel: formatMonthYearPtBr(item.ano_mes || item.mes),
    percentLabel: formatPercent(item.percentual_em_dia_qtd),
  }));

  const multiOptions = visibleOptions.map((option) => ({
    value: option.key,
    label: option.label,
  }));

  const hint = novosNegocios
    ? allSelected || (!visibleOptions.length && !optionsLoading)
      ? "Pontualidade por quantidade — somente Novos Negócios (exceto WEG 000001)."
      : noneSelected
        ? "Nenhum cliente de Novos Negócios selecionado."
        : `Pontualidade por quantidade — Novos Negócios (${selectedKeys.length} cliente(s)).`
    : allSelected || (!customerOptions.length && !optionsLoading)
      ? "Pontualidade por quantidade (todos os clientes). Passe o ponteiro sobre o mês para ver o detalhamento."
      : noneSelected
        ? "Nenhum cliente selecionado. Marque ao menos um cliente para ver a evolução."
        : `Pontualidade por quantidade de ${selectedKeys.length} cliente(s) selecionado(s).`;

  return (
    <ChartCard
      title="Evolução mensal"
      hint={hint}
      headerActions={
        <div className="fi-chart-filters">
          <div className="fi-field--chart-filter">
            <MultiSelectField
              label="Clientes"
              options={multiOptions}
              selectedValues={selectedKeys}
              totalOptionsCount={visibleOptions.length}
              onChange={(values) => {
                setSelectedKeys(values);
                setSelectionSyncedFor(periodKey);
                if (
                  values.length === 0 ||
                  (!novosNegocios &&
                    customerOptions.length > 0 &&
                    values.length === customerOptions.length)
                ) {
                  if (!novosNegocios) {
                    setFilteredMensal(null);
                    setFilteredError(null);
                    setFilteredLoading(false);
                  }
                }
              }}
              searchable
              disabled={optionsLoading || loading}
              className="fi-field--chart-filter-multi"
            />
          </div>
          <label className="fi-check fi-check--novos-negocios">
            <input
              type="checkbox"
              checked={novosNegocios}
              disabled={optionsLoading || loading}
              onChange={(event) => {
                const enabled = event.target.checked;
                setNovosNegocios(enabled);
                setSelectionSyncedFor(periodKey);
                const nextKeys = enabled
                  ? customerOptions
                      .filter((option) => isNovosNegociosCustomer(option.cliente_codigo))
                      .map((option) => option.key)
                  : customerOptions.map((option) => option.key);
                setSelectedKeys(nextKeys);
                if (!enabled) {
                  setFilteredMensal(null);
                  setFilteredError(null);
                  setFilteredLoading(false);
                }
              }}
            />
            <span>Novos Negócios</span>
          </label>
        </div>
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
            noneSelected
              ? "Marque ao menos um cliente para visualizar a evolução mensal."
              : needsCustomFetch
                ? "Nenhum título encontrado para o filtro atual no período selecionado."
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
            {novosNegocios ? " · Novos Negócios" : ""}
            {isPartialSelection ? ` · ${selectedKeys.length} cliente(s)` : ""}.
          </p>
        </>
      ) : null}
    </ChartCard>
  );
}
