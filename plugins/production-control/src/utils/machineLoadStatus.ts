import { copy } from "../content/copy";
import type { MachineLoadOperation, ProductionStatus } from "../types";

export type MachineLoadStatusBadge = {
  label: string;
  variant: "success" | "info" | "neutral";
  /** Em produção primeiro — mesma prioridade que a API aplica na fila. */
  rank: number;
};

type BalanceFields = Pick<MachineLoadOperation, "operation_pending_qty" | "pending_qty">;
type QueueStatusFields = Pick<
  MachineLoadOperation,
  "production_status" | "is_in_production" | "operation_pending_qty" | "pending_qty"
>;

const BADGES: Record<ProductionStatus, MachineLoadStatusBadge> = {
  in_progress: { label: copy.machineLoad.status.inProgress, variant: "success", rank: 0 },
  started: { label: copy.machineLoad.status.started, variant: "info", rank: 1 },
  not_started: { label: copy.machineLoad.status.notStarted, variant: "neutral", rank: 2 },
};

export function machineLoadStatusBadge(status: string | null | undefined): MachineLoadStatusBadge {
  return BADGES[status as ProductionStatus] ?? BADGES.not_started;
}

export function machineLoadStatusRank(status: string | null | undefined): number {
  return machineLoadStatusBadge(status).rank;
}

/** Saldo da bancada; cabeçalho da OP só em snapshot antigo. */
export function machineLoadOperationPendingQty(operation: BalanceFields): number | null {
  const own = operation.operation_pending_qty;
  if (typeof own === "number" && Number.isFinite(own)) return own;
  const header = operation.pending_qty;
  if (typeof header === "number" && Number.isFinite(header)) return header;
  return null;
}

/** Saldo da operação esgotado — «Já apontada» / tachar / Limpar fila. */
export function hasExhaustedMachineLoadBalance(operation: BalanceFields): boolean {
  const pending = machineLoadOperationPendingQty(operation);
  return pending !== null && pending <= 1e-9;
}

/**
 * Status de apresentação da fila: «Já apontada» só com saldo esgotado.
 * `production_status === "started"` na API só indica histórico de apontamento
 * (pode ser parcial) — não basta para tachar a linha.
 */
export function resolveMachineLoadQueueStatus(operation: QueueStatusFields): ProductionStatus {
  if (hasExhaustedMachineLoadBalance(operation)) return "started";
  if (operation.is_in_production || operation.production_status === "in_progress") {
    return "in_progress";
  }
  return "not_started";
}

/** Já apontada no contrato bruto da API (HZA com histórico, sem apontamento aberto). */
export function isMachineLoadStarted(status: string | null | undefined): boolean {
  return status === "started";
}

/**
 * Operação «finalizada» na fila do PCP: saldo da operação esgotado.
 * Em produção com saldo continua visível; apontamento parcial também.
 */
export function isMachineLoadFinishedOperation(operation: QueueStatusFields): boolean {
  return hasExhaustedMachineLoadBalance(operation);
}

/** Vista da fila sem operações já apontadas (filtro local do MFE). */
export function filterActiveMachineLoadOperations<T extends QueueStatusFields>(operations: T[]): T[] {
  return operations.filter((item) => !isMachineLoadFinishedOperation(item));
}

/** Classe de linha da fila — em produção vs já apontada (tachada). */
export function machineLoadRowModifierClass(operation: QueueStatusFields): string | undefined {
  const status = resolveMachineLoadQueueStatus(operation);
  if (status === "in_progress") return "ppc-load__row--running";
  if (status === "started") return "ppc-load__row--started";
  return undefined;
}
