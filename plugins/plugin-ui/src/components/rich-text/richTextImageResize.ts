/** Resize selected `<img>` inside RichTextEditor via width/height attrs (BFF allowlist ≤4096). */

export const RICH_TEXT_IMAGE_MIN_WIDTH = 48;
/** Align with helpdesk-api / BFF img width allowlist. */
export const RICH_TEXT_IMAGE_MAX_WIDTH = 4096;
/**
 * @deprecated Paste uses natural size (capped at MAX). Kept for callers that pass defaultMaxWidth.
 */
export const RICH_TEXT_IMAGE_DEFAULT_MAX_WIDTH = RICH_TEXT_IMAGE_MAX_WIDTH;

export type RichTextImageSize = {
  width: number;
  height: number;
};

export function clampRichTextImageWidth(
  width: number,
  options?: { min?: number; max?: number; containerWidth?: number },
): number {
  const min = options?.min ?? RICH_TEXT_IMAGE_MIN_WIDTH;
  // Do not clamp to containerWidth: author may enlarge beyond the editor (scroll).
  const max = options?.max ?? RICH_TEXT_IMAGE_MAX_WIDTH;
  if (max < min) return min;
  return Math.max(min, Math.min(max, Math.round(width)));
}

export function resolveRichTextImageNaturalSize(img: HTMLImageElement): RichTextImageSize {
  const naturalW = img.naturalWidth || img.width || img.getBoundingClientRect().width || 320;
  const naturalH = img.naturalHeight || img.height || img.getBoundingClientRect().height || 240;
  return {
    width: Math.max(1, Math.round(naturalW)),
    height: Math.max(1, Math.round(naturalH)),
  };
}

/** Keep aspect ratio; persist via HTML width/height (not CSS — sanitizer strips width style). */
export function applyRichTextImageWidth(
  img: HTMLImageElement,
  nextWidth: number,
  options?: { min?: number; max?: number; containerWidth?: number },
): RichTextImageSize {
  const natural = resolveRichTextImageNaturalSize(img);
  const width = clampRichTextImageWidth(nextWidth, options);
  const height = Math.max(1, Math.round((width * natural.height) / natural.width));
  img.setAttribute("width", String(width));
  img.setAttribute("height", String(height));
  img.style.width = `${width}px`;
  img.style.height = `${height}px`;
  // Explicit size must win over stylesheet max-width:100% so enlarge is visible.
  img.style.maxWidth = "none";
  return { width, height };
}

/**
 * Stamp natural pixel size on insert (paste/attach) when no width attr yet.
 * Only caps at RICH_TEXT_IMAGE_MAX_WIDTH — does not shrink to the editor column.
 */
export function fitRichTextImageToContainer(
  img: HTMLImageElement,
  _containerWidth: number,
  options?: { defaultMaxWidth?: number; maxWidth?: number },
): RichTextImageSize | null {
  if (img.getAttribute("width")) return null;
  const natural = resolveRichTextImageNaturalSize(img);
  const max =
    options?.maxWidth ?? options?.defaultMaxWidth ?? RICH_TEXT_IMAGE_MAX_WIDTH;
  const target = Math.min(natural.width, Math.max(RICH_TEXT_IMAGE_MIN_WIDTH, max));
  return applyRichTextImageWidth(img, target, { max });
}

export function clearRichTextImageInlineSizeStyles(img: HTMLImageElement): void {
  img.style.removeProperty("width");
  img.style.removeProperty("height");
  img.style.removeProperty("max-width");
}

/** SE handle position relative to `root`, clamped to the visible image∩editor box. */
export function resolveRichTextImageResizeHandlePosition(args: {
  img: HTMLImageElement;
  root: HTMLElement;
  editor: HTMLElement;
  handleSize?: number;
}): { top: number; left: number; width: number; height: number } {
  const handleSize = args.handleSize ?? 12;
  const rootRect = args.root.getBoundingClientRect();
  const imgRect = args.img.getBoundingClientRect();
  const editorRect = args.editor.getBoundingClientRect();
  const visibleLeft = Math.max(imgRect.left, editorRect.left);
  const visibleTop = Math.max(imgRect.top, editorRect.top);
  const visibleRight = Math.min(imgRect.right, editorRect.right);
  const visibleBottom = Math.min(imgRect.bottom, editorRect.bottom);
  const width = Math.max(handleSize, visibleRight - visibleLeft);
  const height = Math.max(handleSize, visibleBottom - visibleTop);
  return {
    top: visibleBottom - rootRect.top - handleSize / 2,
    left: visibleRight - rootRect.left - handleSize / 2,
    width,
    height,
  };
}
