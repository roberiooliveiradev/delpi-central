/**
 * Evita que Backspace/Delete na fronteira de negrito/itálico “contamine”
 * o restante da linha (bug clássico do contentEditable + HTML do Word).
 */

type TextCaret = { node: Text; offset: number };

function previousTextNode(from: Text, editor: HTMLElement): Text | null {
  const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT);
  let prev: Text | null = null;
  let current = walker.nextNode();
  while (current) {
    if (current === from) return prev;
    prev = current as Text;
    current = walker.nextNode();
  }
  return null;
}

function nextTextNode(from: Text, editor: HTMLElement): Text | null {
  const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT);
  let current = walker.nextNode();
  let seen = false;
  while (current) {
    if (seen) return current as Text;
    if (current === from) seen = true;
    current = walker.nextNode();
  }
  return null;
}

function resolveTextCaret(range: Range): TextCaret | null {
  const { startContainer, startOffset } = range;
  if (startContainer.nodeType === Node.TEXT_NODE) {
    return { node: startContainer as Text, offset: startOffset };
  }
  if (startContainer instanceof Element) {
    const before = startContainer.childNodes[startOffset - 1];
    const after = startContainer.childNodes[startOffset];
    if (before?.nodeType === Node.TEXT_NODE) {
      const node = before as Text;
      return { node, offset: node.data.length };
    }
    if (after?.nodeType === Node.TEXT_NODE) {
      return { node: after as Text, offset: 0 };
    }
    if (after) {
      const walker = document.createTreeWalker(after, NodeFilter.SHOW_TEXT);
      const text = walker.nextNode() as Text | null;
      if (text) return { node: text, offset: 0 };
    }
    if (before) {
      const walker = document.createTreeWalker(before, NodeFilter.SHOW_TEXT);
      let text: Text | null = null;
      let current = walker.nextNode();
      while (current) {
        text = current as Text;
        current = walker.nextNode();
      }
      if (text) return { node: text, offset: text.data.length };
    }
  }
  return null;
}

function adjacentChar(
  caret: TextCaret,
  direction: "backward" | "forward",
  editor: HTMLElement,
): TextCaret | null {
  if (direction === "backward") {
    if (caret.offset > 0) {
      return { node: caret.node, offset: caret.offset - 1 };
    }
    const prev = previousTextNode(caret.node, editor);
    if (!prev?.data.length) return null;
    return { node: prev, offset: prev.data.length - 1 };
  }
  if (caret.offset < caret.node.data.length) {
    return { node: caret.node, offset: caret.offset };
  }
  const next = nextTextNode(caret.node, editor);
  if (!next?.data.length) return null;
  return { node: next, offset: 0 };
}

/**
 * Assinatura de ênfase (negrito/itálico/sublinhado/tachado).
 * Estilo inline mais interno vence (ex.: span font-weight:normal dentro de <b>).
 */
export function richTextEmphasisSignature(node: Node, editor: HTMLElement): string {
  let bold: boolean | null = null;
  let italic: boolean | null = null;
  let underline: boolean | null = null;
  let strike: boolean | null = null;

  let el: Element | null = node instanceof Element ? node : node.parentElement;
  while (el && el !== editor) {
    if (el instanceof HTMLElement) {
      const fw = el.style.fontWeight.trim().toLowerCase();
      if (bold === null && fw) {
        if (fw === "normal" || fw === "400") bold = false;
        else if (fw === "bold" || fw === "bolder" || Number.parseInt(fw, 10) >= 600) {
          bold = true;
        }
      }
      const fs = el.style.fontStyle.trim().toLowerCase();
      if (italic === null && fs) {
        if (fs === "normal") italic = false;
        else if (fs === "italic" || fs === "oblique") italic = true;
      }
      const deco = `${el.style.textDecoration} ${el.style.textDecorationLine}`.toLowerCase();
      if (underline === null && deco.includes("underline")) underline = true;
      if (underline === null && deco.includes("none")) underline = false;
      if (strike === null && deco.includes("line-through")) strike = true;
    }

    const tag = el.tagName;
    if (bold === null && (tag === "B" || tag === "STRONG")) bold = true;
    if (italic === null && (tag === "I" || tag === "EM")) italic = true;
    if (underline === null && tag === "U") underline = true;
    if (strike === null && (tag === "S" || tag === "STRIKE" || tag === "DEL")) strike = true;

    el = el.parentElement;
  }

  if (bold === null || italic === null) {
    const probe = node instanceof Element ? node : node.parentElement;
    if (probe && editor.contains(probe)) {
      try {
        const cs = window.getComputedStyle(probe);
        if (bold === null) {
          const weight = cs.fontWeight;
          bold = weight === "bold" || Number.parseInt(weight, 10) >= 600;
        }
        if (italic === null) {
          italic = cs.fontStyle === "italic" || cs.fontStyle === "oblique";
        }
      } catch {
        /* jsdom / contexto sem computed style */
      }
    }
  }

  return [
    bold ? "b" : "",
    italic ? "i" : "",
    underline ? "u" : "",
    strike ? "s" : "",
  ].join("");
}

function pruneEmptyInline(editor: HTMLElement) {
  editor.querySelectorAll("b,strong,i,em,u,s,strike,del,span").forEach((el) => {
    if (!(el instanceof HTMLElement) || !editor.contains(el)) return;
    if (el.classList.length > 0) return;
    if ([...el.attributes].some((attr) => attr.name !== "style")) return;
    if (el.querySelector("img, br, table, a")) return;
    const text = (el.textContent ?? "").replace(/\u200B/g, "");
    if (text.length > 0) return;
    if (el.childElementCount > 0) return;
    el.remove();
  });
}

/**
 * Se o caractere a apagar tem ênfase diferente do caret, apaga manualmente
 * sem deixar o browser fundir o trecho no <b>/<strong> vizinho.
 * @returns true se consumiu o evento (chamar preventDefault).
 */
export function tryDeleteRichTextAtEmphasisBoundary(
  editor: HTMLElement | null,
  direction: "backward" | "forward",
): boolean {
  if (!editor) return false;
  const selection = window.getSelection();
  if (!selection?.isCollapsed || selection.rangeCount === 0) return false;
  const liveRange = selection.getRangeAt(0);
  if (!editor.contains(liveRange.commonAncestorContainer)) return false;

  const caret = resolveTextCaret(liveRange);
  if (!caret) return false;

  const target = adjacentChar(caret, direction, editor);
  if (!target) return false;

  const caretSig = richTextEmphasisSignature(caret.node, editor);
  const targetSig = richTextEmphasisSignature(target.node, editor);
  if (caretSig === targetSig) return false;

  const del = document.createRange();
  del.setStart(target.node, target.offset);
  del.setEnd(target.node, target.offset + 1);
  del.deleteContents();

  selection.removeAllRanges();
  const next = document.createRange();
  if (direction === "backward") {
    if (caret.node.isConnected) {
      const offset = Math.min(caret.offset, caret.node.data.length);
      next.setStart(caret.node, offset);
    } else if (target.node.isConnected) {
      next.setStart(target.node, Math.min(target.offset, target.node.data.length));
    } else {
      pruneEmptyInline(editor);
      return true;
    }
    next.collapse(true);
  } else if (target.node.isConnected) {
    next.setStart(target.node, Math.min(target.offset, target.node.data.length));
    next.collapse(true);
  } else if (caret.node.isConnected) {
    next.setStart(caret.node, Math.min(caret.offset, caret.node.data.length));
    next.collapse(true);
  } else {
    pruneEmptyInline(editor);
    return true;
  }
  selection.addRange(next);
  pruneEmptyInline(editor);
  return true;
}
