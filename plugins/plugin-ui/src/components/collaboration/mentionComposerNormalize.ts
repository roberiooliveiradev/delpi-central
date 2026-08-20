/**
 * Remove cascas de formato vazias (só ZWSP/whitespace) no composer.
 * Evita «bolhas» indeleveles após undo/unwrap de code, quote e ênfases.
 */

const INLINE_SHELL_SELECTOR = "code, strong, b, em, i, s, strike, del, u, a";

export type NormalizeComposerFormatShellsOptions = {
  /**
   * Mantém a casca vazia sob o caret (modo digitação: `<code>\u200b</code>`).
   * Undo/redo/paste não devem preservar.
   */
  preserveActiveTypingShell?: boolean;
};

/** Conteúdo sem significado tipográfico (ZWSP, NBSP, espaços). */
export function isComposerShellContentEmpty(node: Node): boolean {
  const text = (node.textContent ?? "")
    .replace(/\u200b/g, "")
    .replace(/\u00a0/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return text.length === 0;
}

function boundaryElement(container: Node, offset: number): Element | null {
  if (container.nodeType === Node.TEXT_NODE) return container.parentElement;
  if (!(container instanceof Element)) return null;
  const child =
    container.childNodes[offset] ?? container.childNodes[offset - 1] ?? container;
  if (child instanceof Element) return child;
  return child.parentElement;
}

/** Cascas vazias sob caret colapsado (estilo de digitação). */
export function findActiveTypingFormatShell(editor: HTMLElement): Element | null {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return null;
  const range = selection.getRangeAt(0);
  if (!range.collapsed || !editor.contains(range.commonAncestorContainer)) return null;
  const start = boundaryElement(range.startContainer, range.startOffset);
  const hit = start?.closest(INLINE_SHELL_SELECTOR) ?? null;
  if (!hit || hit === editor || !editor.contains(hit)) return null;
  if (!isComposerShellContentEmpty(hit)) return null;
  return hit;
}

function removeEmptyInlineShells(
  editor: HTMLElement,
  preserve: Element | null,
): boolean {
  let changed = false;
  const shells = Array.from(editor.querySelectorAll(INLINE_SHELL_SELECTOR));
  shells.sort((a, b) => {
    if (a.contains(b)) return 1;
    if (b.contains(a)) return -1;
    return 0;
  });
  for (const el of shells) {
    if (!editor.contains(el)) continue;
    if (preserve && (el === preserve || preserve.contains(el) || el.contains(preserve))) {
      continue;
    }
    if (!isComposerShellContentEmpty(el)) continue;
    el.remove();
    changed = true;
  }
  return changed;
}

function removeEmptyBlockShells(editor: HTMLElement): boolean {
  let changed = false;
  for (const pre of Array.from(editor.querySelectorAll("pre"))) {
    if (!editor.contains(pre)) continue;
    if (isComposerShellContentEmpty(pre)) {
      pre.remove();
      changed = true;
      continue;
    }
    const onlyCode =
      pre.children.length === 1 && pre.firstElementChild?.tagName === "CODE";
    if (onlyCode && isComposerShellContentEmpty(pre.firstElementChild!)) {
      pre.remove();
      changed = true;
    }
  }
  for (const bq of Array.from(editor.querySelectorAll("blockquote"))) {
    if (!editor.contains(bq)) continue;
    if (!isComposerShellContentEmpty(bq)) continue;
    bq.remove();
    changed = true;
  }
  return changed;
}

/**
 * Normaliza o contenteditable após mutação de formato / undo / redo / paste.
 * Idempotente.
 */
export function normalizeComposerFormatShells(
  editor: HTMLElement | null,
  options?: NormalizeComposerFormatShellsOptions,
): void {
  if (!editor) return;
  const preserve = options?.preserveActiveTypingShell
    ? findActiveTypingFormatShell(editor)
    : null;
  let guard = 0;
  while (guard < 8) {
    guard += 1;
    const a = removeEmptyInlineShells(editor, preserve);
    const b = removeEmptyBlockShells(editor);
    if (!a && !b) break;
  }
}
