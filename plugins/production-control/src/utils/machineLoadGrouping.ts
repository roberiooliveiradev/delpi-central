import type { MachineLoadOperation } from "../types";
import { machineLoadOperationKey } from "./machineLoadOperationSelection";

/**
 * Operação protegida por run aberto do cockpit — espelha a regra canônica
 * `MachineLoadService._protected_operation_keys` (Etapa 01): todo run aberto
 * protege a posição (producing, stopped, paused, unknown e inconsistent).
 *
 * A apresentação usa `execution_status` (projeção do cockpit, nunca a flag
 * congelada `is_in_production`/`production_status` — ambas zeradas no merge).
 * `execution_integrity_status === "inconsistent"` é redundância defensiva:
 * um run inconsistente também tem `display_status`.
 */
export function machineLoadOperationHasOpenRun(
  operation: Pick<
    MachineLoadOperation,
    "execution_status" | "execution_integrity_status"
  >,
): boolean {
  return (
    operation.execution_status != null ||
    operation.execution_integrity_status === "inconsistent"
  );
}

export type MachineLoadGroupingOutcome =
  | {
      status: "ok";
      /** Nova ordem da fila do CT — permutação exata de `rows`. */
      nextRows: MachineLoadOperation[];
      /** Quantidade de operações reunidas na âncora. */
      groupedCount: number;
    }
  | { status: "noop" }
  | { status: "too_few" }
  | { status: "ambiguous" }
  | { status: "protected"; blocked: MachineLoadOperation };

/**
 * Agrupa operações selecionadas na posição da primeira selecionada na ordem
 * da fila — permutação pura, sem entidade de agrupamento.
 *
 * Regras:
 * - âncora = primeira operação selecionada na ORDEM DA FILA (não do clique);
 * - selecionadas mantêm a ordem relativa entre si; não selecionadas também;
 * - cardinalidade e unicidade preservadas (permutação exata);
 * - operação com run aberto dentro do intervalo afetado (âncora exclusa —
 *   ela não se move — até a última selecionada) bloqueia o agrupamento;
 * - já contíguas → `noop`, sem write;
 * - chave selecionada duplicada na fila → `ambiguous` (não escolhe arbitrário).
 *
 * Função pura: não muta `rows`, não decide autorização — isso é do backend
 * via PATCH /machine-load/sequence (permutação exata).
 */
export function groupSelectedMachineLoadOperations(
  rows: MachineLoadOperation[],
  selectedKeys: ReadonlySet<string>,
  fallbackBranch?: string | null,
): MachineLoadGroupingOutcome {
  const keys = rows.map((row) => machineLoadOperationKey(row, fallbackBranch));
  const selectedIndices: number[] = [];
  const seen = new Set<string>();
  for (let index = 0; index < rows.length; index += 1) {
    const key = keys[index];
    if (key == null || !selectedKeys.has(key)) continue;
    if (seen.has(key)) return { status: "ambiguous" };
    seen.add(key);
    selectedIndices.push(index);
  }

  if (selectedIndices.length < 2) return { status: "too_few" };

  const anchorIndex = selectedIndices[0];
  const lastIndex = selectedIndices[selectedIndices.length - 1];

  // Intervalo afetado: tudo que muda de posição está entre a âncora e a
  // última selecionada. A âncora preserva a posição absoluta, por isso fica
  // fora do bloqueio — o restante do intervalo não pode mover run aberto.
  for (let index = anchorIndex + 1; index <= lastIndex; index += 1) {
    if (machineLoadOperationHasOpenRun(rows[index])) {
      return { status: "protected", blocked: rows[index] };
    }
  }

  const selectedSet = new Set(selectedIndices);
  const selectedInOrder = selectedIndices.map((index) => rows[index]);
  const nextRows: MachineLoadOperation[] = [];
  for (let index = 0; index < rows.length; index += 1) {
    if (index === anchorIndex) nextRows.push(...selectedInOrder);
    else if (!selectedSet.has(index)) nextRows.push(rows[index]);
  }

  // Já contíguas → mesma sequência de objetos → noop, sem write.
  if (nextRows.every((row, index) => row === rows[index])) {
    return { status: "noop" };
  }

  return { status: "ok", nextRows, groupedCount: selectedInOrder.length };
}
