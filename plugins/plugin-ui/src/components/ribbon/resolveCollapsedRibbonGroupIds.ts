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

/** Folga exigida para reexpandir um grupo já colapsado (evita oscilação RO ↔ setState). */
export const RIBBON_COLLAPSE_EXPAND_HYSTERESIS_PX = 24;

/** Ignora ruído de subpixel / ceil ao registrar medidas. */
export const RIBBON_GROUP_WIDTH_EPSILON_PX = 2;

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

/**
 * Estabiliza o conjunto colapsado: pode colapsar mais (ideal), mas só reexpande
 * quando há folga ≥ `expandHysteresisPx`. Evita React #185 por loop
 * colapsar ↔ medir ↔ expandir na fronteira de largura.
 */
export function stabilizeCollapsedRibbonGroupIds(
  groups: ReadonlyArray<RibbonGroupSize>,
  availableWidth: number,
  previousCollapsed: ReadonlySet<string>,
  gap = 8,
  expandHysteresisPx = RIBBON_COLLAPSE_EXPAND_HYSTERESIS_PX,
): Set<string> {
  const ideal = resolveCollapsedRibbonGroupIds(groups, availableWidth, gap);
  if (previousCollapsed.size === 0 || !(availableWidth > 0)) return ideal;

  const next = new Set(ideal);
  const slackLimit = availableWidth - Math.max(0, expandHysteresisPx);
  for (const id of previousCollapsed) {
    if (next.has(id)) continue;
    if (sumRibbonGroupsWidth(groups, next, gap) > slackLimit) {
      next.add(id);
    }
  }
  return next;
}

export function ribbonGroupWidthsNearlyEqual(
  a: number,
  b: number,
  epsilonPx = RIBBON_GROUP_WIDTH_EPSILON_PX,
): boolean {
  return Math.abs(a - b) <= Math.max(0, epsilonPx);
}
