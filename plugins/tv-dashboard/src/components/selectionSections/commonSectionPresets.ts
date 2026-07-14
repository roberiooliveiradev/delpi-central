import type { SelectionSectionId, SelectionSectionLayout } from "./types";

/**
 * Seções transversais Elemento — repetem em quase todo tipo.
 * Ribbon: Tamanho e posição → Organizar → Ações.
 * Pane: + animação (antes de ações).
 */
export const COMMON_RIBBON_TAIL = [
  "display",
  "organize",
  "actions",
] as const satisfies readonly SelectionSectionId[];

export const COMMON_PANE_TAIL = [
  "display",
  "organize",
  "animation",
  "actions",
] as const satisfies readonly SelectionSectionId[];

/** Tipografia + Forma (texto/heading — mesmo chrome que shape). */
export const COMMON_TYPOGRAPHY_PREFIX = [
  "typography",
  "shapeChrome",
] as const satisfies readonly SelectionSectionId[];

export function commonTailForLayout(
  layout: SelectionSectionLayout,
): readonly SelectionSectionId[] {
  return layout === "pane" ? COMMON_PANE_TAIL : COMMON_RIBBON_TAIL;
}

/**
 * Anexa o rabo transversal a uma lista de seções tipadas.
 * `light`: display+organize+actions (fontes de dados, parte sem animação).
 */
export function withCommonTail(
  head: SelectionSectionId[],
  mode: "full" | "light" = "full",
): SelectionSectionId[] {
  if (mode === "light") {
    return [...head, ...COMMON_RIBBON_TAIL];
  }
  return [...head, ...COMMON_PANE_TAIL];
}

/** Concatena prefixo tipado + rabo, sem duplicar IDs. */
export function appendSectionIds(
  ...groups: Array<readonly SelectionSectionId[] | SelectionSectionId[]>
): SelectionSectionId[] {
  const seen = new Set<SelectionSectionId>();
  const out: SelectionSectionId[] = [];
  for (const group of groups) {
    for (const id of group) {
      if (seen.has(id)) continue;
      seen.add(id);
      out.push(id);
    }
  }
  return out;
}
