/**
 * Handoff editor → prévia / copiloto: flush autosave + limpa cache antes de
 * abrir apresentação ou enviar comando no chat embutido.
 * Garante que `dataDefaults` / native_config persistidos alimentem o mesmo
 * `SlideDataResolutionService` que a TV usa (viewer puro; sem defaults só no live).
 * Anti-padrão: navegar ou planejar no BFF sem flush (payload do servidor fica stale).
 */

import { clearPreviewPayloadCache } from "./previewPayloadCache";

type PreviewHandoff = {
  flush: () => Promise<void>;
};

let handoff: PreviewHandoff | null = null;

export function registerPreviewHandoff(next: PreviewHandoff | null): void {
  handoff = next;
}

/** Flush do autosave do slide ativo — usado por prévia e pelo chat embutido. */
export async function flushRegisteredEditorAutosave(): Promise<void> {
  if (handoff?.flush) {
    await handoff.flush();
  }
}

export async function preparePreviewNavigation(playlistId: string): Promise<void> {
  await flushRegisteredEditorAutosave();
  clearPreviewPayloadCache(playlistId);
}
