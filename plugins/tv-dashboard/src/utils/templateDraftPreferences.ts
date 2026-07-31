/**
 * Draft local do editor de template (Biblioteca).
 * Reusa o mesmo contrato versionado do slide de playlist.
 */
import {
  clearComunicadoSlideDraft,
  readComunicadoSlideDraft,
  writeComunicadoSlideDraft,
  type ComunicadoSlideDraft,
} from "./comunicadoSlideDraftPreferences";

const TEMPLATE_PLAYLIST_NS = "__template_library__";

export function readTemplateDraft(templateId: string): ComunicadoSlideDraft | null {
  return readComunicadoSlideDraft(TEMPLATE_PLAYLIST_NS, templateId);
}

export function writeTemplateDraft(
  templateId: string,
  nativeConfig: Record<string, unknown>,
  version: number,
  updatedAt: number = Date.now(),
): void {
  writeComunicadoSlideDraft(TEMPLATE_PLAYLIST_NS, templateId, nativeConfig, updatedAt, version);
}

export function clearTemplateDraft(templateId: string): void {
  clearComunicadoSlideDraft(TEMPLATE_PLAYLIST_NS, templateId);
}

/** Mantém draft local se for mais novo ou versão >= remoto (F5 / merge). */
export function resolveTemplateConfigWithLocalDraft(
  templateId: string,
  serverConfig: Record<string, unknown>,
  serverVersion: number,
): { nativeConfig: Record<string, unknown>; fromDraft: boolean } {
  const draft = readTemplateDraft(templateId);
  if (!draft) return { nativeConfig: serverConfig, fromDraft: false };
  if (draft.version > serverVersion) {
    return { nativeConfig: draft.nativeConfig, fromDraft: true };
  }
  if (draft.version === serverVersion && draft.updatedAt > 0) {
    // Mesma versão remota: preferir draft se houver alterações locais recentes
    return { nativeConfig: draft.nativeConfig, fromDraft: true };
  }
  return { nativeConfig: serverConfig, fromDraft: false };
}
