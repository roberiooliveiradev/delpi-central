/**
 * Resolve quais grupos da ribbon colapsam (direita → esquerda).
 * Retorna ids que devem renderizar como botão + popover.
 */

export type RibbonGroupSize = {
  id: string;
  expandedWidth: number;
  collapsedWidth: number;
  /** Ordem visual (0 = esquerda). */
  order: number;
};

export function sumRibbonGroupsWidth(
  groups: ReadonlyArray<RibbonGroupSize>,
  collapsedIds: ReadonlySet<string>,
  gap: number,
): number {
  if (groups.length === 0) return 0;
  let sum = 0;
  for (const group of groups) {
    const w = collapsedIds.has(group.id) ? group.collapsedWidth : group.expandedWidth;
    sum += Math.max(0, w);
  }
  return sum + gap * Math.max(0, groups.length - 1);
}

/**
 * Colapsa do fim da faixa (direita) até caber em `availableWidth`.
 * Grupos sem medidas válidas são tratados como expandídos com largura 0.
 */
export function resolveCollapsedRibbonGroupIds(
  groups: ReadonlyArray<RibbonGroupSize>,
  availableWidth: number,
  gap = 8,
): Set<string> {
  const collapsed = new Set<string>();
  if (!(availableWidth > 0) || groups.length === 0) return collapsed;

  const ordered = [...groups].sort((a, b) => a.order - b.order);
  const safe = ordered.map((group) => ({
    ...group,
    expandedWidth: Math.max(0, group.expandedWidth),
    collapsedWidth: Math.max(0, group.collapsedWidth || 56),
  }));

  while (
    safe.length > 0 &&
    sumRibbonGroupsWidth(safe, collapsed, gap) > availableWidth
  ) {
    let candidate: RibbonGroupSize | null = null;
    for (let i = safe.length - 1; i >= 0; i -= 1) {
      const group = safe[i];
      if (!collapsed.has(group.id)) {
        candidate = group;
        break;
      }
    }
    if (!candidate) break;
    /* Já todos colapsados e ainda não cabe — para (scroll fallback no host). */
    if (
      candidate.expandedWidth <= candidate.collapsedWidth &&
      collapsed.size === safe.length - 1
    ) {
      collapsed.add(candidate.id);
      break;
    }
    collapsed.add(candidate.id);
    if (collapsed.size >= safe.length) break;
  }

  return collapsed;
}
