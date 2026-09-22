import {
  filterActiveMachineLoadOperations,
  isMachineLoadFinishedOperation,
} from "./machineLoadStatus";

type QueueRow = {
  production_order: string;
  operation_code: string;
  production_status?: string | null;
  is_in_production?: boolean | null;
  operation_pending_qty?: number | null;
  pending_qty?: number | null;
};

function operationKey(row: QueueRow): string {
  return `${row.production_order}|${row.operation_code}`;
}

/**
 * Aplica a ordem das linhas visíveis (ativas) na fila completa do CT.
 *
 * Finalizadas ficam pinadas na posição absoluta; só os slots ativos são
 * preenchidos na nova ordem. Assim o PATCH continua mandando a permutação
 * exata exigida pela API mesmo com «Ocultar finalizadas» ligado.
 */
export function mergeActiveOrderIntoMachineLoadQueue<T extends QueueRow>(
  fullRows: T[],
  reorderedActive: T[],
): T[] {
  if (fullRows.length === 0) return fullRows;
  if (reorderedActive.length === fullRows.length) return reorderedActive;

  const expectedActive = filterActiveMachineLoadOperations(fullRows);
  if (reorderedActive.length !== expectedActive.length) return fullRows;

  const expectedKeys = new Set(expectedActive.map(operationKey));
  const nextKeys = reorderedActive.map(operationKey);
  if (nextKeys.some((key) => !expectedKeys.has(key))) return fullRows;
  if (new Set(nextKeys).size !== nextKeys.length) return fullRows;

  const pending = [...reorderedActive];
  return fullRows.map((row) => {
    if (isMachineLoadFinishedOperation(row)) return row;
    return pending.shift() ?? row;
  });
}
