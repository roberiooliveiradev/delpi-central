/** Yamazumi — helpers puros de apresentação (carga por posto,
 * operações não atribuídas, séries do gráfico e payload de exportação).
 * Nenhuma regra de domínio: a carga é a soma simples dos tempos por
 * peça OBSERVED das operações atribuídas — a mesma soma que o usuário
 * faria manualmente, marcada SIMULATION/DRAFT_LOCAL. Tempos ausentes
 * permanecem UNKNOWN, nunca zero fictício. Não há decomposição em
 * manual/automático/caminhada: o contrato oficial expõe apenas tempo
 * padrão agregado. */

import type { HypotheticalPost } from "../../products/routing/routingStudyDraft";
import type { RoutingOperationView } from "../../products/routing/routingGrouping";

/** Única categoria honesta de tempo disponível no contrato oficial. */
export const AGGREGATE_TIME_CATEGORY =
  "Tempo padrão agregado — composição desconhecida";

/** Rotação de tokens do design system para os segmentos por operação. */
const OP_SEGMENT_FILLS = [
  "var(--delpi-ui-accent, #2563eb)",
  "var(--delpi-ui-success, #16a34a)",
  "var(--delpi-ui-warning, #d97706)",
  "var(--delpi-ui-info, #0284c7)",
] as const;

export const TAKT_LINE_FILL = "var(--delpi-ui-danger, #dc2626)";

export type YamazumiPostLoad = {
  postId: string;
  postName: string;
  /** Soma dos tempos por peça das operações atribuídas (null quando
   * nenhuma operação tem tempo). */
  loadMinutes: number | null;
  /** Operações atribuídas com tempo oficial. */
  timedOps: RoutingOperationView[];
  /** Operações atribuídas sem tempo (UNKNOWN — nunca zeradas). */
  unknownOps: RoutingOperationView[];
  empty: boolean;
};

export function computePostLoads(
  posts: HypotheticalPost[],
  operations: RoutingOperationView[],
): YamazumiPostLoad[] {
  const byKey = new Map(operations.map((op) => [op.key, op]));
  return posts.map((post, index) => {
    const assigned = post.operationRefs
      .map((ref) => byKey.get(ref))
      .filter((op): op is RoutingOperationView => Boolean(op));
    const timedOps = assigned.filter(
      (op) => op.time_minutes_piece != null,
    );
    const unknownOps = assigned.filter(
      (op) => op.time_minutes_piece == null,
    );
    const loadMinutes = timedOps.length
      ? timedOps.reduce((acc, op) => acc + (op.time_minutes_piece ?? 0), 0)
      : null;
    return {
      postId: post.clientId,
      postName: post.name || `Posto ${String(index + 1).padStart(2, "0")}`,
      loadMinutes,
      timedOps,
      unknownOps,
      empty: assigned.length === 0,
    };
  });
}

export function unassignedOperations(
  posts: HypotheticalPost[],
  operations: RoutingOperationView[],
): RoutingOperationView[] {
  const assigned = new Set(posts.flatMap((p) => p.operationRefs));
  return operations.filter((op) => !assigned.has(op.key));
}

/** Move/atribui uma operação para o posto alvo — remove de outros
 * postos (política exclusiva: uma operação contribui carga em um único
 * posto; divisão/paralelismo exigiriam regra explícita, não inferida).
 * Retorna os patches por posto a aplicar no rascunho. */
export function assignOperationToPost(
  posts: HypotheticalPost[],
  opKey: string,
  targetPostId: string,
): { postId: string; patch: { operationRefs: string[] } }[] {
  const updates: {
    postId: string;
    patch: { operationRefs: string[] };
  }[] = [];
  for (const post of posts) {
    const has = post.operationRefs.includes(opKey);
    const isTarget = post.clientId === targetPostId;
    if (has && !isTarget) {
      updates.push({
        postId: post.clientId,
        patch: {
          operationRefs: post.operationRefs.filter((r) => r !== opKey),
        },
      });
    } else if (!has && isTarget) {
      updates.push({
        postId: post.clientId,
        patch: { operationRefs: [...post.operationRefs, opKey] },
      });
    }
  }
  return updates;
}

export type YamazumiChartSpec = {
  /** Uma linha por posto; chaves `op_<key>` em MINUTOS (a conversão de
   * unidade é da camada de apresentação no RoutingSeriesChart). */
  rows: Record<string, unknown>[];
  /** Série empilhada por operação (com tempo) + linha do takt. */
  series: {
    dataKey: string;
    name: string;
    fill: string;
    plotAs?: "bar" | "line";
    trendCapable?: boolean;
  }[];
  /** Segmentos empilháveis por posto (chave → rótulo da operação). */
  segmentLabels: Record<string, string>;
};

export function buildYamazumiChartSpec(
  loads: YamazumiPostLoad[],
  taktMinutes: number | null,
): YamazumiChartSpec {
  /* Catálogo estável de operações com tempo — um segmento por op, na
   * ordem do roteiro (aparição nos postos). */
  const opsInOrder: RoutingOperationView[] = [];
  const seen = new Set<string>();
  for (const load of loads) {
    for (const op of load.timedOps) {
      if (!seen.has(op.key)) {
        seen.add(op.key);
        opsInOrder.push(op);
      }
    }
  }
  const dataKeyOf = (opKey: string) => `op_${opKey}`;
  const segmentLabels: Record<string, string> = {};
  opsInOrder.forEach((op) => {
    segmentLabels[dataKeyOf(op.key)] =
      `${op.operation_code || "—"} — ${op.operation_description ?? "—"}`;
  });

  const rows = loads.map((load) => {
    const row: Record<string, unknown> = {
      post: load.postName,
      postId: load.postId,
    };
    for (const op of opsInOrder) {
      row[dataKeyOf(op.key)] = load.timedOps.some((o) => o.key === op.key)
        ? op.time_minutes_piece
        : 0;
    }
    if (taktMinutes != null) row.takt = taktMinutes;
    return row;
  });

  const series: YamazumiChartSpec["series"] = opsInOrder.map((op, i) => ({
    dataKey: dataKeyOf(op.key),
    name: `${op.operation_code || "—"}`,
    fill: OP_SEGMENT_FILLS[i % OP_SEGMENT_FILLS.length],
    trendCapable: false,
  }));
  if (taktMinutes != null) {
    series.push({
      dataKey: "takt",
      name: "Takt",
      fill: TAKT_LINE_FILL,
      plotAs: "line",
      trendCapable: false,
    });
  }
  return { rows, series, segmentLabels };
}

export type YamazumiExportRow = {
  post: string;
  order: number;
  operation_code: string;
  operation_description: string;
  work_center: string;
  resource: string;
  time_minutes_piece: number | "UNKNOWN";
  provenance: string;
};

export function buildYamazumiExportRows(
  loads: YamazumiPostLoad[],
  unassigned: RoutingOperationView[],
): YamazumiExportRow[] {
  const rows: YamazumiExportRow[] = [];
  loads.forEach((load, index) => {
    const ops = [...load.timedOps, ...load.unknownOps];
    if (!ops.length) {
      rows.push({
        post: load.postName,
        order: index + 1,
        operation_code: "—",
        operation_description: "(posto sem operações atribuídas)",
        work_center: "",
        resource: "",
        time_minutes_piece: "UNKNOWN",
        provenance: "DRAFT_LOCAL",
      });
      return;
    }
    for (const op of ops) {
      rows.push({
        post: load.postName,
        order: index + 1,
        operation_code: op.operation_code || "—",
        operation_description: op.operation_description ?? "—",
        work_center: op.work_center ?? "",
        resource: op.resource_code ?? "",
        time_minutes_piece: op.time_minutes_piece ?? "UNKNOWN",
        provenance: "OBSERVED+DRAFT_LOCAL",
      });
    }
  });
  for (const op of unassigned) {
    rows.push({
      post: "(não atribuída)",
      order: 0,
      operation_code: op.operation_code || "—",
      operation_description: op.operation_description ?? "—",
      work_center: op.work_center ?? "",
      resource: op.resource_code ?? "",
      time_minutes_piece: op.time_minutes_piece ?? "UNKNOWN",
      provenance: "OBSERVED (não atribuída)",
    });
  }
  return rows;
}
