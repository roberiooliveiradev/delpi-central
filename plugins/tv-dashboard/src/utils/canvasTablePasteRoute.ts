/**
 * Roteamento de paste SO → Grade (célula ativa) vs bloco TSV novo.
 */

export type CanvasTablePasteRouteSelection = {
  blockId: string;
  cells: readonly { row: number; col: number }[];
  focus?: { row: number; col: number } | null;
} | null | undefined;

/** Quando true, o paste global não deve criar bloco TSV — cola na Grade. */
export function shouldRoutePasteToCanvasTable(params: {
  selectedCanvasTableCell: CanvasTablePasteRouteSelection;
  editingTextId?: string | null;
}): boolean {
  if (params.editingTextId) return false;
  const selection = params.selectedCanvasTableCell;
  if (!selection?.blockId) return false;
  return (selection.cells?.length ?? 0) > 0;
}

export function resolveCanvasTablePasteOrigin(
  selection: NonNullable<CanvasTablePasteRouteSelection>,
): { row: number; col: number } {
  return selection.focus ?? selection.cells[0] ?? { row: 0, col: 0 };
}
