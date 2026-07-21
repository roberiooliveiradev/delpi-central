import type { PresentationPayload } from "../api/tvDashboardApi";

/** Cache de sessão: reabrir prévia não mostra tela vazia «Carregando…». */
const previewPayloadCache = new Map<string, PresentationPayload>();

export function peekPreviewPayloadCache(playlistId: string): PresentationPayload | null {
  return previewPayloadCache.get(playlistId) ?? null;
}

export function rememberPreviewPayloadCache(playlistId: string, payload: PresentationPayload): void {
  previewPayloadCache.set(playlistId, payload);
}

export function clearPreviewPayloadCache(playlistId?: string): void {
  if (playlistId) previewPayloadCache.delete(playlistId);
  else previewPayloadCache.clear();
}
