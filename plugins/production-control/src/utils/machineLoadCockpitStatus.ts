import type {
  MachineLoadBalancesPayload,
  MachineLoadCockpitStatusItem,
  MachineLoadCockpitStatusPayload,
  MachineLoadOperation,
  MachineLoadPayload,
} from "../types";

/**
 * Identidade canônica da EXECUÇÃO: centro + OP + operação, dentro da filial
 * (espelha `protected_operation_key` do backend — CT e OP em caixa alta, como
 * saem do TOTVS; a operação só é aparada).
 *
 * O centro não é opcional: a mesma OP/operação pode existir em outra bancada
 * (transferência) sem run — casar só por OP+operação mostraria «Produzindo»
 * no posto errado.
 */
export function machineLoadExecutionKey(
  workCenter: string | null | undefined,
  productionOrder: string,
  operationCode: string,
): string {
  return `${(workCenter ?? "").trim().toUpperCase()}|${productionOrder
    .trim()
    .toUpperCase()}|${operationCode.trim()}`;
}

/** Identidade do SALDO SH6/SC2: OP + operação — o saldo é da operação, não da bancada. */
function operationKey(productionOrder: string, operationCode: string): string {
  return `${productionOrder.trim()}|${operationCode.trim()}`;
}

function runsByKey(
  items: MachineLoadCockpitStatusItem[],
): Map<string, MachineLoadCockpitStatusItem> {
  const index = new Map<string, MachineLoadCockpitStatusItem>();
  for (const item of items) {
    index.set(
      machineLoadExecutionKey(item.work_center, item.production_order, item.operation_code),
      item,
    );
  }
  return index;
}

function withExecution(
  operation: MachineLoadOperation,
  run: MachineLoadCockpitStatusItem | undefined,
): MachineLoadOperation {
  const next = {
    execution_status: run ? run.display_status : null,
    execution_integrity_status: run ? run.integrity_status : null,
    execution_started_at: run ? (run.started_at ?? null) : null,
    // Flags enriquecidas por HZA no snapshot congelado nunca sinalizam
    // produção na interface nova: zeradas aqui, sem ressurreição.
    is_in_production: false,
    active_operator_code: null,
    active_operator_name: null,
    active_operator_count: 0,
    production_started_date: null,
    production_started_time: null,
    appointment_count: 0,
    last_appointment_date: null,
  } as const;
  const unchanged = (Object.keys(next) as (keyof typeof next)[]).every(
    (key) => operation[key] === next[key],
  );
  if (unchanged) return operation;
  return { ...operation, ...next };
}

/**
 * Aplica o snapshot de execução do cockpit sobre a fila congelada.
 *
 * Diferente do antigo live-status (HZA), a resposta é um SNAPSHOT COMPLETO dos
 * runs abertos: operação ausente não tem execução — os campos `execution_*`
 * são zerados, então um `items: []` limpa todos os estados ativos. Flags HZA
 * congeladas no snapshot (`is_in_production`, `production_status`) nunca
 * voltam a sinalizar produção: a apresentação lê só `execution_*`.
 *
 * A ordem e o conteúdo da fila não mudam — só a projeção de execução. Os
 * contadores «em produção» contam somente `display_status === "producing"`;
 * stopped/paused/unknown têm estado próprio e não inflam o indicador.
 */
export function applyMachineLoadCockpitStatus(
  payload: MachineLoadPayload,
  status: MachineLoadCockpitStatusPayload,
): MachineLoadPayload {
  const queue = payload.operations;
  if (!queue) return payload;
  // Resposta de outra filial nunca projeta estado nesta fila.
  if (
    status.branch != null &&
    payload.branch != null &&
    status.branch.trim() !== payload.branch.trim()
  ) {
    return payload;
  }

  const index = runsByKey(status.items ?? []);

  let changed = false;
  const operations = queue.map((operation) => {
    const run = index.get(
      machineLoadExecutionKey(
        operation.work_center,
        operation.production_order,
        operation.operation_code,
      ),
    );
    const merged = withExecution(operation, run);
    if (merged !== operation) changed = true;
    return merged;
  });

  if (!changed) return payload;

  const producingByCenter = new Map<string, number>();
  let producingCount = 0;
  for (const operation of operations) {
    if (operation.execution_status !== "producing") continue;
    producingCount += 1;
    const center = operation.work_center.trim();
    producingByCenter.set(center, (producingByCenter.get(center) ?? 0) + 1);
  }

  return {
    ...payload,
    operations,
    summary: { ...payload.summary, in_production_count: producingCount },
    work_centers: payload.work_centers.map((center) => ({
      ...center,
      in_production_count: producingByCenter.get(center.work_center.trim()) ?? 0,
    })),
  };
}

/**
 * Aplica os saldos SH6/SC2 sobre a fila — independente do estado de execução.
 *
 * Operação ausente do lote mantém o último saldo conhecido (saldo desconhecido
 * nunca esconde trabalho). Nenhum campo `execution_*` é tocado e a fila não é
 * reordenada: é atualização de quantidades, não de execução.
 */
export function applyMachineLoadBalances(
  payload: MachineLoadPayload,
  balances: MachineLoadBalancesPayload,
): MachineLoadPayload {
  const queue = payload.operations;
  if (!queue) return payload;
  // Mesma guarda da execução: lote de outra filial nunca aplica aqui.
  if (
    balances.branch != null &&
    payload.branch != null &&
    balances.branch.trim() !== payload.branch.trim()
  ) {
    return payload;
  }

  const index = new Map<string, { produced: number | null; pending: number | null }>();
  for (const item of balances.items ?? []) {
    index.set(operationKey(item.production_order, item.operation_code), {
      produced: item.operation_produced_qty,
      pending: item.operation_pending_qty,
    });
  }
  if (index.size === 0) return payload;

  let changed = false;
  const operations = queue.map((operation) => {
    const balance = index.get(operationKey(operation.production_order, operation.operation_code));
    if (!balance) return operation;
    if (
      operation.operation_produced_qty === balance.produced &&
      operation.operation_pending_qty === balance.pending
    ) {
      return operation;
    }
    changed = true;
    return {
      ...operation,
      operation_produced_qty: balance.produced,
      operation_pending_qty: balance.pending,
    };
  });

  if (!changed) return payload;
  return { ...payload, operations };
}
