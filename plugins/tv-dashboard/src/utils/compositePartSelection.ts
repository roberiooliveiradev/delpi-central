/**
 * Política de clique em partes de widgets compostos (KPI / chart / table / input).
 * Seleção de parte = duplo clique; clique simples move o bloco (ou a parte já ativa).
 */

export type CompositePartPointerAction = "drag-block" | "part-move";

/**
 * - Bloco ainda não selecionado / modo global / outra parte → arrastar o bloco (destravar).
 * - Mesma parte já selecionada e móvel → arrastar a parte.
 */
export function resolveCompositePartPointerAction(params: {
  blockSelected: boolean;
  samePartSelected: boolean;
  partAllowsMove: boolean;
}): CompositePartPointerAction {
  if (params.blockSelected && params.samePartSelected && params.partAllowsMove) {
    return "part-move";
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
