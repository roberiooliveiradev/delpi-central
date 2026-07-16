/**
 * Política de clique em partes de widgets compostos (KPI / chart / table / input).
 *
 * Excel-like: com o bloco já selecionado, clique em parte de conteúdo (série, métrica…)
 * seleciona a parte sem arrastar o bloco. Arraste do bloco fica no chrome/moldura.
 */

export type CompositePartPointerAction = "drag-block" | "part-move" | "select-part";

/**
 * - Bloco ainda não selecionado → arrastar o bloco (1º clique).
 * - Conteúdo + bloco selecionado → selecionar a parte (sem drag).
 * - Mesma parte já selecionada e móvel → arrastar a parte.
 * - Moldura / fundo → arrastar o bloco.
 */
export function resolveCompositePartPointerAction(params: {
  blockSelected: boolean;
  samePartSelected: boolean;
  partAllowsMove: boolean;
  /** Parte de conteúdo (série, marcador, título, métrica…) vs moldura/fundo. */
  contentPart?: boolean;
}): CompositePartPointerAction {
  if (params.blockSelected && params.samePartSelected && params.partAllowsMove) {
    return "part-move";
  }
  if (params.blockSelected && params.contentPart) {
    return "select-part";
  }
  return "drag-block";
}

/**
 * Moldura (= fundo do widget) não pinta chrome próprio — outline/handles ficam no wrap.
 * KPI `card` mantém chrome no host (já alinhavel ao shell); filtro/gráfico/tabela usam wrap.
 */
export function isMolduraPartSelection(
  blockType: string | undefined,
  part: { kind: string } | null | undefined,
): boolean {
  if (!part || !blockType) return false;
  if (blockType === "input" && part.kind === "frame") return true;
  if (blockType === "chart_view" && part.kind === "chartArea") return true;
  if (blockType === "table_view" && part.kind === "frame") return true;
  return false;
}

/** Parte de conteúdo (não moldura) → chrome da parte no lugar do wrap. */
export function shouldUsePartChromeInsteadOfBlock(
  blockType: string | undefined,
  part: { kind: string } | null | undefined,
): boolean {
  return Boolean(part) && !isMolduraPartSelection(blockType, part);
}

/** Clique deve selecionar a parte sem iniciar drag do bloco. */
export function isCompositeContentPart(
  blockType: string | undefined,
  part: { kind: string } | null | undefined,
): boolean {
  return shouldUsePartChromeInsteadOfBlock(blockType, part);
}
