/**
 * Posicionamento de balões KeyTip (atalhos Alt) — flip e clamp na viewport.
 */

export type ShortcutTipPlacement = "top" | "bottom";

export type ShortcutTipPositionInput = {
  anchor: { top: number; left: number; right: number; bottom: number; width: number; height: number };
  tipWidth: number;
  tipHeight: number;
  preferred: ShortcutTipPlacement;
  viewportWidth: number;
  viewportHeight: number;
  gap?: number;
  margin?: number;
};

export type ShortcutTipPosition = {
  top: number;
  left: number;
  placement: ShortcutTipPlacement;
};

/**
 * Centraliza o balão no âncora; se não couber no lado preferido, inverte;
 * clamp horizontal/vertical para permanecer na tela.
 */
export function resolveShortcutTipPosition(input: ShortcutTipPositionInput): ShortcutTipPosition {
  const gap = input.gap ?? 8;
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
  let left = centerX - tipWidth / 2;
  left = Math.min(Math.max(margin, left), Math.max(margin, viewportWidth - tipWidth - margin));

  let top =
    placement === "top" ? anchor.top - tipHeight - gap : anchor.bottom + gap;
  top = Math.min(
    Math.max(margin, top),
    Math.max(margin, viewportHeight - tipHeight - margin),
  );

  return { top, left, placement };
}
