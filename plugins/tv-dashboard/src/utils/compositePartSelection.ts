/**
 * Política de clique em partes de widgets compostos (KPI / chart / table / input).
 *
 * Complexo ≡ agrupado (`stageGroupedSelection.ts`):
 * - Clique simples no palco = unidade pai (arrasta o bloco).
 * - Parte de conteúdo = filho; chrome do pai desativa (`shouldUsePartChromeInsteadOfBlock`).
 * - Moldura (`card` / `frame` / …) permanece na unidade pai.
 */

export type CompositePartPointerAction = "drag-block" | "part-move" | "select-part";

/**
 * Widgets compostos no editor sempre expõem handlers de parte.
 * Clique simples → `resolveCompositePartPointerAction` → arrasta/seleciona o bloco;
 * parte só move quando já está selecionada (`part-move`).
 * Sem isso, hit-test em fatias/séries com stopPropagation engole o clique do wrap.
 */
export function shouldAttachCompositePartInteraction(_blockType?: string): boolean {
  return true;
}

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
 * Chrome de palco no wrap do bloco some quando um **filho** (parte de conteúdo)
 * está selecionado — paridade com membro isolado de grupo.
 * Moldura / sem parte → chrome permanece no pai.
 */
export function shouldUsePartChromeInsteadOfBlock(
  blockType: string | undefined,
  part: { kind: string } | null | undefined,
): boolean {
  return isCompositeContentPart(blockType, part);
}

/** Parte de conteúdo (não moldura) — ribbon / duplo clique / float toolbar. */
export function isCompositeContentPart(
  blockType: string | undefined,
  part: { kind: string } | null | undefined,
): boolean {
  return Boolean(part) && !isMolduraPartSelection(blockType, part);
}

/**
 * Alterna parte na multi-seleção de filhos (Shift), como blocos em grupo.
 * Moldura sempre substitui (volta à unidade pai).
 */
export function toggleCompositePartSelection<T extends { kind: string }>(params: {
  blockType: string;
  current: T[];
  next: T;
  equal: (a: T, b: T) => boolean;
  additive?: boolean;
}): T[] {
  const { blockType, current, next, equal, additive } = params;
  if (isMolduraPartSelection(blockType, next) || !additive) {
    return [next];
  }
  if (!isCompositeContentPart(blockType, next)) {
    return [next];
  }
  const contentOnly = current.filter((part) => isCompositeContentPart(blockType, part));
  const already = contentOnly.some((part) => equal(part, next));
  if (already) {
    const rest = contentOnly.filter((part) => !equal(part, next));
    return rest.length > 0 ? rest : [next];
  }
  return [...contentOnly, next];
}
