/**
 * Primário da multi-seleção de blocos = último id (espelha o filmstrip).
 * Sem campo `primaryId` extra.
 */

export function promoteSelectionPrimary(
  selectedIds: readonly string[],
  primaryId: string,
): string[] {
  if (!selectedIds.includes(primaryId)) return [...selectedIds];
  return [...selectedIds.filter((id) => id !== primaryId), primaryId];
}

/** Clique em já selecionado: promove o alvo; senão mantém a lista. */
export function resolveStageBlockSelection(input: {
  selectedIds: readonly string[];
  clickedId: string;
}): string[] {
  return promoteSelectionPrimary(input.selectedIds, input.clickedId);
}

export function resolveSelectionPrimaryId(selectedIds: readonly string[]): string | null {
  return selectedIds[selectedIds.length - 1] ?? null;
}
