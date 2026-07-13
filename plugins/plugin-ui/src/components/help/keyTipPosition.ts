/**
 * Posicionamento de KeyTips (atalhos Alt / letras F) — flip e clamp na viewport.
 */

export type KeyTipPlacement = "top" | "bottom";

export type KeyTipPositionInput = {
  anchor: {
    top: number;
    left: number;
    right: number;
    bottom: number;
    width: number;
    height: number;
  };
  tipWidth: number;
  tipHeight: number;
  preferred: KeyTipPlacement;
  viewportWidth: number;
  viewportHeight: number;
  gap?: number;
  margin?: number;
  /** Desloca o balão no eixo X (ex.: separar undo/redo adjacentes). */
  offsetX?: number;
};

export type KeyTipPosition = {
  top: number;
  left: number;
  placement: KeyTipPlacement;
};

/**
 * Centraliza o balão no âncora; se não couber no lado preferido, inverte;
 * clamp horizontal/vertical para permanecer na tela.
 */
export function resolveKeyTipPosition(input: KeyTipPositionInput): KeyTipPosition {
  /* Folga inclui a setinha do balão (~6px) além do respiro visual. */
  const gap = input.gap ?? 10;
  const margin = input.margin ?? 8;
  const { anchor, tipWidth, tipHeight, preferred, viewportWidth, viewportHeight } = input;

  const spaceAbove = anchor.top - margin;
  const spaceBelow = viewportHeight - anchor.bottom - margin;

  let placement = preferred;
  if (preferred === "top") {
    if (tipHeight + gap > spaceAbove && spaceBelow >= spaceAbove) {
      placement = "bottom";
    }
  } else if (tipHeight + gap > spaceBelow && spaceAbove > spaceBelow) {
    placement = "top";
  }

  const centerX = anchor.left + anchor.width / 2;
  let left = centerX - tipWidth / 2 + (input.offsetX ?? 0);
  left = Math.min(Math.max(margin, left), Math.max(margin, viewportWidth - tipWidth - margin));

  let top = placement === "top" ? anchor.top - tipHeight - gap : anchor.bottom + gap;
  top = Math.min(
    Math.max(margin, top),
    Math.max(margin, viewportHeight - tipHeight - margin),
  );

  return { top, left, placement };
}
