/**
 * Política de clique em células da Grade (`canvas_table`).
 *
 * Paridade com texto/composito em dois estágios:
 * - 1º clique (bloco não selecionado) → seleciona o container (evento sobe ao wrap).
 * - 2º clique (bloco já selecionado) → seleciona/edita a célula.
 */

export type CanvasTableCellPointerAction = "select-block" | "select-cell";

export function resolveCanvasTableCellPointerAction(params: {
  blockSelected: boolean;
}): CanvasTableCellPointerAction {
  return params.blockSelected ? "select-cell" : "select-block";
}
