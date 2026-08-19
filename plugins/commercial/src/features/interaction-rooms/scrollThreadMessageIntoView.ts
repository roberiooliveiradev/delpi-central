export const PIN_HIGHLIGHT_MS = 1500;

function escapeAttrValue(value: string): string {
  if (typeof CSS !== "undefined" && typeof CSS.escape === "function") {
    return CSS.escape(value);
  }
  return value.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

export function pinTitleFromMessageBody(
  body: string | null | undefined,
  fallback: string,
): string {
  const text = (body ?? "").replace(/\s+/g, " ").trim();
  if (!text) return fallback;
  return text.length > 80 ? `${text.slice(0, 77)}…` : text;
}

function isHighlightableElement(value: unknown): value is HTMLElement {
  if (!value || typeof value !== "object") return false;
  const el = value as {
    scrollIntoView?: unknown;
    classList?: { add?: unknown; remove?: unknown };
  };
  return (
    typeof el.scrollIntoView === "function" &&
    typeof el.classList?.add === "function" &&
    typeof el.classList?.remove === "function"
  );
}

/** Scroll + highlight do item do thread (kit `data-message-id`). */
export function scrollThreadMessageIntoView(
  root: ParentNode | null | undefined,
  messageId: string,
  highlightMs = PIN_HIGHLIGHT_MS,
): HTMLElement | null {
  const id = messageId.trim();
  if (!root || !id) return null;
  const el = root.querySelector(`[data-message-id="${escapeAttrValue(id)}"]`);
  if (!isHighlightableElement(el)) return null;
  el.scrollIntoView({ block: "center" });
  el.classList.add("is-pin-target");
  globalThis.setTimeout(() => {
    el.classList.remove("is-pin-target");
  }, highlightMs);
  return el;
}
