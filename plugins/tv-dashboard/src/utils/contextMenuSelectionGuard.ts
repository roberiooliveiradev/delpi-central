/**
 * Right-click em bloco já selecionado arma tap-deselect no pointerdown;
 * o pointerup do mesmo gesto limpa a seleção com o menu ainda aberto.
 * Cancelar o arm ao abrir o menu (e ao aplicar ações do picker) evita chrome
 * sumindo e «Alterar ícone/forma» virando no-op.
 *
 * Ações do menu (Alinhar / Girar / …) devem usar o snapshot da sessão —
 * nunca recalcular a partir de `selectedIds` live (pode ter sido limpa ou
 * colapsada para o `targetBlockId` e destruir o grupo fechado).
 */

type BlockWithGroup = { id: string; groupId?: string };

export function shouldCancelTapDeselectOnContextMenu(hitType: "block" | "empty"): boolean {
  return hitType === "block" || hitType === "empty";
}

function expandTargetGroupMembers(
  blocks: readonly BlockWithGroup[],
  targetBlockId: string,
): string[] {
  const target = blocks.find((block) => block.id === targetBlockId);
  if (!target?.groupId) return [targetBlockId];
  const members = blocks
    .filter((block) => block.groupId === target.groupId)
    .map((block) => block.id);
  return members.length > 0 ? members : [targetBlockId];
}

/**
 * Congela os ids da seleção no momento em que o menu abre.
 * - Alvo já na seleção → preserva a seleção inteira (grupo fechado incluso).
 * - Alvo fora da seleção → expande o grupo do alvo (sem alterar live até o apply).
 * - Fundo do palco → preserva a seleção atual.
 */
export function resolveContextMenuSessionSelectedIds(params: {
  selectedIds: readonly string[];
  targetBlockId: string | null;
  blocks: readonly BlockWithGroup[];
}): string[] {
  const { selectedIds, targetBlockId, blocks } = params;
  if (targetBlockId && selectedIds.includes(targetBlockId)) {
    return [...selectedIds];
  }
  if (targetBlockId) {
    return expandTargetGroupMembers(blocks, targetBlockId);
  }
  return [...selectedIds];
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

/** True se as duas listas têm os mesmos ids (ordem irrelevante). */
export function sameSelectedIdSet(
  a: readonly string[],
  b: readonly string[],
): boolean {
  if (a.length !== b.length) return false;
  const setB = new Set(b);
  return a.every((id) => setB.has(id));
}
