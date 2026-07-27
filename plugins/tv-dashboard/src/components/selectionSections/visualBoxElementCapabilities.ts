import {
  isComunicadoVisualBoxBlock,
  resolveShapePrimitive,
  resolveVisualBoxShapeKind,
  shapeAdjustmentSpecs,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

/**
 * Capacidades da faixa Elemento para caixa visual (texto / título / forma).
 * Texto = forma sem fundo por padrão — mesmas opções (tipografia + Forma + Alterar forma).
 */
export type VisualBoxElementCapabilities = {
  textHighlight: boolean;
  clearFormatting: boolean;
  paragraphJustify: boolean;
  paragraphLists: boolean;
  paragraphNamedStyle: boolean;
  /** Entrelinhas / espaçamento (popover Estilo). */
  paragraphSpacing: boolean;
  /** Tile «Alterar forma» dentro do grupo Forma. */
  shapeGallery: boolean;
  shapeChrome: boolean;
  shapeAdjustments: boolean;
  shapeMarker: boolean;
};

const HIDDEN: VisualBoxElementCapabilities = {
  textHighlight: false,
  clearFormatting: false,
  paragraphJustify: false,
  paragraphLists: false,
  paragraphNamedStyle: false,
  paragraphSpacing: false,
  shapeGallery: false,
  shapeChrome: false,
  shapeAdjustments: false,
  shapeMarker: false,
};

const CAP_KEYS = Object.keys(HIDDEN) as Array<keyof VisualBoxElementCapabilities>;

export function resolveVisualBoxElementCapabilities(
  block: ComunicadoBlock | null | undefined,
): VisualBoxElementCapabilities | null {
  if (!block || !isComunicadoVisualBoxBlock(block)) return null;

  const shapeKind = resolveVisualBoxShapeKind(block);
  const primitive = resolveShapePrimitive(shapeKind);
  const shapeAdjustments = shapeAdjustmentSpecs(shapeKind).some(
    (spec) => spec.id !== "corner" && spec.id !== "round",
  );

  return {
    textHighlight: true,
    clearFormatting: true,
    paragraphJustify: true,
    paragraphLists: true,
    paragraphNamedStyle: true,
    paragraphSpacing: true,
    shapeGallery: true,
    shapeChrome: true,
    shapeAdjustments,
    shapeMarker: primitive === "point",
  };
}

/**
 * AND booleano das capacidades de todos os blocos.
 * Retorna null se algum não for visual-box (seleção heterogênea).
 */
export function resolveVisualBoxElementCapabilitiesForSelection(
  blocks: readonly ComunicadoBlock[],
): VisualBoxElementCapabilities | null {
  if (blocks.length === 0) return null;
  const perBlock = blocks.map((block) => resolveVisualBoxElementCapabilities(block));
  if (perBlock.some((caps) => caps == null)) return null;
  const list = perBlock as VisualBoxElementCapabilities[];
  const out = { ...list[0]! };
  for (let i = 1; i < list.length; i += 1) {
    const caps = list[i]!;
    for (const key of CAP_KEYS) {
      out[key] = Boolean(out[key] && caps[key]);
    }
  }
  return out;
}

/** Capacidades vazias (não-visual-box). */
export function emptyVisualBoxElementCapabilities(): VisualBoxElementCapabilities {
  return { ...HIDDEN };
}
