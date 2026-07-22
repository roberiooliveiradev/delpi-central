/**
 * Resolve quais abas da faixa de tabs vão para o menu «Mais…» (direita → esquerda).
 * Diferente do colapso de grupos: tabs ocultas não viram botão individual — entram num overflow único.
 */

export type RibbonTabSize = {
  id: string;
  width: number;
  /** Ordem visual (0 = esquerda). */
  order: number;
};

export type ResolveOverflowRibbonTabIdsOptions = {
  /** Largura reservada do botão «Mais» quando houver overflow. */
  overflowControlWidth?: number;
  /** Aba ativa deve permanecer visível (promovida se cairia no overflow). */
  activeId?: string | null;
  gap?: number;
};

function sumVisibleWidth(
  tabs: ReadonlyArray<RibbonTabSize>,
  overflowIds: ReadonlySet<string>,
  gap: number,
  overflowControlWidth: number,
): number {
  const visible = tabs.filter((tab) => !overflowIds.has(tab.id));
  if (visible.length === 0 && overflowIds.size === 0) return 0;
  let sum = 0;
  for (const tab of visible) {
    sum += Math.max(0, tab.width);
  }
  const gaps = Math.max(0, visible.length - 1);
  sum += gap * gaps;
  if (overflowIds.size > 0) {
    if (visible.length > 0) sum += gap;
    sum += Math.max(0, overflowControlWidth);
  }
  return sum;
}

/**
 * Esconde abas da direita até caber em `availableWidth`.
 * Se `activeId` estivesse no overflow, promove e empurra outra aba (direita → esquerda).
 */
export function resolveOverflowRibbonTabIds(
  tabs: ReadonlyArray<RibbonTabSize>,
  availableWidth: number,
  options: ResolveOverflowRibbonTabIdsOptions = {},
): Set<string> {
  const {
    overflowControlWidth = 40,
    activeId = null,
    gap = 0,
  } = options;

  const overflow = new Set<string>();
  if (!(availableWidth > 0) || tabs.length === 0) return overflow;

  const ordered = [...tabs]
    .map((tab) => ({
      ...tab,
      width: Math.max(0, tab.width),
    }))
    .sort((a, b) => a.order - b.order);

  while (
    ordered.length > 0 &&
    sumVisibleWidth(ordered, overflow, gap, overflowControlWidth) > availableWidth
  ) {
    let candidate: RibbonTabSize | null = null;
    for (let i = ordered.length - 1; i >= 0; i -= 1) {
      const tab = ordered[i]!;
      if (!overflow.has(tab.id)) {
        candidate = tab;
        break;
      }
    }
    if (!candidate) break;
    /* Última aba visível: para (não esconder todas). */
    if (overflow.size >= ordered.length - 1) break;
    overflow.add(candidate.id);
  }

  if (activeId && overflow.has(activeId)) {
    overflow.delete(activeId);
    while (
      sumVisibleWidth(ordered, overflow, gap, overflowControlWidth) > availableWidth &&
      overflow.size < ordered.length - 1
    ) {
      let candidate: RibbonTabSize | null = null;
      for (let i = ordered.length - 1; i >= 0; i -= 1) {
        const tab = ordered[i]!;
        if (tab.id === activeId) continue;
        if (!overflow.has(tab.id)) {
          candidate = tab;
          break;
        }
      }
      if (!candidate) break;
      overflow.add(candidate.id);
    }
    /* Se ainda não cabe com a ativa, mantém a ativa e aceita overflow residual no host. */
  }

  return overflow;
}
