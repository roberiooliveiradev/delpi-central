export type MenuAnchorRect = Pick<
  DOMRect,
  "left" | "top" | "right" | "bottom" | "width" | "height"
>;

const MENU_WIDTH = 240;
const MENU_ITEM_HEIGHT = 36;
const MENU_PADDING = 16;
const VIEWPORT_MARGIN = 8;
const ANCHOR_GAP = 6;
/** Legado `.mdc-chat-input__menu { bottom: calc(100% + 0.55rem) }` */
export const COMPOSER_PANEL_ANCHOR_GAP = 9;

export const COMPOSER_OPTION_MENU_WIDTH = 260;
export const COMPOSER_PANEL_MENU_WIDTH = 352;
export const ACTION_MENU_WIDTH = 224;
const COMPOSER_OPTION_ITEM_HEIGHT = 58;
const COMPOSER_PANEL_ITEM_HEIGHT = 44;
const COMPOSER_OPTION_MENU_PADDING = 12;
const COMPOSER_PANEL_MENU_PADDING = 16;
const COMPOSER_OPTION_MENU_MIN_HEIGHT = 8.5 * 16;
const COMPOSER_PANEL_MENU_MIN_HEIGHT = 10 * 16;
const COMPOSER_PANEL_MENU_MAX_HEIGHT = 28 * 16;
const COMPOSER_PANEL_SECTION_OVERHEAD = 88;

export function estimateMenuHeight(itemCount: number): number {
  return Math.max(itemCount, 1) * MENU_ITEM_HEIGHT + MENU_PADDING;
}

export function estimateComposerOptionMenuHeight(itemCount: number): number {
  return Math.max(itemCount, 1) * COMPOSER_OPTION_ITEM_HEIGHT + COMPOSER_OPTION_MENU_PADDING;
}

export function estimateComposerPanelMenuHeight(itemCount: number): number {
  const natural =
    Math.max(itemCount, 1) * COMPOSER_PANEL_ITEM_HEIGHT +
    COMPOSER_PANEL_MENU_PADDING +
    COMPOSER_PANEL_SECTION_OVERHEAD;

  return Math.min(COMPOSER_PANEL_MENU_MAX_HEIGHT, natural);
}

/** Linhas estimadas do menu 「+」 (anexo, agentes, projetos, cabeçalhos). */
export function estimateChatInputPlusMenuItemCount(options: {
  agentCount: number;
  projectCount: number;
}): number {
  const projectRows = Math.min(options.projectCount, 8);

  return 1 + options.agentCount + projectRows + 3;
}

export type ComposerOptionMenuLayout = {
  left: number;
  top: number;
  maxHeight: number;
  /** Quando true, `top` ancora a borda inferior do painel (transform translateY(-100%)). */
  anchorAbove?: boolean;
};

type ViewportBounds = {
  width: number;
  height: number;
};

function readViewportBounds(viewport?: ViewportBounds): ViewportBounds {
  if (viewport) {
    return viewport;
  }

  if (typeof window === "undefined") {
    return { width: 1280, height: 800 };
  }

  return {
    width: window.innerWidth,
    height: window.innerHeight,
  };
}

export function toContainerRelativeRect(
  rect: MenuAnchorRect,
  containerRect: MenuAnchorRect,
): MenuAnchorRect {
  return {
    left: rect.left - containerRect.left,
    top: rect.top - containerRect.top,
    right: rect.right - containerRect.left,
    bottom: rect.bottom - containerRect.top,
    width: rect.width,
    height: rect.height,
  };
}

type ContainedLayoutOptions = {
  contained?: boolean;
  containerRect?: MenuAnchorRect;
};

function resolveContainedComposerLayout(
  rect: MenuAnchorRect,
  options: ContainedLayoutOptions,
): { rect: MenuAnchorRect; viewport?: ViewportBounds } {
  if (!options.contained || !options.containerRect) {
    return { rect };
  }

  return {
    rect: toContainerRelativeRect(rect, options.containerRect),
    viewport: {
      width: options.containerRect.width,
      height: options.containerRect.height,
    },
  };
}

type ComposerPopoverLayoutOptions = {
  rect: MenuAnchorRect;
  itemCount: number;
  menuWidth: number;
  naturalHeight: number;
  minHeight: number;
  viewport?: ViewportBounds;
  anchorGap?: number;
  /** `start` = borda esquerda do menu no gatilho (menu 「+」); default flip horizontal. */
  horizontalAlign?: "start" | "flip";
};

function resolveComposerPopoverLayout(
  options: ComposerPopoverLayoutOptions,
): ComposerOptionMenuLayout {
  const margin = VIEWPORT_MARGIN;
  const gap = options.anchorGap ?? ANCHOR_GAP;
  const { left, top, right, bottom } = options.rect;
  const viewport = readViewportBounds(options.viewport);
  const menuWidth = options.menuWidth;
  const naturalHeight = options.naturalHeight;

  const spaceAbove = top - margin;
  const spaceBelow = viewport.height - bottom - margin;
  const openAbove = spaceAbove >= spaceBelow || spaceBelow < naturalHeight * 0.45;

  let menuLeft = left;

  if (options.horizontalAlign === "start") {
    if (menuLeft + menuWidth > viewport.width - margin) {
      menuLeft = Math.max(margin, viewport.width - margin - menuWidth);
    }
  } else if (menuLeft + menuWidth > viewport.width - margin) {
    menuLeft = Math.max(margin, right - menuWidth);
  }

  if (menuLeft < margin) {
    menuLeft = margin;
  }

  if (openAbove) {
    let maxHeight = Math.min(naturalHeight, Math.max(0, spaceAbove - gap));
    maxHeight = Math.max(maxHeight, Math.min(naturalHeight, options.minHeight));

    if (maxHeight > spaceAbove - gap) {
      maxHeight = Math.max(0, spaceAbove - gap);
    }

    let menuTop = top - gap;

    if (menuTop - maxHeight < margin) {
      maxHeight = Math.max(0, menuTop - margin);
    }

    return { left: menuLeft, top: menuTop, maxHeight, anchorAbove: true };
  }

  let maxHeight = Math.min(naturalHeight, Math.max(0, spaceBelow - gap));
  maxHeight = Math.max(maxHeight, Math.min(naturalHeight, options.minHeight));

  let menuTop = bottom + gap;

  if (menuTop < margin) {
    menuTop = margin;
    maxHeight = Math.min(naturalHeight, viewport.height - margin * 2);
  }

  if (menuTop + maxHeight > viewport.height - margin) {
    maxHeight = Math.max(0, viewport.height - margin - menuTop);
  }

  return { left: menuLeft, top: menuTop, maxHeight, anchorAbove: false };
}

/** Menu do composer (formato/modo) — flip vertical, altura limitada ao espaço visível. */
export function resolveComposerOptionMenuPosition(options: {
  rect: MenuAnchorRect;
  itemCount: number;
  menuWidth?: number;
  viewport?: ViewportBounds;
  contained?: boolean;
  containerRect?: MenuAnchorRect;
}): ComposerOptionMenuLayout {
  const menuWidth = options.menuWidth ?? COMPOSER_OPTION_MENU_WIDTH;
  const naturalHeight = estimateComposerOptionMenuHeight(options.itemCount);
  const { rect, viewport } = resolveContainedComposerLayout(options.rect, options);

  return resolveComposerPopoverLayout({
    rect,
    itemCount: options.itemCount,
    menuWidth,
    naturalHeight,
    minHeight: COMPOSER_OPTION_MENU_MIN_HEIGHT,
    viewport: viewport ?? options.viewport,
  });
}

/** Menu 「+」 do composer — painel largo com scroll. */
export function resolveComposerPanelMenuPosition(options: {
  rect: MenuAnchorRect;
  itemCount: number;
  menuWidth?: number;
  viewport?: ViewportBounds;
  contained?: boolean;
  containerRect?: MenuAnchorRect;
}): ComposerOptionMenuLayout {
  const menuWidth = options.menuWidth ?? COMPOSER_PANEL_MENU_WIDTH;
  const naturalHeight = estimateComposerPanelMenuHeight(options.itemCount);
  const { rect, viewport } = resolveContainedComposerLayout(options.rect, options);

  return resolveComposerPopoverLayout({
    rect,
    itemCount: options.itemCount,
    menuWidth,
    naturalHeight,
    minHeight: COMPOSER_PANEL_MENU_MIN_HEIGHT,
    viewport: viewport ?? options.viewport,
    anchorGap: COMPOSER_PANEL_ANCHOR_GAP,
    horizontalAlign: "start",
  });
}

export type ActionMenuLayout = {
  left: number;
  top: number;
};

export type ContextMenuAnchor =
  | { point: { x: number; y: number } }
  | { rect: MenuAnchorRect };

export type ContextMenuLayout = {
  left: number;
  top: number;
};

/** Menu de contexto (tabela, gráfico, chips) — âncora por rect ou ponto. */
export function resolveContextMenuPosition(options: {
  anchor: ContextMenuAnchor;
  itemCount: number;
  menuWidth?: number;
  contained: boolean;
  containerRect?: MenuAnchorRect;
}): ContextMenuLayout {
  const menuWidth = options.menuWidth ?? MENU_WIDTH;

  if ("rect" in options.anchor) {
    if (options.contained && options.containerRect) {
      return resolveMenuPositionInContainer({
        rect: options.anchor.rect,
        containerRect: options.containerRect,
        itemCount: options.itemCount,
        menuWidth,
      });
    }

    return resolveMenuPosition({
      rect: options.anchor.rect,
      itemCount: options.itemCount,
      menuWidth,
    });
  }

  if (options.contained && options.containerRect) {
    return resolveMenuPositionFromPointInContainer(
      options.anchor.point,
      options.containerRect,
      options.itemCount,
      menuWidth,
    );
  }

  return resolveMenuPositionFromPoint(
    options.anchor.point,
    options.itemCount,
    menuWidth,
  );
}

/** Menu de ações (sidebar, cards) — abre à direita do gatilho com flip horizontal. */
export function resolveActionMenuPosition(options: {
  rect: MenuAnchorRect;
  itemCount: number;
  menuWidth?: number;
  viewport?: ViewportBounds;
  contained?: boolean;
  containerRect?: MenuAnchorRect;
}): ActionMenuLayout {
  const menuWidth = options.menuWidth ?? ACTION_MENU_WIDTH;
  const menuHeight = estimateMenuHeight(options.itemCount);
  const margin = VIEWPORT_MARGIN;
  const gap = ANCHOR_GAP;
  const { rect, viewport: containedViewport } = resolveContainedComposerLayout(
    options.rect,
    options,
  );
  const { left, top, right } = rect;
  const viewport = readViewportBounds(containedViewport ?? options.viewport);

  const preferredLeft = right + gap;
  const fallbackLeft = left - menuWidth - gap;

  const menuLeft =
    preferredLeft + menuWidth <= viewport.width - margin
      ? preferredLeft
      : Math.max(margin, fallbackLeft);

  const maxTop = viewport.height - menuHeight - margin;
  const menuTop = Math.max(margin, Math.min(top, maxTop));

  return { left: menuLeft, top: menuTop };
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
