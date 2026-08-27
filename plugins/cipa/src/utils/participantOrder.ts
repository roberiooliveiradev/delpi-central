/** Move um item na lista; retorna a mesma referência se o índice alvo for inválido. */
export function moveArrayItemAt<T>(items: T[], index: number, delta: number): T[] {
  const target = index + delta;
  if (target < 0 || target >= items.length) return items;
  const next = [...items];
  [next[index], next[target]] = [next[target], next[index]];
  return next;
}

/** Participantes/signatários usam o índice da lista como ordem canônica. */
export function participantsWithSortOrder<T extends Record<string, unknown>>(
  participants: T[],
): Array<T & { sort_order: number }> {
  return participants.map((item, index) => ({
    ...item,
    sort_order: index,
  }));
}
