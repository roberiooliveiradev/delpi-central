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

/** Capacidades vazias (não-visual-box). */
export function emptyVisualBoxElementCapabilities(): VisualBoxElementCapabilities {
  return { ...HIDDEN };
}
