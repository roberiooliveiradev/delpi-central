import type {
  MachineLoadLiveStatusItem,
  MachineLoadLiveStatusPayload,
  MachineLoadOperation,
  MachineLoadPayload,
} from "../types";

/** Mesma lista que a API sobrescreve na fila congelada (`_STATUS_FIELDS`). */
const STATUS_FIELDS = [
  "production_status",
  "is_in_production",
  "production_started_date",
  "production_started_time",
  "active_operator_code",
  "active_operator_name",
  "active_operator_count",
  "appointment_count",
  "last_appointment_date",
  "operation_produced_qty",
  "operation_pending_qty",
] as const satisfies ReadonlyArray<keyof MachineLoadOperation>;

function operationKey(productionOrder: string, operationCode: string): string {
  return `${productionOrder.trim()}|${operationCode.trim()}`;
}

function statusByKey(
  items: MachineLoadLiveStatusItem[],
): Map<string, MachineLoadLiveStatusItem> {
  const index = new Map<string, MachineLoadLiveStatusItem>();
  for (const item of items) {
    index.set(operationKey(item.production_order, item.operation_code), item);
  }
  return index;
}

function withLiveStatus(
  operation: MachineLoadOperation,
  status: MachineLoadLiveStatusItem,
): MachineLoadOperation {
  const merged = { ...operation };
  for (const field of STATUS_FIELDS) {
    if (field in status) {
      // Campo a campo: o status vivo só sobrescreve o que o chão de fábrica informou.
      (merged as Record<string, unknown>)[field] = (status as Record<string, unknown>)[field];
    }
  }
  return merged;
}

/**
 * Aplica o status vivo (HZA) sobre a fila congelada que já está em memória.
 *
 * Operação ausente do status mantém o valor do snapshot — mesma semântica de
 * `_apply_status_map` na API. Os contadores de «em produção» são recalculados
 * porque as abas e o resumo dependem deles.
 */
export function applyMachineLoadLiveStatus(
  payload: MachineLoadPayload,
  live: MachineLoadLiveStatusPayload,
): MachineLoadPayload {
  const queue = payload.operations;
  if (!queue) return payload;

  const index = statusByKey(live.items ?? []);
  if (index.size === 0) return payload;

  let changed = false;
  const operations = queue.map((operation) => {
    const status = index.get(
      operationKey(operation.production_order, operation.operation_code),
    );
    if (!status) return operation;
    const merged = withLiveStatus(operation, status);
    if (!changed) {
      changed = STATUS_FIELDS.some((field) => merged[field] !== operation[field]);
    }
    return merged;
  });

  if (!changed) return payload;

  const runningByCenter = new Map<string, number>();
  let inProductionCount = 0;
  for (const operation of operations) {
    if (!operation.is_in_production) continue;
    inProductionCount += 1;
    const center = operation.work_center.trim();
    runningByCenter.set(center, (runningByCenter.get(center) ?? 0) + 1);
  }

  return {
    ...payload,
    operations,
    summary: { ...payload.summary, in_production_count: inProductionCount },
    work_centers: payload.work_centers.map((center) => ({
      ...center,
      in_production_count: runningByCenter.get(center.work_center.trim()) ?? 0,
    })),
  };
}
