import type { MenuAnchorRect } from "../components/shared/overlay/menuPositionUtils";

const MIRROR_STYLE_PROPERTIES = [
  "boxSizing",
  "overflowX",
  "overflowY",
  "borderTopWidth",
  "borderRightWidth",
  "borderBottomWidth",
  "borderLeftWidth",
  "borderStyle",
  "paddingTop",
  "paddingRight",
  "paddingBottom",
  "paddingLeft",
  "fontStyle",
  "fontVariant",
  "fontWeight",
  "fontStretch",
  "fontSize",
  "fontSizeAdjust",
  "lineHeight",
  "fontFamily",
  "textAlign",
  "textTransform",
  "textIndent",
  "textDecoration",
  "letterSpacing",
  "wordSpacing",
  "tabSize",
  "whiteSpace",
  "wordWrap",
  "wordBreak",
] as const;

function parsePixel(value: string): number {
  const parsed = Number.parseFloat(value);

  return Number.isFinite(parsed) ? parsed : 0;
}

/** Mede a posição do caret/@ no viewport a partir de um índice no textarea. */
export function measureTextareaCaretRect(
  textarea: HTMLTextAreaElement,
  caretIndex: number,
): MenuAnchorRect {
  const doc = textarea.ownerDocument;
  const win = doc.defaultView ?? window;
  const computed = win.getComputedStyle(textarea);
  const textareaRect = textarea.getBoundingClientRect();
  const mirror = doc.createElement("div");

  mirror.setAttribute("aria-hidden", "true");
  mirror.style.position = "fixed";
  mirror.style.top = `${textareaRect.top}px`;
  mirror.style.left = `${textareaRect.left}px`;
  mirror.style.width = `${textareaRect.width}px`;
  mirror.style.height = `${textareaRect.height}px`;
  mirror.style.visibility = "hidden";
  mirror.style.pointerEvents = "none";
  mirror.style.overflow = "hidden";
  mirror.style.zIndex = "-1";

  for (const property of MIRROR_STYLE_PROPERTIES) {
    mirror.style.setProperty(property, computed.getPropertyValue(property));
  }

  mirror.style.whiteSpace = "pre-wrap";
  mirror.style.wordWrap = "break-word";

  const safeIndex = Math.max(0, Math.min(caretIndex, textarea.value.length));
  const textBefore = textarea.value.slice(0, safeIndex);
  const textAfter = textarea.value.slice(safeIndex) || "\u200b";

  mirror.textContent = textBefore;

  const marker = doc.createElement("span");
  marker.textContent = textAfter;
  mirror.appendChild(marker);

  doc.body.appendChild(mirror);
  mirror.scrollTop = textarea.scrollTop;
  mirror.scrollLeft = textarea.scrollLeft;

  const markerRect = marker.getBoundingClientRect();
  const lineHeight = markerRect.height || parsePixel(computed.lineHeight) || 20;

  doc.body.removeChild(mirror);

  return {
    left: markerRect.left,
    top: markerRect.top,
    right: markerRect.left,
    bottom: markerRect.top + lineHeight,
    width: 0,
    height: lineHeight,
  };
}
