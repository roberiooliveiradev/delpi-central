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
export const COMPOSER_MENTION_MENU_MIN_WIDTH = 168;
export const COMPOSER_MENTION_MENU_MAX_WIDTH = 280;
export const ACTION_MENU_WIDTH = 224;
const COMPOSER_OPTION_ITEM_HEIGHT = 58;
const COMPOSER_PANEL_ITEM_HEIGHT = 44;
const COMPOSER_MENTION_ITEM_HEIGHT = 28;
const COMPOSER_OPTION_MENU_PADDING = 12;
const COMPOSER_PANEL_MENU_PADDING = 16;
const COMPOSER_MENTION_MENU_PADDING = 8;
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

export function estimateComposerMentionMenuHeight(itemCount: number): number {
  return (
    Math.max(itemCount, 1) * COMPOSER_MENTION_ITEM_HEIGHT + COMPOSER_MENTION_MENU_PADDING * 2
  );
}

export function resolveComposerMentionMenuWidth(options: {
  anchorLeft: number;
  viewport?: ViewportBounds;
  margin?: number;
}): number {
  const margin = options.margin ?? VIEWPORT_MARGIN;
  const viewport = readViewportBounds(options.viewport);
  const spaceToRight = viewport.width - margin - options.anchorLeft;
  const spaceInViewport = viewport.width - margin * 2;

  return Math.max(
    COMPOSER_MENTION_MENU_MIN_WIDTH,
    Math.min(COMPOSER_MENTION_MENU_MAX_WIDTH, spaceToRight, spaceInViewport),
  );
}

/** Menu @ do composer — ancora no caret com largura responsiva ao espaço visível. */
export function resolveComposerMentionMenuPosition(options: {
  rect: MenuAnchorRect;
  itemCount: number;
  menuWidth?: number;
  viewport?: ViewportBounds;
  contained?: boolean;
  containerRect?: MenuAnchorRect;
}): ComposerOptionMenuLayout {
  const { rect, viewport } = resolveContainedComposerLayout(options.rect, options);
  const resolvedViewport = viewport ?? options.viewport;
  const menuWidth =
    options.menuWidth ??
    resolveComposerMentionMenuWidth({ anchorLeft: rect.left, viewport: resolvedViewport });

  return resolveComposerPopoverLayout({
    rect,
    itemCount: options.itemCount,
    menuWidth,
    naturalHeight: estimateComposerMentionMenuHeight(options.itemCount),
    minHeight: COMPOSER_MENTION_ITEM_HEIGHT + COMPOSER_MENTION_MENU_PADDING,
    viewport: resolvedViewport,
    anchorGap: ANCHOR_GAP,
    horizontalAlign: "start",
  });
}

/** Linhas estimadas do menu 「+」 (anexo, agentes, projetos, cabeçalhos e hints). */
export function estimateChatInputPlusMenuItemCount(options: {
  agentCount: number;
  projectCount: number;
}): number {
  const projectRows = Math.max(Math.min(options.projectCount, 8), 1);
  const agentRows = Math.max(options.agentCount, 1);

  return 1 + agentRows + projectRows + 5;
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
    const maxHeight = Math.max(0, spaceAbove - gap);
    const menuTop = top - gap;

    return { left: menuLeft, top: menuTop, maxHeight, anchorAbove: true };
  }

  let maxHeight = Math.max(0, spaceBelow - gap);
  let menuTop = bottom + gap;

  if (menuTop < margin) {
    menuTop = margin;
    maxHeight = Math.max(0, viewport.height - margin * 2);
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
  maxHeight?: number;
  /** Ancora a borda inferior do painel em `top` (canto superior direito). */
  anchorAbove?: boolean;
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

export type ActionMenuHorizontalAlign = "start" | "end";
export type ActionMenuVerticalAlign = "auto" | "below" | "corner" | "beside";

function clampHorizontalPosition(
  menuLeft: number,
  menuWidth: number,
  viewport: ViewportBounds,
  margin: number,
): number {
  return Math.max(
    margin,
    Math.min(menuLeft, viewport.width - menuWidth - margin),
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
  horizontalAlign?: ActionMenuHorizontalAlign;
  /** Sidebar ⋯: `beside` abre à direita do gatilho, alinhado ao topo. */
  verticalAlign?: ActionMenuVerticalAlign;
}): ActionMenuLayout {
  const menuWidth = options.menuWidth ?? ACTION_MENU_WIDTH;
  const menuHeight = estimateMenuHeight(options.itemCount);
  const margin = VIEWPORT_MARGIN;
  const gap = ANCHOR_GAP;
  const verticalMode =
    options.verticalAlign === "corner" ? "auto" : options.verticalAlign;
  const { rect, viewport: containedViewport } = resolveContainedComposerLayout(
    options.rect,
    options,
  );
  const { left, top, right, bottom } = rect;
  const viewport = readViewportBounds(containedViewport ?? options.viewport);

  if (verticalMode === "beside") {
    const menuLeft = Math.max(margin, right + gap);
    let menuTop = Math.max(margin, top);

    if (menuTop + menuHeight > viewport.height - margin) {
      menuTop = Math.max(margin, viewport.height - menuHeight - margin);
    }

    const layout: ActionMenuLayout = { left: menuLeft, top: menuTop };

    if (menuTop + menuHeight > viewport.height - margin) {
      layout.maxHeight = Math.max(0, viewport.height - menuTop - margin);
    }

    return layout;
  }

  let menuLeft: number;

  if (options.horizontalAlign === "end") {
    menuLeft = right - menuWidth;

    if (menuLeft < margin) {
      menuLeft = margin;
    }

    if (menuLeft + menuWidth > viewport.width - margin) {
      menuLeft = Math.max(margin, viewport.width - menuWidth - margin);
    }
  } else {
    const preferredLeft = right + gap;
    const fallbackLeft = left - menuWidth - gap;
    const fitsRight =
      preferredLeft >= margin &&
      preferredLeft + menuWidth <= viewport.width - margin;

    menuLeft = fitsRight
      ? preferredLeft
      : clampHorizontalPosition(fallbackLeft, menuWidth, viewport, margin);
  }

  const maxTop = viewport.height - menuHeight - margin;
  let menuTop = bottom + gap;
  let maxHeight: number | undefined;
  let anchorAbove = false;

  if (verticalMode === "below") {
    menuTop = Math.max(menuTop, margin);

    if (menuTop + menuHeight > viewport.height - margin) {
      maxHeight = Math.max(0, viewport.height - menuTop - margin);
    }
  } else {
    const spaceBelow = viewport.height - bottom - margin;
    const spaceAbove = top - margin;
    const openBelow =
      spaceBelow >= menuHeight + gap || spaceBelow >= spaceAbove;

    if (openBelow) {
      menuTop = bottom + gap;

      if (menuTop + menuHeight > viewport.height - margin) {
        maxHeight = Math.max(0, viewport.height - menuTop - margin);
      }
    } else {
      menuTop = top - gap;
      anchorAbove = true;
      maxHeight = Math.max(0, spaceAbove - gap);
    }

    if (!anchorAbove) {
      if (menuTop < margin) {
        menuTop = margin;
      }

      menuTop = Math.min(menuTop, maxTop);
    }
  }

  const layout: ActionMenuLayout = { left: menuLeft, top: menuTop };

  if (maxHeight != null) {
    layout.maxHeight = maxHeight;
  }

  if (anchorAbove) {
    layout.anchorAbove = true;
  }

  return layout;
}

/** Gatilho fora do portal contido (#mdc-modal-root) — ex.: menu ⋯ na sidebar. */
export function isMenuAnchorOutsideContainer(
  rect: MenuAnchorRect,
  containerRect: MenuAnchorRect,
): boolean {
  const relative = toContainerRelativeRect(rect, containerRect);

  return (
    relative.right <= VIEWPORT_MARGIN ||
    relative.left >= containerRect.width - VIEWPORT_MARGIN ||
    relative.bottom <= VIEWPORT_MARGIN ||
    relative.top >= containerRect.height - VIEWPORT_MARGIN
  );
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
