/**
 * Mescla nova ordem dos favoritos visíveis na ordem completa persistida,
 * mantendo apps ocultos (não lançáveis) nas posições originais.
 */
export function mergeFavoriteOrder(
  allFavoriteIds: string[],
  visibleIds: string[],
  newVisibleOrder: string[],
): string[] {
  const visibleSet = new Set(visibleIds);
  const queue = [...newVisibleOrder];

  return allFavoriteIds.map((id) =>
    visibleSet.has(id) ? queue.shift()! : id,
  );
}

/**
 * Reordena uma lista movendo um item de `fromIndex` para `toIndex`.
 */
export function reorderList<T>(items: T[], fromIndex: number, toIndex: number): T[] {
  if (
    fromIndex === toIndex ||
    fromIndex < 0 ||
    toIndex < 0 ||
    fromIndex >= items.length ||
    toIndex >= items.length
  ) {
    return items;
  }

  const next = [...items];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  return next;
}
