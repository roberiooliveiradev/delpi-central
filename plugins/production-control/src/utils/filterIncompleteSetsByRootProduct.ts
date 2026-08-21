import type { IncompleteOrderSetItem } from "../types";

/** Normaliza código/texto para comparação (maiúsculas, sem espaços laterais). */
export function normalizeRootProductQuery(query: string): string {
  return query.trim().toUpperCase();
}

/**
 * Casa produto raiz por código (prefixo ou trecho) ou descrição (trecho).
 * Query vazia = todos os itens.
 */
export function matchesRootProductQuery(
  item: Pick<IncompleteOrderSetItem, "root_code" | "root_description">,
  query: string,
): boolean {
  const needle = normalizeRootProductQuery(query);
  if (!needle) return true;
  const code = String(item.root_code ?? "")
    .trim()
    .toUpperCase();
  const description = String(item.root_description ?? "")
    .trim()
    .toUpperCase();
  return code.includes(needle) || description.includes(needle);
}

export function filterIncompleteSetsByRootProduct(
  items: readonly IncompleteOrderSetItem[],
  query: string,
): IncompleteOrderSetItem[] {
  const needle = normalizeRootProductQuery(query);
  if (!needle) return [...items];
  return items.filter((item) => matchesRootProductQuery(item, needle));
}
