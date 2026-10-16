import { copy } from "../content/copy";
import type { MachineLoadExecutionStatus } from "../types";

/**
 * Status de apresentação da fila — derivado da execução do cockpit e do saldo.
 *
 * - `in_progress`: run aberto produzindo no cockpit.
 * - `stopped`: run aberto com parada registrada.
 * - `paused`: run aberto pausado pelo operador.
 * - `unconfirmed`: run aberto com leitura inconsistente (não confirmada).
 * - `started`: saldo da operação esgotado e nenhum run aberto («Já apontada»).
 * - `not_started`: nenhum run aberto — flags HZA do snapshot não contam.
 */
export type MachineLoadQueueStatus =
  | "in_progress"
  | "stopped"
  | "paused"
  | "unconfirmed"
  | "started"
  | "not_started";

export type MachineLoadStatusBadge = {
  label: string;
  variant: "success" | "warning" | "info" | "neutral";
  /** Execução primeiro — produzindo lidera a fila visual. */
  rank: number;
};

/** Estrutural e solto — aceita linhas parciais (reorder, locate, stops). */
type BalanceFields = {
  pending_qty?: number | null;
  operation_pending_qty?: number | null;
};
type ExecutionFields = { execution_status?: MachineLoadExecutionStatus | string | null };
type QueueStatusFields = BalanceFields & ExecutionFields;

const BADGES: Record<MachineLoadQueueStatus, MachineLoadStatusBadge> = {
  in_progress: { label: copy.machineLoad.status.inProgress, variant: "success", rank: 0 },
  stopped: { label: copy.machineLoad.status.stopped, variant: "warning", rank: 1 },
  paused: { label: copy.machineLoad.status.paused, variant: "info", rank: 2 },
  unconfirmed: { label: copy.machineLoad.status.unconfirmed, variant: "warning", rank: 3 },
  started: { label: copy.machineLoad.status.started, variant: "info", rank: 4 },
  not_started: { label: copy.machineLoad.status.notStarted, variant: "neutral", rank: 5 },
};

export function machineLoadStatusBadge(
  status: MachineLoadQueueStatus | string | null | undefined,
): MachineLoadStatusBadge {
  return BADGES[status as MachineLoadQueueStatus] ?? BADGES.not_started;
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
 * Estado de apresentação da fila. A execução vem exclusivamente do cockpit
 * (`execution_status`): OP com HZA aberta e sem run não aparece produzindo.
 * Saldo esgotado só vira «Já apontada» quando não há run — execução tem
 * prioridade visual e um run aberto nunca é escondido pelo saldo do ERP.
 */
export function resolveMachineLoadQueueStatus(operation: QueueStatusFields): MachineLoadQueueStatus {
  switch (operation.execution_status) {
    case "producing":
      return "in_progress";
    case "stopped":
      return "stopped";
    case "paused":
      return "paused";
    case "unknown":
      return "unconfirmed";
    default:
      break;
  }
  if (hasExhaustedMachineLoadBalance(operation)) return "started";
  return "not_started";
}

/**
 * Operação «finalizada» na fila do PCP: saldo esgotado **sem run aberto**.
 * Um run aberto (produzindo/parada/pausada/inconsistente) mantém a operação
 * visível mesmo com o saldo do ERP zerado — execução real nunca é ocultada.
 */
export function isMachineLoadFinishedOperation(operation: QueueStatusFields): boolean {
  if (operation.execution_status != null) return false;
  return hasExhaustedMachineLoadBalance(operation);
}

/** Vista da fila sem operações já apontadas (filtro local do MFE). */
export function filterActiveMachineLoadOperations<T extends QueueStatusFields>(operations: T[]): T[] {
  return operations.filter((item) => !isMachineLoadFinishedOperation(item));
}

/** Classe de linha da fila — execução do cockpit vs já apontada (tachada). */
export function machineLoadRowModifierClass(operation: QueueStatusFields): string | undefined {
  const status = resolveMachineLoadQueueStatus(operation);
  if (status === "in_progress") return "ppc-load__row--running";
  if (status === "stopped") return "ppc-load__row--stopped";
  if (status === "paused") return "ppc-load__row--paused";
  if (status === "unconfirmed") return "ppc-load__row--unconfirmed";
  if (status === "started") return "ppc-load__row--started";
  return undefined;
}
