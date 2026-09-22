export type RichTextAlign = "left" | "center" | "right" | "justify";

function focusEditor(editor: HTMLElement | null) {
  editor?.focus();
}

/** Seleção atual contida no editor (clone), ou null. */
export function getRichTextSelectionRange(editor: HTMLElement | null): Range | null {
  if (!editor) return null;
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return null;
  const range = selection.getRangeAt(0);
  if (!editor.contains(range.commonAncestorContainer)) return null;
  return range.cloneRange();
}

/** True se o Range ainda aponta para nós vivos dentro do editor. */
export function isRichTextRangeInEditor(
  editor: HTMLElement | null,
  range: Range | null,
): boolean {
  if (!editor || !range) return false;
  try {
    return editor.contains(range.commonAncestorContainer);
  } catch {
    return false;
  }
}

/**
 * Restaura seleção salva antes de comandos da toolbar (que roubam o foco).
 * Se o Range salvo estiver morto (ex.: após remount do contentEditable),
 * preserva a seleção viva atual — não chama só `focus()` sem seleção.
 */
export function restoreRichTextSelection(editor: HTMLElement | null, range: Range | null) {
  if (!editor) return;
  const selection = window.getSelection();
  if (!selection) {
    focusEditor(editor);
    return;
  }

  const liveBeforeFocus =
    selection.rangeCount > 0 &&
    editor.contains(selection.getRangeAt(0).commonAncestorContainer)
      ? selection.getRangeAt(0).cloneRange()
      : null;

  if (isRichTextRangeInEditor(editor, range)) {
    focusEditor(editor);
    try {
      selection.removeAllRanges();
      selection.addRange(range as Range);
      return;
    } catch {
      /* fall through — tenta seleção viva */
    }
  }

  focusEditor(editor);
  if (liveBeforeFocus && isRichTextRangeInEditor(editor, liveBeforeFocus)) {
    try {
      selection.removeAllRanges();
      selection.addRange(liveBeforeFocus);
    } catch {
      /* seleção pode ter invalidado no focus */
    }
  }
}

export function execRichTextCommand(command: string, value?: string) {
  try {
    document.execCommand(command, false, value);
  } catch {
    /* execCommand pode falhar em contextos sem seleção */
  }
}

/** Insere linha horizontal (`<hr>`) — paridade com HTML/Markdown (`---` / `***`). */
export function insertRichTextHorizontalRule(editor: HTMLElement | null): void {
  if (!editor) return;
  focusEditor(editor);
  const before = editor.innerHTML;
  try {
    document.execCommand("insertHorizontalRule");
  } catch {
    /* ignore */
  }
  if (editor.innerHTML !== before && /<hr\b/i.test(editor.innerHTML)) return;
  insertRichTextHtmlFragment(editor, "<hr>");
}

/** Insere HTML na seleção (fallback quando execCommand insertHTML é no-op, ex. jsdom). */
export function insertRichTextHtmlFragment(editor: HTMLElement | null, html: string): void {
  if (!editor || !html) return;
  focusEditor(editor);
  const before = editor.innerHTML;
  try {
    document.execCommand("insertHTML", false, html);
  } catch {
    /* ignore */
  }
  if (editor.innerHTML !== before) return;

  const selection = window.getSelection();
  const range =
    selection &&
    selection.rangeCount > 0 &&
    editor.contains(selection.getRangeAt(0).commonAncestorContainer)
      ? selection.getRangeAt(0)
      : null;

  const template = document.createElement("template");
  template.innerHTML = html;
  const frag = template.content;

  if (range) {
    range.deleteContents();
    range.insertNode(frag);
    selection?.collapseToEnd();
    return;
  }

  const empty =
    !editor.innerHTML.trim() ||
    editor.innerHTML === "<p></p>" ||
    editor.innerHTML === "<br>" ||
    editor.innerHTML === "<p><br></p>";
  if (empty) {
    editor.innerHTML = html;
    return;
  }
  editor.appendChild(frag);
}

export function runRichTextCommand(
  editor: HTMLElement | null,
  command: string,
  value?: string,
) {
  focusEditor(editor);
  execRichTextCommand(command, value);
}

/** Font family via canonical inline CSS pipeline (not execCommand fontName). */
export function applyRichTextFontFamily(editor: HTMLElement | null, fontFamily: string) {
  if (!fontFamily.trim()) return;
  applyRichTextInlineCss(editor, { fontFamily: fontFamily.trim() });
}

function placeCaretInNode(selection: Selection, node: Node, offset: number) {
  const next = document.createRange();
  next.setStart(node, offset);
  next.collapse(true);
  selection.removeAllRanges();
  selection.addRange(next);
}

const RICH_TEXT_BLOCK_TAGS = new Set([
  "p",
  "div",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "li",
  "td",
  "th",
  "blockquote",
  "pre",
]);

function isRichTextBlockElement(node: Node | null): node is HTMLElement {
  return node instanceof HTMLElement && RICH_TEXT_BLOCK_TAGS.has(node.tagName.toLowerCase());
}

function isRichTextBlockHtmlElement(el: HTMLElement): boolean {
  return RICH_TEXT_BLOCK_TAGS.has(el.tagName.toLowerCase());
}

function findClosestRichTextBlock(
  node: Node | null,
  editor: HTMLElement,
): HTMLElement | null {
  let current: Node | null = node;
  while (current && current !== editor) {
    if (isRichTextBlockElement(current) && editor.contains(current)) {
      return current;
    }
    current = current.parentNode;
  }
  return null;
}

/** CSS inline canônico para intents `class: inline` (fonte, tamanho, cor). */
export type RichTextInlineCssPatch = {
  fontSize?: string;
  fontFamily?: string;
  color?: string;
  backgroundColor?: string;
};

export type ApplyRichTextInlineCssOptions = {
  /**
   * When the selection covers the whole block, also stamp the block element
   * (needed to beat editor CSS such as `h2 { font-size }`). Default true.
   */
  stampBlockOnFullCover?: boolean;
};

function applyInlineCssPatch(el: HTMLElement, patch: RichTextInlineCssPatch) {
  if (patch.fontSize != null) {
    el.style.fontSize = patch.fontSize;
    if (el.tagName === "FONT") el.removeAttribute("size");
  }
  if (patch.fontFamily != null) {
    el.style.fontFamily = patch.fontFamily;
    if (el.tagName === "FONT") el.removeAttribute("face");
  }
  if (patch.color != null) {
    el.style.color = patch.color;
    if (el.tagName === "FONT") el.removeAttribute("color");
  }
  if (patch.backgroundColor != null) {
    el.style.backgroundColor = patch.backgroundColor;
  }
}

function stampRichTextInlineCss(root: Node, patch: RichTextInlineCssPatch) {
  if (root instanceof HTMLElement) applyInlineCssPatch(root, patch);
  if (!(root instanceof Element) && !(root instanceof DocumentFragment)) return;
  root.querySelectorAll("*").forEach((node) => {
    if (node instanceof HTMLElement) applyInlineCssPatch(node, patch);
  });
}

function fragmentHasBlockChild(fragment: DocumentFragment): boolean {
  return Array.from(fragment.childNodes).some((child) => isRichTextBlockElement(child));
}

/** True when the live range equals the full contents of `block` (not a partial slice). */
function rangeCoversBlockContents(range: Range, block: HTMLElement): boolean {
  const full = document.createRange();
  full.selectNodeContents(block);
  try {
    return (
      range.compareBoundaryPoints(Range.START_TO_START, full) === 0 &&
      range.compareBoundaryPoints(Range.END_TO_END, full) === 0
    );
  } catch {
    return false;
  }
}

/**
 * Propagate CSS only through *inline* ancestors (Word nested spans).
 * Never write on block elements — inheritance would enlarge unselected siblings.
 */
function propagateRichTextInlineCssToAncestors(
  from: Node | null,
  editor: HTMLElement,
  patch: RichTextInlineCssPatch,
) {
  let el: HTMLElement | null =
    from instanceof HTMLElement ? from : from?.parentElement ?? null;
  while (el && el !== editor) {
    if (isRichTextBlockHtmlElement(el)) break;
    applyInlineCssPatch(el, patch);
    el = el.parentElement;
  }
}

/**
 * Single Range pipeline for inline CSS intents (S-F1):
 * caret → pending span; partial → wrap Range; full block → optional block stamp.
 * Callers: fontSize / fontName / foreColor / hiliteColor via `applyFormat`.
 */
export function applyRichTextInlineCss(
  editor: HTMLElement | null,
  patch: RichTextInlineCssPatch,
  options?: ApplyRichTextInlineCssOptions,
) {
  if (!editor) return;
  const keys = Object.keys(patch).filter(
    (key) => patch[key as keyof RichTextInlineCssPatch] != null,
  );
  if (keys.length === 0) return;

  focusEditor(editor);
  const selection = window.getSelection();
  if (!selection) return;

  let range =
    selection.rangeCount > 0 && editor.contains(selection.getRangeAt(0).commonAncestorContainer)
      ? selection.getRangeAt(0)
      : null;

  if (!range) {
    range = document.createRange();
    range.selectNodeContents(editor);
    range.collapse(false);
    selection.removeAllRanges();
    selection.addRange(range);
  }

  const stampBlockOnFullCover = options?.stampBlockOnFullCover !== false;

  if (range.collapsed) {
    const span = document.createElement("span");
    applyInlineCssPatch(span, patch);
    const marker = document.createTextNode("\u200B");
    span.appendChild(marker);
    range.insertNode(span);
    placeCaretInNode(selection, marker, 1);
    return;
  }

  const containingBlock = findClosestRichTextBlock(range.commonAncestorContainer, editor);
  const coversWholeBlock =
    containingBlock != null && rangeCoversBlockContents(range, containingBlock);

  const fragment = range.extractContents();
  stampRichTextInlineCss(fragment, patch);

  if (fragmentHasBlockChild(fragment)) {
    const first = fragment.firstChild;
    const last = fragment.lastChild;
    range.insertNode(fragment);
    if (first && last) {
      selection.removeAllRanges();
      const next = document.createRange();
      next.setStartBefore(first);
      next.setEndAfter(last);
      selection.addRange(next);
      propagateRichTextInlineCssToAncestors(first, editor, patch);
    }
    return;
  }

  const span = document.createElement("span");
  applyInlineCssPatch(span, patch);
  span.appendChild(fragment);
  range.insertNode(span);
  if (stampBlockOnFullCover && coversWholeBlock && containingBlock) {
    stampRichTextInlineCss(containingBlock, patch);
  } else {
    propagateRichTextInlineCssToAncestors(span, editor, patch);
  }
  selection.removeAllRanges();
  const next = document.createRange();
  next.selectNodeContents(span);
  selection.addRange(next);
}

/**
 * Font size in px via canonical inline CSS pipeline.
 * Does not use execCommand("fontSize") (legacy 1–7 scale).
 */
export function applyRichTextFontSize(editor: HTMLElement | null, fontSizePx: number) {
  applyRichTextInlineCss(editor, { fontSize: `${Math.round(fontSizePx)}px` });
}

/** Foreground / highlight via the same inline CSS pipeline. */
export function applyRichTextForeColor(editor: HTMLElement | null, color: string) {
  if (!color.trim()) return;
  applyRichTextInlineCss(editor, { color: color.trim() });
}

export function applyRichTextHiliteColor(editor: HTMLElement | null, color: string) {
  if (!color.trim()) return;
  applyRichTextInlineCss(editor, { backgroundColor: color.trim() });
}

/** Tamanho computado (px) no ponto da seleção / editor. */
export function queryRichTextFontSize(editor: HTMLElement | null): number | null {
  if (!editor) return null;
  const selection = window.getSelection();
  let el: Element | null = null;
  if (
    selection &&
    selection.rangeCount > 0 &&
    selection.anchorNode &&
    editor.contains(selection.anchorNode)
  ) {
    const node = selection.anchorNode;
    el = node instanceof Element ? node : node.parentElement;
  }
  if (!el) el = editor;
  const px = Number.parseFloat(window.getComputedStyle(el).fontSize);
  return Number.isFinite(px) ? Math.round(px) : null;
}

export function applyRichTextAlign(editor: HTMLElement | null, align: RichTextAlign) {
  if (!editor) return;
  focusEditor(editor);
  let block = findRichTextAlignBlock(editor);
  if (!block) {
    const last = editor.querySelector("p:last-of-type");
    block = (last as HTMLElement | null) ?? editor;
  }
  if (align === "left") {
    block.style.removeProperty("text-align");
  } else {
    block.style.textAlign = align;
  }
}

/** Blocks that can carry `text-align`. Never the editor host (`div` surface). */
const ALIGN_BLOCK_SELECTOR = "p,li,h1,h2,h3,h4,h5,h6,blockquote";

const INLINE_IMAGE_ALIGN_SELECTOR =
  "span.delpi-ui-mention-composer__inline-image, span.delpi-ui-message-thread__inline-image, " +
  "figure.delpi-ui-mention-composer__inline-image, figure.delpi-ui-message-thread__inline-image";

/** Bloco da seleção — se o caret está na imagem, o `<p>` pai (não o primeiro `p` do editor). */
export function findRichTextAlignBlock(editor: HTMLElement | null): HTMLElement | null {
  if (!editor) return null;
  const selection = window.getSelection();
  let el: Element | null = null;
  if (
    selection &&
    selection.rangeCount > 0 &&
    selection.anchorNode &&
    editor.contains(selection.anchorNode)
  ) {
    const node = selection.anchorNode;
    el = node instanceof Element ? node : node.parentElement;
  }
  const image = el?.closest(INLINE_IMAGE_ALIGN_SELECTOR);
  if (image && editor.contains(image)) {
    const parent = image.parentElement;
    if (parent && parent !== editor && parent.matches(ALIGN_BLOCK_SELECTOR)) {
      return parent;
    }
  }
  if (el && editor.contains(el)) {
    const closest = el.closest(ALIGN_BLOCK_SELECTOR);
    if (closest && editor.contains(closest) && closest !== editor) {
      return closest as HTMLElement;
    }
    const innerDiv = el.closest("div");
    if (innerDiv && innerDiv !== editor && editor.contains(innerDiv)) {
      return innerDiv as HTMLElement;
    }
  }
  return null;
}

function normalizeAlignValue(raw: string): RichTextAlign | null {
  const value = raw.trim().toLowerCase();
  if (value === "center" || value === "middle") return "center";
  if (value === "right" || value === "end") return "right";
  if (value === "justify") return "justify";
  if (value === "left" || value === "start" || value === "") return "left";
  return null;
}

/** Lê `text-align` do bloco da seleção (estilo inline; fallback computed). */
export function queryRichTextAlign(editor?: HTMLElement | null): RichTextAlign | null {
  const block = findRichTextAlignBlock(editor ?? null);
  if (!block) return null;
  const inline = normalizeAlignValue(block.style.textAlign || "");
  if (inline) return inline;
  try {
    return normalizeAlignValue(window.getComputedStyle(block).textAlign || "") ?? "left";
  } catch {
    return "left";
  }
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

/** Remove o elemento preservando os filhos (toggle de ênfase / link). */
export function unwrapRichTextElement(el: Element) {
  const parent = el.parentNode;
  if (!parent) return;
  while (el.firstChild) {
    parent.insertBefore(el.firstChild, el);
  }
  parent.removeChild(el);
}

/** Remove a âncora preservando o conteúdo (unlink estrutural, sem depender da seleção). */
export function unwrapRichTextLink(anchor: HTMLAnchorElement) {
  unwrapRichTextElement(anchor);
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

export function queryRichTextCommandEnabled(command: string): boolean {
  try {
    return document.queryCommandEnabled(command);
  } catch {
    return false;
  }
}
