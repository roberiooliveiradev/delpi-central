/**
 * Política de clique em partes de widgets compostos (KPI / chart / table / input).
 *
 * Palco = mesmo modo de formas/textos: clique seleciona e arrasta o **bloco**.
 * Parte interna entra via toolbar / duplo clique; só então arrasta a parte se móvel.
 * Chrome de outline/handles no wrap permanece no bloco (não some ao focar uma parte).
 */

export type CompositePartPointerAction = "drag-block" | "part-move" | "select-part";

/**
 * - Parte já selecionada e móvel → arrastar a parte.
 * - Demais cliques no palco → arrastar/selecionar o bloco (como componente comum).
 */
export function resolveCompositePartPointerAction(params: {
  blockSelected: boolean;
  samePartSelected: boolean;
  partAllowsMove: boolean;
  /** Mantido por compatibilidade — não força mais select-part no clique simples. */
  contentPart?: boolean;
}): CompositePartPointerAction {
  if (params.blockSelected && params.samePartSelected && params.partAllowsMove) {
    return "part-move";
  }
  return "drag-block";
}

/**
 * Moldura (= fundo do widget) — clique trata como o bloco.
 * Inclui KPI `card` (paridade com filtro/gráfico/tabela).
 */
export function isMolduraPartSelection(
  blockType: string | undefined,
  part: { kind: string } | null | undefined,
): boolean {
  if (!part || !blockType) return false;
  if (blockType === "kpi_view" && part.kind === "card") return true;
  if (blockType === "input" && part.kind === "frame") return true;
  if (blockType === "chart_view" && part.kind === "chartArea") return true;
  if (blockType === "table_view" && part.kind === "frame") return true;
  return false;
}

/**
 * Chrome de palco: sempre no wrap do bloco (como formas).
 * A parte selecionada continua com outline/handles próprios no host interno;
 * o wrap não cede o outline global nem esconde os handles de resize do bloco.
 */
export function shouldUsePartChromeInsteadOfBlock(
  _blockType: string | undefined,
  _part: { kind: string } | null | undefined,
): boolean {
  return false;
}

/** Parte de conteúdo (não moldura) — ribbon / duplo clique / float toolbar. */
export function isCompositeContentPart(
  blockType: string | undefined,
  part: { kind: string } | null | undefined,
): boolean {
  return Boolean(part) && !isMolduraPartSelection(blockType, part);
}
