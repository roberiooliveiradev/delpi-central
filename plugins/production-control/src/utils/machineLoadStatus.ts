import { copy } from "../content/copy";
import type { MachineLoadOperation, ProductionStatus } from "../types";

export type MachineLoadStatusBadge = {
  label: string;
  variant: "success" | "info" | "neutral";
  /** Em produção primeiro — mesma prioridade que a API aplica na fila. */
  rank: number;
};

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

/** Já apontada (HZA com histórico, sem apontamento aberto). */
export function isMachineLoadStarted(status: string | null | undefined): boolean {
  return status === "started";
}

/**
 * Operação «finalizada» na fila do PCP: já apontada e não rodando agora.
 * Em produção continua visível mesmo com status legado inconsistente.
 */
export function isMachineLoadFinishedOperation(
  operation: Pick<MachineLoadOperation, "production_status" | "is_in_production">,
): boolean {
  if (operation.is_in_production) return false;
  return isMachineLoadStarted(operation.production_status);
}

/** Vista da fila sem operações já apontadas (filtro local do MFE). */
export function filterActiveMachineLoadOperations<
  T extends Pick<MachineLoadOperation, "production_status" | "is_in_production">,
>(operations: T[]): T[] {
  return operations.filter((item) => !isMachineLoadFinishedOperation(item));
}

/** Classe de linha da fila — em produção vs já apontada (tachada). */
export function machineLoadRowModifierClass(
  operation: Pick<MachineLoadOperation, "production_status" | "is_in_production">,
): string | undefined {
  if (operation.is_in_production) return "ppc-load__row--running";
  if (isMachineLoadStarted(operation.production_status)) return "ppc-load__row--started";
  return undefined;
}
