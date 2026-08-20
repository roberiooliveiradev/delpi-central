/** Caret helpers for @ mention composers (domain-neutral). */

export type ActiveMentionQuery = {
  query: string;
  start: number;
  end: number;
};

/**
 * Detects an active `@query` ending at `cursor` (Notion-style).
 * Trigger after whitespace or start of string / open brackets.
 */
export function detectActiveMention(
  value: string,
  cursor: number,
): ActiveMentionQuery | null {
  const safeCursor = Math.max(0, Math.min(cursor, value.length));
  const before = value.slice(0, safeCursor);
  const match = before.match(/(^|[\s([{])@([^\s@]*)$/);
  if (!match) return null;

  const query = match[2] ?? "";
  const atIndex = before.lastIndexOf("@");
  if (atIndex < 0) return null;

  return {
    query,
    start: atIndex,
    end: safeCursor,
  };
}

export function insertMentionToken(
  value: string,
  cursor: number,
  mentionStart: number,
  displayLabel: string,
): { nextValue: string; nextCursor: number; token: string } {
  const cleaned = displayLabel.trim().replace(/\s+/g, " ");
  const token = cleaned.startsWith("@") ? cleaned : `@${cleaned}`;
  const before = value.slice(0, mentionStart);
  const after = value.slice(cursor);
  const needsSpace = after.length === 0 || !/^\s/.test(after);
  const insertion = needsSpace ? `${token} ` : token;
  const nextValue = `${before}${insertion}${after}`;
  const nextCursor = before.length + insertion.length;
  return { nextValue, nextCursor, token };
}

function collectTextNodes(root: Node): Text[] {
  const nodes: Text[] = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let current = walker.nextNode();
  while (current) {
    nodes.push(current as Text);
    current = walker.nextNode();
  }
  return nodes;
}

/** Texto visível + offset do caret no contenteditable (para detectActiveMention). */
export function snapshotEditablePlaintext(root: HTMLElement): {
  text: string;
  cursor: number;
} {
  const full = document.createRange();
  full.selectNodeContents(root);
  const text = full.toString();
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0 || !root.contains(selection.focusNode)) {
    return { text, cursor: text.length };
  }
  const range = selection.getRangeAt(0);
  const prefix = range.cloneRange();
  prefix.selectNodeContents(root);
  prefix.setEnd(range.endContainer, range.endOffset);
  return { text, cursor: prefix.toString().length };
}

export function setEditablePlainCursor(root: HTMLElement, offset: number): void {
  const nodes = collectTextNodes(root);
  const selection = window.getSelection();
  if (!selection) return;
  let remaining = Math.max(0, offset);
  for (const node of nodes) {
    const len = node.data.length;
    if (remaining <= len) {
      const range = document.createRange();
      range.setStart(node, remaining);
      range.collapse(true);
      selection.removeAllRanges();
      selection.addRange(range);
      return;
    }
    remaining -= len;
  }
  const range = document.createRange();
  range.selectNodeContents(root);
  range.collapse(false);
  selection.removeAllRanges();
  selection.addRange(range);
}

/** Substitui [start, end) no texto plano e devolve o caret após `insert`. */
export function replaceEditablePlainRange(
  root: HTMLElement,
  start: number,
  end: number,
  insert: string,
): number {
  const safeStart = Math.max(0, Math.min(start, end));
  const safeEnd = Math.max(safeStart, end);
  const nodes = collectTextNodes(root);
  if (nodes.length === 0) {
    root.textContent = insert;
    setEditablePlainCursor(root, insert.length);
    return insert.length;
  }

  const range = document.createRange();
  let remainingStart = safeStart;
  let remainingEnd = safeEnd;
  let startNode: Text | null = null;
  let startOffset = 0;
  let endNode: Text | null = null;
  let endOffset = 0;

  for (const node of nodes) {
    const len = node.data.length;
    if (!startNode) {
      if (remainingStart <= len) {
        startNode = node;
        startOffset = remainingStart;
      } else {
        remainingStart -= len;
      }
    }
    if (!endNode) {
      if (remainingEnd <= len) {
        endNode = node;
        endOffset = remainingEnd;
      } else {
        remainingEnd -= len;
      }
    }
    if (startNode && endNode) break;
  }

  if (!startNode || !endNode) {
    root.appendChild(document.createTextNode(insert));
    const next = snapshotEditablePlaintext(root).text.length;
    setEditablePlainCursor(root, next);
    return next;
  }

  range.setStart(startNode, startOffset);
  range.setEnd(endNode, endOffset);
  range.deleteContents();
  const textNode = document.createTextNode(insert);
  range.insertNode(textNode);
  const caret = safeStart + insert.length;
  setEditablePlainCursor(root, caret);
  return caret;
}
