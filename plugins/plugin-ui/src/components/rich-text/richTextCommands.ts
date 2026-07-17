export type RichTextAlign = "left" | "center" | "right" | "justify";

function focusEditor(editor: HTMLElement | null) {
  editor?.focus();
}

export function execRichTextCommand(command: string, value?: string) {
  try {
    document.execCommand(command, false, value);
  } catch {
    /* execCommand pode falhar em contextos sem seleção */
  }
}

export function runRichTextCommand(
  editor: HTMLElement | null,
  command: string,
  value?: string,
) {
  focusEditor(editor);
  execRichTextCommand(command, value);
}

export function applyRichTextFontFamily(editor: HTMLElement | null, fontFamily: string) {
  focusEditor(editor);
  execRichTextCommand("fontName", fontFamily);
}

export function applyRichTextFontSize(editor: HTMLElement | null, fontSizePx: number) {
  focusEditor(editor);
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    execRichTextCommand("fontSize", "3");
    return;
  }
  const range = selection.getRangeAt(0);
  if (range.collapsed) {
    execRichTextCommand("fontSize", "3");
    return;
  }
  const span = document.createElement("span");
  span.style.fontSize = `${fontSizePx}px`;
  try {
    range.surroundContents(span);
  } catch {
    span.appendChild(range.extractContents());
    range.insertNode(span);
  }
  selection.removeAllRanges();
  const next = document.createRange();
  next.selectNodeContents(span);
  next.collapse(false);
  selection.addRange(next);
}

export function applyRichTextAlign(editor: HTMLElement | null, align: RichTextAlign) {
  const map: Record<RichTextAlign, string> = {
    left: "justifyLeft",
    center: "justifyCenter",
    right: "justifyRight",
    justify: "justifyFull",
  };
  runRichTextCommand(editor, map[align]);
}

export function insertRichTextLink(editor: HTMLElement | null, url: string) {
  runRichTextCommand(editor, "createLink", url);
}

/** Completa o esquema quando o usuário digita só o domínio (ex.: `delpi.com.br`). */
export function normalizeRichTextLinkUrl(raw: string): string {
  const url = raw.trim();
  if (!url) return "";
  if (/^[a-z][a-z0-9+.-]*:/i.test(url) || url.startsWith("/") || url.startsWith("#")) {
    return url;
  }
  return `https://${url}`;
}

/** Âncora `<a>` do editor que contém a seleção/cursor atual (ou null). */
export function findRichTextLinkAtSelection(
  editor: HTMLElement | null,
): HTMLAnchorElement | null {
  if (!editor) return null;
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return null;
  const node = selection.getRangeAt(0).commonAncestorContainer;
  const element = node instanceof Element ? node : node.parentElement;
  const anchor = element?.closest("a");
  if (!anchor || !editor.contains(anchor)) return null;
  return anchor as HTMLAnchorElement;
}

/** Remove a âncora preservando o conteúdo (unlink estrutural, sem depender da seleção). */
export function unwrapRichTextLink(anchor: HTMLAnchorElement) {
  const parent = anchor.parentNode;
  if (!parent) return;
  while (anchor.firstChild) {
    parent.insertBefore(anchor.firstChild, anchor);
  }
  parent.removeChild(anchor);
}

/**
 * Aplica link na seleção salva antes do diálogo abrir. Com seleção colapsada
 * (cursor sem texto marcado), insere o próprio URL como texto do link.
 */
export function applyRichTextLinkAtRange(
  editor: HTMLElement | null,
  range: Range | null,
  url: string,
) {
  if (!editor) return;
  editor.focus();
  const selection = window.getSelection();
  if (selection && range) {
    selection.removeAllRanges();
    selection.addRange(range);
  }
  const activeRange =
    selection && selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
  if (!activeRange || activeRange.collapsed) {
    const anchor = document.createElement("a");
    anchor.setAttribute("href", url);
    anchor.textContent = url;
    if (activeRange) {
      activeRange.insertNode(anchor);
      activeRange.setStartAfter(anchor);
      activeRange.collapse(true);
      selection?.removeAllRanges();
      selection?.addRange(activeRange);
    } else {
      editor.appendChild(anchor);
    }
    return;
  }
  execRichTextCommand("createLink", url);
}

export function queryRichTextCommandState(command: string): boolean {
  try {
    return document.queryCommandState(command);
  } catch {
    return false;
  }
}

export function queryRichTextAlign(): RichTextAlign | null {
  if (queryRichTextCommandState("justifyCenter")) return "center";
  if (queryRichTextCommandState("justifyRight")) return "right";
  if (queryRichTextCommandState("justifyFull")) return "justify";
  if (queryRichTextCommandState("justifyLeft")) return "left";
  return null;
}
