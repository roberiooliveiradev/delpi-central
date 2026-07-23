/**
 * Right-click em bloco já selecionado arma tap-deselect no pointerdown;
 * o pointerup do mesmo gesto limpa a seleção com o menu ainda aberto.
 * Cancelar o arm ao abrir o menu (e ao aplicar ações do picker) evita chrome
 * sumindo e «Alterar ícone/forma» virando no-op.
 */

export function shouldCancelTapDeselectOnContextMenu(hitType: "block" | "empty"): boolean {
  return hitType === "block" || hitType === "empty";
}

/** Resolve o id do bloco ícone alvo do picker após fechar o menu de contexto. */
export function resolveContextMenuIconPickerTargetId(params: {
  menuSelectedId?: string | null;
  menuSelectedType?: string | null;
  targetBlockId?: string | null;
  targetBlockType?: string | null;
  fallbackSelectedIds?: readonly string[];
}): string | null {
  const {
    menuSelectedId,
    menuSelectedType,
    targetBlockId,
    targetBlockType,
    fallbackSelectedIds = [],
  } = params;
  if (menuSelectedType === "icon" && menuSelectedId) return menuSelectedId;
  if (targetBlockType === "icon" && targetBlockId) return targetBlockId;
  return fallbackSelectedIds[0] ?? null;
}
