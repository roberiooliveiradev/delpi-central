/**
 * Handoff editor → prévia: flush autosave + limpa cache antes de abrir apresentação.
 * Anti-padrão: navegar para prévia sem flush (payload do servidor fica stale).
 */

import { clearPreviewPayloadCache } from "./previewPayloadCache";

type PreviewHandoff = {
  flush: () => Promise<void>;
};

let handoff: PreviewHandoff | null = null;

export function registerPreviewHandoff(next: PreviewHandoff | null): void {
  handoff = next;
}

export async function preparePreviewNavigation(playlistId: string): Promise<void> {
  if (handoff?.flush) {
    await handoff.flush();
  }
  clearPreviewPayloadCache(playlistId);
}
