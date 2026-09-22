import type { ProblemDetectorItem } from "../types";

/** Normaliza código/texto para comparação (maiúsculas, sem espaços laterais). */
export function normalizeRootProductQuery(query: string): string {
  return query.trim().toUpperCase();
}

function matchesFinishedProducts(
  item: ProblemDetectorItem,
  needle: string,
): boolean {
  if (!("finished_products" in item) || !Array.isArray(item.finished_products)) {
    return false;
  }
  return item.finished_products.some((entry) => {
    const code = String(entry.product_code ?? "")
      .trim()
      .toUpperCase();
    const description = String(entry.description ?? "")
      .trim()
      .toUpperCase();
    return code.includes(needle) || description.includes(needle);
  });
}

/**
 * Casa produto raiz por código (prefixo ou trecho) ou descrição (trecho).
 * Query vazia = todos os itens.
 */
export function matchesRootProductQuery(
  item: Pick<ProblemDetectorItem, "root_code" | "root_description"> & ProblemDetectorItem,
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
  if (code.includes(needle) || description.includes(needle)) {
    return true;
  }
  return matchesFinishedProducts(item, needle);
}

export function filterIncompleteSetsByRootProduct<T extends ProblemDetectorItem>(
  items: readonly T[],
  query: string,
): T[] {
  const needle = normalizeRootProductQuery(query);
  if (!needle) return [...items];
  return items.filter((item) => matchesRootProductQuery(item, needle));
}
