export type MenuAnchorRect = Pick<
  DOMRect,
  "left" | "top" | "right" | "bottom" | "width" | "height"
>;

const MENU_WIDTH = 240;
const MENU_ITEM_HEIGHT = 36;
const MENU_PADDING = 16;
const VIEWPORT_MARGIN = 8;
const ANCHOR_GAP = 6;

export function estimateMenuHeight(itemCount: number): number {
  return Math.max(itemCount, 1) * MENU_ITEM_HEIGHT + MENU_PADDING;
}

export function menuAnchorRectFromElement(element: HTMLElement): MenuAnchorRect {
  const rect = element.getBoundingClientRect();

  return {
    left: rect.left,
    top: rect.top,
    right: rect.right,
    bottom: rect.bottom,
    width: rect.width,
    height: rect.height,
  };
}

/** Posiciona o menu flutuante junto ao elemento âncora, com flip nas bordas da viewport. */
export function resolveMenuPosition(options: {
  rect: MenuAnchorRect;
  itemCount: number;
  menuWidth?: number;
}): { left: number; top: number } {
  const menuWidth = options.menuWidth ?? MENU_WIDTH;
  const menuHeight = estimateMenuHeight(options.itemCount);
  const { left, top, right, bottom } = options.rect;

  let menuLeft = left;
  let menuTop = bottom + ANCHOR_GAP;

  if (menuTop + menuHeight > window.innerHeight - VIEWPORT_MARGIN) {
    menuTop = top - menuHeight - ANCHOR_GAP;
  }

  if (menuTop < VIEWPORT_MARGIN) {
    menuTop = VIEWPORT_MARGIN;
  }

  if (menuLeft + menuWidth > window.innerWidth - VIEWPORT_MARGIN) {
    menuLeft = Math.max(VIEWPORT_MARGIN, right - menuWidth);
  }

  if (menuLeft < VIEWPORT_MARGIN) {
    menuLeft = VIEWPORT_MARGIN;
  }

  return { left: menuLeft, top: menuTop };
}

/** Posiciona menu dentro de um container (coordenadas relativas ao portal do chat). */
export function resolveMenuPositionInContainer(options: {
  rect: MenuAnchorRect;
  containerRect: MenuAnchorRect;
  itemCount: number;
  menuWidth?: number;
}): { left: number; top: number } {
  const menuWidth = options.menuWidth ?? MENU_WIDTH;
  const menuHeight = estimateMenuHeight(options.itemCount);
  const margin = VIEWPORT_MARGIN;

  const anchorLeft = options.rect.left - options.containerRect.left;
  const anchorTop = options.rect.top - options.containerRect.top;
  const anchorRight = options.rect.right - options.containerRect.left;
  const anchorBottom = options.rect.bottom - options.containerRect.top;

  const containerWidth = options.containerRect.width;
  const containerHeight = options.containerRect.height;

  let menuLeft = anchorLeft;
  let menuTop = anchorBottom + ANCHOR_GAP;

  if (menuTop + menuHeight > containerHeight - margin) {
    menuTop = anchorTop - menuHeight - ANCHOR_GAP;
  }

  if (menuTop < margin) {
    menuTop = margin;
  }

  if (menuLeft + menuWidth > containerWidth - margin) {
    menuLeft = Math.max(margin, anchorRight - menuWidth);
  }

  if (menuLeft < margin) {
    menuLeft = margin;
  }

  return { left: menuLeft, top: menuTop };
}

/** Fallback para âncora por ponto (ex.: clique em gráfico). */
export function resolveMenuPositionFromPoint(
  point: { x: number; y: number },
  itemCount: number,
  menuWidth = MENU_WIDTH,
): { left: number; top: number } {
  const menuHeight = estimateMenuHeight(itemCount);

  return {
    left: Math.min(
      Math.max(VIEWPORT_MARGIN, point.x),
      window.innerWidth - menuWidth - VIEWPORT_MARGIN,
    ),
    top: Math.min(
      Math.max(VIEWPORT_MARGIN, point.y),
      window.innerHeight - menuHeight - VIEWPORT_MARGIN,
    ),
  };
}

export function resolveMenuPositionFromPointInContainer(
  point: { x: number; y: number },
  containerRect: MenuAnchorRect,
  itemCount: number,
  menuWidth = MENU_WIDTH,
): { left: number; top: number } {
  const menuHeight = estimateMenuHeight(itemCount);
  const margin = VIEWPORT_MARGIN;
  const containerWidth = containerRect.width;
  const containerHeight = containerRect.height;

  const relativeX = point.x - containerRect.left;
  const relativeY = point.y - containerRect.top;

  return {
    left: Math.min(
      Math.max(margin, relativeX),
      containerWidth - menuWidth - margin,
    ),
    top: Math.min(
      Math.max(margin, relativeY),
      containerHeight - menuHeight - margin,
    ),
  };
}
