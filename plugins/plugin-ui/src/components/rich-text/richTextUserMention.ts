/**
 * GLPI-style user mentions in RichTextEditor — spans keyed by numeric data-user-id.
 * Reuses caret helpers from collaboration; does not use MentionComposer token model.
 */

import {
  detectActiveMention,
  setEditablePlainCursor,
  snapshotEditablePlaintext,
  type ActiveMentionQuery,
} from "../collaboration/mentionComposerCaret";
import type { MentionMenuHit } from "../collaboration/MentionMenu";

const USER_ID_DIGITS = /^\d+$/;

export function isGlpiUserMentionId(raw: string): boolean {
  return USER_ID_DIGITS.test(String(raw || "").trim());
}

export function buildGlpiUserMentionLabel(label: string): string {
  const cleaned = String(label || "")
    .trim()
    .replace(/\s+/g, " ");
  if (!cleaned) return "@";
  return cleaned.startsWith("@") ? cleaned : `@${cleaned}`;
}

/** Create a non-editable GLPI mention chip for contentEditable. */
export function createGlpiUserMentionElement(
  doc: Document,
  options: { userId: string; label: string },
): HTMLSpanElement | null {
  const id = String(options.userId || "").trim();
  if (!isGlpiUserMentionId(id)) return null;
  const span = doc.createElement("span");
  span.setAttribute("data-user-mention", "true");
  span.setAttribute("data-user-id", id);
  span.setAttribute("contenteditable", "false");
  span.className = "delpi-ui-mention-text__chip";
  span.textContent = buildGlpiUserMentionLabel(options.label);
  return span;
}

function resolvePlainOffsets(
  root: HTMLElement,
  start: number,
  end: number,
): { startNode: Text; startOffset: number; endNode: Text; endOffset: number } | null {
  const safeStart = Math.max(0, Math.min(start, end));
  const safeEnd = Math.max(safeStart, end);
  const nodes: Text[] = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let current = walker.nextNode();
  while (current) {
    nodes.push(current as Text);
    current = walker.nextNode();
  }
  if (nodes.length === 0) return null;

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
  if (!startNode || !endNode) return null;
  return { startNode, startOffset, endNode, endOffset };
}

/**
 * Replace plain-text range [start, end) with a GLPI user-mention span + trailing space.
 * Returns false if id invalid or range unresolved.
 */
export function insertGlpiUserMentionAtPlainRange(
  root: HTMLElement,
  start: number,
  end: number,
  hit: Pick<MentionMenuHit, "id" | "label">,
): boolean {
  const span = createGlpiUserMentionElement(root.ownerDocument, {
    userId: hit.id,
    label: hit.label,
  });
  if (!span) return false;

  const resolved = resolvePlainOffsets(root, start, end);
  if (!resolved) {
    // Empty editor — seed a paragraph then insert.
    if (!root.firstChild) {
      const p = root.ownerDocument.createElement("p");
      root.appendChild(p);
    }
    const host = (root.querySelector("p") as HTMLElement | null) ?? root;
    host.appendChild(span);
    host.appendChild(root.ownerDocument.createTextNode(" "));
    const snap = snapshotEditablePlaintext(root);
    setEditablePlainCursor(root, snap.text.length);
    return true;
  }

  const range = root.ownerDocument.createRange();
  range.setStart(resolved.startNode, resolved.startOffset);
  range.setEnd(resolved.endNode, resolved.endOffset);
  range.deleteContents();
  range.insertNode(span);
  const space = root.ownerDocument.createTextNode(" ");
  if (span.nextSibling) {
    span.parentNode?.insertBefore(space, span.nextSibling);
  } else {
    span.parentNode?.appendChild(space);
  }
  const selection = window.getSelection();
  if (selection) {
    const caretRange = root.ownerDocument.createRange();
    caretRange.setStart(space, space.data.length);
    caretRange.collapse(true);
    selection.removeAllRanges();
    selection.addRange(caretRange);
  }
  return true;
}

export function refreshActiveUserMention(
  root: HTMLElement | null,
): ActiveMentionQuery | null {
  if (!root) return null;
  const snap = snapshotEditablePlaintext(root);
  return detectActiveMention(snap.text, snap.cursor);
}

export type { ActiveMentionQuery };
