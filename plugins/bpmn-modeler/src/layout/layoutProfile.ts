/**
 * layout-profile-v1 — única fonte de tamanhos/spacings do auto-layout.
 * P5 §34-35: defaults do vendor bpmn-js extraídos para tabela central;
 * refinamento numérico permitido SOMENTE aqui.
 */

export const LAYOUT_PROFILE_V1 = {
  /** Vendor element sizes (bpmn-js defaults — nunca inventados por uso). */
  nodeSizes: {
    task: { width: 100, height: 80 },
    subProcess: { width: 350, height: 200 },
    callActivity: { width: 100, height: 80 },
    event: { width: 36, height: 36 },
    gateway: { width: 50, height: 50 },
    participant: { width: 600, height: 250 },
    lane: { width: 570, height: 135 },
    textAnnotation: { width: 100, height: 80 },
    dataObject: { width: 36, height: 50 },
    dataStore: { width: 50, height: 50 },
    default: { width: 100, height: 80 },
  },

  /** Spacing categories (P5 §34). */
  spacing: {
    nodeNodeSpacing: 30,
    nodeEdgeSpacing: 15,
    lanePadding: 30,
    poolPadding: 12,
    subprocessPadding: 20,
    rankSpacing: 50,
  },

  /** ELK layered options (P5: orthogonal routing, seed fixo). */
  elk: {
    algorithm: "layered",
    "elk.edgeRouting": "ORTHOGONAL",
    "elk.direction": "RIGHT",
    "elk.randomSeed": "1",
  } as Record<string, string>,

  /** Timeout do cálculo de layout no worker. */
  timeoutMs: 15_000,
} as const;

export type LayoutProfile = typeof LAYOUT_PROFILE_V1;

export function nodeSizeFor(bpmnType: string): { width: number; height: number } {
  const key = bpmnType.replace(/^bpmn:/, "");
  const lower = key.charAt(0).toLowerCase() + key.slice(1);
  const table = LAYOUT_PROFILE_V1.nodeSizes as Record<
    string,
    { width: number; height: number }
  >;
  if (lower in table) return table[lower];
  if (lower.endsWith("event")) return table.event;
  if (lower.endsWith("gateway")) return table.gateway;
  if (lower.includes("subprocess") || lower.includes("transaction"))
    return table.subProcess;
  if (lower.includes("task") || lower.includes("activity")) return table.task;
  return table.default;
}
