import type { MenuAnchorRect } from "../components/shared/overlay/menuPositionUtils";

const MIRROR_STYLE_PROPERTIES = [
  "boxSizing",
  "width",
  "height",
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
  const mirror = doc.createElement("div");

  mirror.setAttribute("aria-hidden", "true");
  mirror.style.position = "absolute";
  mirror.style.top = "0";
  mirror.style.left = "-9999px";
  mirror.style.visibility = "hidden";
  mirror.style.pointerEvents = "none";
  mirror.style.overflow = "hidden";

  for (const property of MIRROR_STYLE_PROPERTIES) {
    mirror.style.setProperty(property, computed.getPropertyValue(property));
  }

  mirror.style.width = `${textarea.clientWidth}px`;

  const safeIndex = Math.max(0, Math.min(caretIndex, textarea.value.length));
  const textBefore = textarea.value.slice(0, safeIndex);
  const textAfter = textarea.value.slice(safeIndex) || ".";

  mirror.textContent = textBefore;

  const marker = doc.createElement("span");
  marker.textContent = textAfter;
  mirror.appendChild(marker);

  doc.body.appendChild(mirror);

  const markerTop = marker.offsetTop;
  const markerLeft = marker.offsetLeft;
  const lineHeight = marker.offsetHeight || parsePixel(computed.lineHeight) || 20;
  const textareaRect = textarea.getBoundingClientRect();
  const borderTop = parsePixel(computed.borderTopWidth);
  const borderLeft = parsePixel(computed.borderLeftWidth);
  const paddingTop = parsePixel(computed.paddingTop);
  const paddingLeft = parsePixel(computed.paddingLeft);

  doc.body.removeChild(mirror);

  const left =
    textareaRect.left + borderLeft + paddingLeft + markerLeft - textarea.scrollLeft;
  const top =
    textareaRect.top + borderTop + paddingTop + markerTop - textarea.scrollTop;

  return {
    left,
    top,
    right: left,
    bottom: top + lineHeight,
    width: 0,
    height: lineHeight,
  };
}
