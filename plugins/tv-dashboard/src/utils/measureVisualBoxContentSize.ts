import {
  TEXT_BOX_HUG_INSET_PX,
  TEXT_BOX_HUG_MIN_HEIGHT_PX,
  TEXT_BOX_HUG_MIN_WIDTH_PX,
  type VisualBoxHugAxes,
} from "@delpi/tv-dashboard-presentation";

/**
 * Mede o tamanho intrínseco do texto interno da caixa visual (px de layout).
 * Usado no hug por duplo clique no handle (paridade Figma / autofit de coluna).
 */
export function measureVisualBoxContentSizePx(
  blockRoot: HTMLElement,
  options?: {
    axes?: VisualBoxHugAxes;
    /** Largura atual do bloco (px) — hug só de altura respeita wrap. */
    currentWidthPx?: number;
  },
): { w: number; h: number } | null {
  const content =
    blockRoot.querySelector<HTMLElement>(
      ".tdp-comunicado__visual-box-content, .delpi-ui-comunicado__visual-box-content",
    ) ??
    blockRoot.querySelector<HTMLElement>(".td-composer__inline-text");
  if (!content) return null;

  const textEl =
    content.querySelector<HTMLElement>(
      ".td-composer__inline-text, h1, p, span, [contenteditable]",
    ) ?? content;

  const axes = options?.axes ?? { width: true, height: true };
  const pad = TEXT_BOX_HUG_INSET_PX * 2;
  const prev = {
    width: textEl.style.width,
    height: textEl.style.height,
    whiteSpace: textEl.style.whiteSpace,
    maxWidth: textEl.style.maxWidth,
  };

  try {
    if (axes.width && !axes.height) {
      textEl.style.whiteSpace = "nowrap";
      textEl.style.width = "max-content";
      textEl.style.height = "auto";
      textEl.style.maxWidth = "none";
    } else if (!axes.width && axes.height) {
      const wrapW = Math.max(
        TEXT_BOX_HUG_MIN_WIDTH_PX,
        (options?.currentWidthPx ?? blockRoot.offsetWidth) - pad,
      );
      textEl.style.whiteSpace = "pre-wrap";
      textEl.style.width = `${wrapW}px`;
      textEl.style.height = "auto";
      textEl.style.maxWidth = "none";
    } else {
      textEl.style.whiteSpace = "nowrap";
      textEl.style.width = "max-content";
      textEl.style.height = "auto";
      textEl.style.maxWidth = "none";
    }

    const measuredW = Math.ceil(textEl.scrollWidth);
    const measuredH = Math.ceil(textEl.scrollHeight);
    if (measuredW <= 0 && measuredH <= 0) return null;

    return {
      w: Math.max(TEXT_BOX_HUG_MIN_WIDTH_PX, measuredW + pad),
      h: Math.max(TEXT_BOX_HUG_MIN_HEIGHT_PX, measuredH + pad),
    };
  } finally {
    textEl.style.width = prev.width;
    textEl.style.height = prev.height;
    textEl.style.whiteSpace = prev.whiteSpace;
    textEl.style.maxWidth = prev.maxWidth;
  }
}

export function visualBoxBlockHasHugableText(block: {
  content?: string;
  contentRuns?: unknown[] | null;
}): boolean {
  if (block.contentRuns && block.contentRuns.length > 0) {
    return true;
  }
  return Boolean(block.content?.trim());
}
