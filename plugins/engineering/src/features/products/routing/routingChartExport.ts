/** Payloads de exportação tabular (CSV / Excel / PDF) dos gráficos do
 * Routing Study — contexto completo por linha: produto, filial, estágio,
 * cenário e unidade de exibição. Apenas dados efetivamente exibidos são
 * exportados — nunca valores inventados nem de outro contexto. */

import type { TableExportPayload } from "@delpi/plugin-ui/index";

export type RoutingChartContext = {
  productCode: string;
  branch: string;
  stageLabel: string;
  scenarioLabel?: string | null;
  unit: string;
};

export type OperationTimeRow = {
  operation: string;
  workCenter: string;
  description?: string | null;
  /** Valor já convertido para a unidade de exibição. */
  time: number | null;
  overTakt?: boolean | null;
};

function contextColumns(ctx: RoutingChartContext) {
  return [
    { key: "produto", label: "Produto" },
    { key: "filial", label: "Filial" },
    { key: "estagio", label: "Estágio" },
    ...(ctx.scenarioLabel
      ? [{ key: "cenario", label: "Cenário" }]
      : []),
  ];
}

function contextValues(ctx: RoutingChartContext) {
  return {
    produto: ctx.productCode,
    filial: ctx.branch || "—",
    estagio: ctx.stageLabel,
    ...(ctx.scenarioLabel ? { cenario: ctx.scenarioLabel } : {}),
  };
}

function formatValue(value: number | null | undefined, decimals: number) {
  if (value == null || !Number.isFinite(value)) return "—";
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  });
}

/** G01 — tempo por operação (OBSERVED). */
export function buildOpsTimeExportPayload(
  ctx: RoutingChartContext,
  rows: OperationTimeRow[],
  decimals: number,
): TableExportPayload {
  return {
    title: `Tempo por operação — ${ctx.productCode} (${ctx.unit})`,
    columns: [
      ...contextColumns(ctx),
      { key: "operacao", label: "Operação" },
      { key: "ct", label: "Centro de trabalho" },
      { key: "descricao", label: "Descrição" },
      { key: "tempo", label: `Tempo por peça (${ctx.unit})` },
      { key: "proveniencia", label: "Proveniência" },
    ],
    rows: rows.map((row) => ({
      ...contextValues(ctx),
      operacao: row.operation,
      ct: row.workCenter,
      descricao: row.description ?? "—",
      tempo: formatValue(row.time, decimals),
      proveniencia: "OBSERVED",
    })),
  };
}

/** G02 — tempo × takt (tempo OBSERVED + takt CALCULATED). */
export function buildOpsVsTaktExportPayload(
  ctx: RoutingChartContext,
  rows: OperationTimeRow[],
  takt: number | null,
  decimals: number,
): TableExportPayload {
  return {
    title: `Tempo × takt — ${ctx.productCode} (${ctx.unit})`,
    columns: [
      ...contextColumns(ctx),
      { key: "operacao", label: "Operação" },
      { key: "ct", label: "Centro de trabalho" },
      { key: "tempo", label: `Tempo por peça (${ctx.unit})` },
      { key: "takt", label: `Takt (${ctx.unit})` },
      { key: "acimaTakt", label: "Acima do takt" },
      { key: "proveniencia", label: "Proveniência" },
    ],
    rows: rows.map((row) => ({
      ...contextValues(ctx),
      operacao: row.operation,
      ct: row.workCenter,
      tempo: formatValue(row.time, decimals),
      takt: formatValue(takt, decimals),
      acimaTakt: row.overTakt == null ? "—" : row.overTakt ? "Sim" : "Não",
      proveniencia: "OBSERVED + CALCULATED",
    })),
  };
}

export type StationLoadRow = {
  station: string;
  load: number | null;
  operations?: string;
};

/** G03 — distribuição simulada por posto (SIMULATION). */
export function buildSimDistributionExportPayload(
  ctx: RoutingChartContext,
  rows: StationLoadRow[],
  decimals: number,
): TableExportPayload {
  return {
    title: `Distribuição simulada — ${ctx.productCode} (${ctx.unit})`,
    columns: [
      ...contextColumns(ctx),
      { key: "posto", label: "Posto (simulado)" },
      { key: "carga", label: `Carga (${ctx.unit})` },
      { key: "operacoes", label: "Operações atribuídas" },
      { key: "proveniencia", label: "Proveniência" },
    ],
    rows: rows.map((row) => ({
      ...contextValues(ctx),
      posto: row.station,
      carga: formatValue(row.load, decimals),
      operacoes: row.operations ?? "—",
      proveniencia: "SIMULATION",
    })),
  };
}
