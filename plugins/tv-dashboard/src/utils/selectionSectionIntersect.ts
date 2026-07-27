import type { SelectionSectionId } from "../components/selectionSections/types";

/** Valor único ou «misto» (padrão Figma / Office em multi-seleção). */
export type AggregatedValue<T> = T | "mixed";

/**
 * Agrega valores iguais → T; divergentes → «mixed».
 * Lista vazia → undefined.
 */
export function aggregateEqualValues<T>(values: readonly T[]): AggregatedValue<T> | undefined {
  if (values.length === 0) return undefined;
  const first = values[0];
  for (let i = 1; i < values.length; i += 1) {
    if (!Object.is(values[i], first)) return "mixed";
  }
  return first;
}

/**
 * Interseção ordenada: preserva a ordem da lista primária (primeiro argumento).
 */
export function intersectOrderedIds<T extends string>(lists: readonly (readonly T[])[]): T[] {
  if (lists.length === 0) return [];
  const [primary, ...rest] = lists;
  if (!primary) return [];
  if (rest.length === 0) return [...primary];
  return primary.filter((id) => rest.every((list) => list.includes(id)));
}

export function filterMultiExcludedSections(
  sections: readonly SelectionSectionId[],
  excluded: ReadonlySet<SelectionSectionId>,
): SelectionSectionId[] {
  return sections.filter((id) => !excluded.has(id));
}
