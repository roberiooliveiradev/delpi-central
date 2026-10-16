import type { MachineLoadOperation } from "../types";

/**
 * Identidade canônica da seleção: filial + centro de trabalho + OP + operação.
 *
 * A chave é um `JSON.stringify` da tupla — determinístico, preserva zeros à
 * esquerda e não depende de separador que possa aparecer dentro dos campos.
 * Nunca usar índice de linha nem `OP+operação` sozinhos: a mesma combinação
 * pode aparecer em centros diferentes.
 */
export type MachineLoadOperationIdentity = Pick<
  MachineLoadOperation,
  "branch" | "work_center" | "production_order" | "operation_code"
>;

function normPart(value: string | null | undefined): string {
  return (value ?? "").trim();
}

/** Chave estável da operação para seleção; `null` quando falta parte canônica. */
export function machineLoadOperationKey(
  operation: MachineLoadOperationIdentity,
  fallbackBranch?: string | null,
): string | null {
  const branch = normPart(operation.branch) || normPart(fallbackBranch);
  const workCenter = normPart(operation.work_center);
  const order = normPart(operation.production_order);
  const operationCode = normPart(operation.operation_code);
  if (!branch || !workCenter || !order || !operationCode) return null;
  return JSON.stringify([branch, workCenter, order, operationCode]);
}

/**
 * Contexto de validade da seleção. Qualquer campo que muda zera a seleção.
 *
 * `refreshedAt` cobre a regeneração a partir do TOTVS; `sequenceUpdatedAt`
 * cobre TODA mutação da fila persistida (reordenação, priorização,
 * otimização, transferência) — inclusive a que chega com o mesmo
 * `refreshed_at`, porque mutações não regeneram o snapshot. Retiradas e
 * restaurações mexem no conjunto de operações, então são capturadas pela
 * poda de chaves (`effectiveKeys`) além deste escopo.
 */
export function machineLoadSelectionScopeKey(input: {
  branch: string;
  startDate?: string | null;
  endDate?: string | null;
  workCenter?: string | null;
  refreshedAt?: string | null;
  sequenceUpdatedAt?: string | null;
  hideFinished?: boolean;
  feedbackOnly?: boolean;
}): string {
  return JSON.stringify([
    normPart(input.branch),
    normPart(input.startDate),
    normPart(input.endDate),
    normPart(input.workCenter),
    normPart(input.refreshedAt),
    normPart(input.sequenceUpdatedAt),
    input.hideFinished ? "hf" : "",
    input.feedbackOnly ? "fb" : "",
  ]);
}

/** Chaves canônicas que aparecem mais de uma vez no contexto — ambíguas. */
export function duplicatedOperationKeys(
  rows: MachineLoadOperationIdentity[],
  fallbackBranch?: string | null,
): Set<string> {
  const counts = new Map<string, number>();
  for (const row of rows) {
    const key = machineLoadOperationKey(row, fallbackBranch);
    if (!key) continue;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const duplicated = new Set<string>();
  for (const [key, count] of counts) {
    if (count > 1) duplicated.add(key);
  }
  return duplicated;
}

export function toggleKeyInSelection(
  selected: ReadonlySet<string>,
  key: string,
): Set<string> {
  const next = new Set(selected);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  return next;
}

/**
 * Intervalo entre âncora e alvo na ordem **visível** vigente.
 * Devolve `[]` quando um dos pontos não está visível.
 */
export function rangeOperationKeys(
  orderedVisibleKeys: Array<string | null>,
  anchorKey: string,
  targetKey: string,
): string[] {
  const from = orderedVisibleKeys.indexOf(anchorKey);
  const to = orderedVisibleKeys.indexOf(targetKey);
  if (from < 0 || to < 0) return [];
  const [start, end] = from <= to ? [from, to] : [to, from];
  return orderedVisibleKeys.slice(start, end + 1).filter((k): k is string => k != null);
}

export function addKeysToSelection(
  selected: ReadonlySet<string>,
  keys: Iterable<string>,
): Set<string> {
  const next = new Set(selected);
  for (const key of keys) next.add(key);
  return next;
}

/**
 * Operações selecionadas na ordem da fila. Chaves fora do contexto atual não
 * produzem linha — a seleção nunca aponta para operações invisíveis/ausentes.
 */
export function resolveSelectedOperations<T extends MachineLoadOperationIdentity>(
  rows: T[],
  selected: ReadonlySet<string>,
  fallbackBranch?: string | null,
): T[] {
  if (selected.size === 0) return [];
  return rows.filter((row) => {
    const key = machineLoadOperationKey(row, fallbackBranch);
    return key != null && selected.has(key);
  });
}

/** Índices das linhas visíveis selecionadas — só para renderização (DataTable). */
export function selectedVisibleIndices<T extends MachineLoadOperationIdentity>(
  visibleRows: T[],
  selected: ReadonlySet<string>,
  fallbackBranch?: string | null,
): number[] {
  if (selected.size === 0) return [];
  const indices: number[] = [];
  visibleRows.forEach((row, index) => {
    const key = machineLoadOperationKey(row, fallbackBranch);
    if (key != null && selected.has(key)) indices.push(index);
  });
  return indices;
}
