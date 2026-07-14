import {
  isComunicadoVisualBoxBlock,
  resolveShapePrimitive,
  resolveVisualBoxProfile,
  shapeAdjustmentSpecs,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

/**
 * Capacidades da faixa Elemento para caixa visual (texto / título / forma).
 * Um único perfil controla o que exibir — ordem fixa: tipografia → Forma → rabo.
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

  const profile = resolveVisualBoxProfile(block);
  const isTextMode = profile.mode === "text";
  const isShapeMode = profile.mode === "shape";
  const primitive =
    isShapeMode && block.type === "shape"
      ? resolveShapePrimitive(block.shape)
      : undefined;
  const shapeAdjustments =
    isShapeMode &&
    block.type === "shape" &&
    shapeAdjustmentSpecs(block.shape).some(
      (spec) => spec.id !== "corner" && spec.id !== "round",
    );

  return {
    /* Tipografia — mesmas opções; ocultar só o que o modelo não sustenta. */
    textHighlight: true,
    clearFormatting: true,
    paragraphJustify: true,
    paragraphLists: isTextMode,
    paragraphNamedStyle: isTextMode,
    paragraphSpacing: true,
    /* Forma — chrome comum; galeria/ajustes só em shape. */
    shapeGallery: isShapeMode,
    shapeChrome: true,
    shapeAdjustments: Boolean(shapeAdjustments),
    shapeMarker: isShapeMode && primitive === "point",
  };
}

/** Capacidades vazias (não-visual-box). */
export function emptyVisualBoxElementCapabilities(): VisualBoxElementCapabilities {
  return { ...HIDDEN };
}
