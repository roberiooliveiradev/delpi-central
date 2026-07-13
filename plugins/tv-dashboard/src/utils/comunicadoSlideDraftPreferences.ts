const STORAGE_KEY_PREFIX = "td-comunicado-slide-draft:";

export type ComunicadoSlideDraft = {
  updatedAt: number;
  nativeConfig: Record<string, unknown>;
};

function canUseLocalStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function storageKey(playlistId: string, slideId: string): string {
  return `${STORAGE_KEY_PREFIX}${playlistId}:${slideId}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

export function normalizeComunicadoSlideDraft(raw: unknown): ComunicadoSlideDraft | null {
  if (!isRecord(raw)) return null;
  if (typeof raw.updatedAt !== "number" || !Number.isFinite(raw.updatedAt)) return null;
  if (!isRecord(raw.nativeConfig)) return null;
  return {
    updatedAt: raw.updatedAt,
    nativeConfig: raw.nativeConfig,
  };
}

/** Draft local do nativeConfig (sobrevive F5 antes do debounce/API). */
export function readComunicadoSlideDraft(
  playlistId: string,
  slideId: string,
): ComunicadoSlideDraft | null {
  if (!canUseLocalStorage() || !playlistId.trim() || !slideId.trim()) return null;
  try {
    const raw = window.localStorage.getItem(storageKey(playlistId, slideId));
    if (!raw) return null;
    return normalizeComunicadoSlideDraft(JSON.parse(raw));
  } catch {
    return null;
  }
}

export function writeComunicadoSlideDraft(
  playlistId: string,
  slideId: string,
  nativeConfig: Record<string, unknown>,
  updatedAt: number = Date.now(),
): void {
  if (!canUseLocalStorage() || !playlistId.trim() || !slideId.trim()) return;
  try {
    const entry: ComunicadoSlideDraft = { updatedAt, nativeConfig };
    window.localStorage.setItem(storageKey(playlistId, slideId), JSON.stringify(entry));
  } catch {
    // quota / private mode
  }
}

export function clearComunicadoSlideDraft(playlistId: string, slideId: string): void {
  if (!canUseLocalStorage() || !playlistId.trim() || !slideId.trim()) return;
  try {
    window.localStorage.removeItem(storageKey(playlistId, slideId));
  } catch {
    // ignore
  }
}

/**
 * Aplica draft local sobre o slide remoto quando o draft é mais recente
 * (timestamp do draft vs. o que já está no shell; sem updatedAt no Slide remoto,
 * qualquer draft presente vence até o save confirmar e limpar).
 */
export function applyComunicadoSlideDraft<T extends { id: string; nativeConfig?: Record<string, unknown> }>(
  slide: T,
  draft: ComunicadoSlideDraft | null,
): T {
  if (!draft) return slide;
  return { ...slide, nativeConfig: draft.nativeConfig };
}

/** Hidrata todos os slides custom com drafts locais (playlist vinda da API). */
export function mergePlaylistSlidesWithComunicadoDrafts<
  T extends { id: string; slides?: Array<{ id: string; nativeScreenKey?: string | null; nativeConfig?: Record<string, unknown> }> },
>(playlistId: string, playlist: T): T {
  const slides = playlist.slides;
  if (!slides?.length) return playlist;
  let changed = false;
  const nextSlides = slides.map((slide) => {
    if (slide.nativeScreenKey !== "custom_message") return slide;
    const draft = readComunicadoSlideDraft(playlistId, slide.id);
    if (!draft) return slide;
    changed = true;
    return applyComunicadoSlideDraft(slide, draft);
  });
  return changed ? { ...playlist, slides: nextSlides } : playlist;
}

/** Fingerprint leve para testes — inclui kpiParts/chartParts no JSON. */
export function comunicadoDraftIncludesPartKeys(nativeConfig: Record<string, unknown>): boolean {
  const blocks = nativeConfig.blocks;
  if (!Array.isArray(blocks)) return false;
  return blocks.some((block) => {
    if (!isRecord(block)) return false;
    return "kpiParts" in block || "chartParts" in block || "tableParts" in block;
  });
}
