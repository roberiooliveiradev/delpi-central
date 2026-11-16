/** Consolidação de APRESENTAÇÃO das linhas do roteiro oficial.
 *
 * A fonte entrega uma linha por tupla (produto, operação, componente) —
 * a mesma operação repete-se por componente. Este módulo agrupa linhas
 * para exibição usando a MESMA identidade oficial do domínio EVA
 * (produto × bom_level × operação × centro de trabalho × recurso).
 *
 * É somente renderização: nenhum número de análise (conteúdo de
 * trabalho, takt, gargalo, postos) é calculado aqui — a calculadora
 * consome `POST /v1/products/{code}/line-balance` (backend). */

import type { ProductRoutingRow } from "../types";

export type RoutingOperationView = {
  key: string;
  operation_code: string;
  operation_description: string | null;
  work_center: string | null;
  resource_code: string | null;
  operation_type: string | null;
  mandatory_operation: string | null;
  mandatory_sequence: string | null;
  mandatory_report: string | null;
  time_minutes_piece: number | null;
  setup_hours: number | null;
  components: {
    code: string;
    description: string | null;
    sequence: string | null;
  }[];
  /** Linhas oficiais fundidas nesta operação (≥1 — prova do dedup). */
  source_rows: number;
};

export type RoutingStageView = {
  key: string;
  product_code: string;
  bom_level: number;
  branch: string | null;
  route_code: string | null;
  operations: RoutingOperationView[];
};

export type RoutingGrouped = {
  rows_total: number;
  unique_operations: number;
  stages: RoutingStageView[];
};

function num(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function groupRoutingRows(
  items: ProductRoutingRow[],
): RoutingGrouped {
  const stages = new Map<string, RoutingStageView>();
  const ops = new Map<string, RoutingOperationView>();
  for (const item of items ?? []) {
    const product = String(item.product_code ?? "").trim();
    const level = num(item.bom_level) ?? 0;
    const opCode = String(item.operation_code ?? "").trim();
    const wc = String(item.work_center ?? "").trim();
    const res = String(item.resource_code ?? "").trim();
    const stageKey = `${product}#${level}`;
    let stage = stages.get(stageKey);
    if (!stage) {
      stage = {
        key: stageKey,
        product_code: product,
        bom_level: level,
        branch: item.branch ?? null,
        route_code: item.route_code ?? null,
        operations: [],
      };
      stages.set(stageKey, stage);
    }
    const opKey = `${stageKey}#${opCode}#${wc}#${res}`;
    let op = ops.get(opKey);
    if (!op) {
      op = {
        key: opKey,
        operation_code: opCode,
        operation_description: item.operation_description ?? null,
        work_center: wc || null,
        resource_code: res || null,
        operation_type: item.operation_type ?? null,
        mandatory_operation: item.mandatory_operation ?? null,
        mandatory_sequence: item.mandatory_sequence ?? null,
        mandatory_report: item.mandatory_report ?? null,
        time_minutes_piece: num(item.standard_time_minutes_piece),
        setup_hours: num(item.setup_hours),
        components: [],
        source_rows: 0,
      };
      ops.set(opKey, op);
      stage.operations.push(op);
    }
    op.source_rows += 1;
    const component = String(item.component_code ?? "").trim();
    if (
      component &&
      !op.components.some((c) => c.code === component)
    ) {
      op.components.push({
        code: component,
        description: item.component_description ?? null,
        sequence: item.component_sequence ?? null,
      });
    }
  }
  const ordered = [...stages.values()].sort(
    (a, b) =>
      a.bom_level - b.bom_level || a.product_code.localeCompare(b.product_code),
  );
  return {
    rows_total: (items ?? []).length,
    unique_operations: ordered.reduce(
      (sum, s) => sum + s.operations.length,
      0,
    ),
    stages: ordered,
  };
}

/** Rótulo curto do estágio para seletores — produto + nível BOM. */
export function stageLabel(stage: RoutingStageView): string {
  return `Estágio ${stage.bom_level} — ${stage.product_code || "produto"}`;
}

/** Formata minutos com a precisão recebida — nunca inventa unidade. */
export function formatMinutes(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${value.toLocaleString("pt-BR", {
    maximumFractionDigits: 6,
  })} min`;
}

export function formatHours(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${value.toLocaleString("pt-BR", {
    maximumFractionDigits: 4,
  })} h`;
}

export function formatRatio(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toLocaleString("pt-BR", {
    maximumFractionDigits: 1,
  })}%`;
}
