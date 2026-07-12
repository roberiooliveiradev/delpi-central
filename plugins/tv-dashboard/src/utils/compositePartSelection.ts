/**
 * Política de clique em partes de widgets compostos (KPI / chart / table).
 * Seleção de parte = duplo clique; clique simples move o bloco (ou a parte já ativa).
 */

export type CompositePartPointerAction = "drag-block" | "part-move";

/**
 * - Bloco ainda não selecionado / modo global / outra parte → arrastar o bloco (destravar).
 * - Mesma parte já selecionada e móvel → arrastar a parte.
 */
export function resolveCompositePartPointerAction(params: {
  blockSelected: boolean;
  samePartSelected: boolean;
  partAllowsMove: boolean;
}): CompositePartPointerAction {
  if (params.blockSelected && params.samePartSelected && params.partAllowsMove) {
    return "part-move";
  }
  return "drag-block";
}
