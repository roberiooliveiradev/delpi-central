/**
 * Clipboard de sessão da Grade — compartilhado entre view (Ctrl+C/V) e menu contextual.
 */

import type { CanvasTableClipboardPayload } from "./canvasTableClipboard";

let canvasTableSessionClipboard: CanvasTableClipboardPayload | null = null;

export function getCanvasTableSessionClipboard(): CanvasTableClipboardPayload | null {
  return canvasTableSessionClipboard;
}

export function setCanvasTableSessionClipboard(
  payload: CanvasTableClipboardPayload | null,
): void {
  canvasTableSessionClipboard = payload;
}
