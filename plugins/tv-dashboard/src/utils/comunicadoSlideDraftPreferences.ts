/**
 * Draft local do nativeConfig do slide custom_message.
 *
 * Rede de segurança antes do debounce/API: sobrevive a F5.
 * Sempre versionado — nunca limpar draft sem comparar versão (anti-padrão).
 */

const STORAGE_KEY_PREFIX = "td-comunicado-slide-draft:";

export type ComunicadoSlideDraft = {
  updatedAt: number;
  /** Versão monotônica do autosave no momento da gravação (0 = legado). */
  version: number;
  nativeConfig: Record<string, unknown>;
};

export type ComunicadoSlideDraftSnapshot = {
  updatedAt: number;
  version: number;
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
  const version =
    typeof raw.version === "number" && Number.isFinite(raw.version) ? Math.max(0, raw.version) : 0;
  return {
    updatedAt: raw.updatedAt,
    version,
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
  version: number = 0,
): void {
  if (!canUseLocalStorage() || !playlistId.trim() || !slideId.trim()) return;
  try {
    const entry: ComunicadoSlideDraft = {
      updatedAt,
      version: Math.max(0, version),
      nativeConfig,
    };
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
 * Limpa o draft só se a versão salva cobre o draft atual.
 * Impede que um updateSlide antigo (reenvio no load) apague edições mais novas.
 */
export function clearComunicadoSlideDraftIfCoveredBySave(
  playlistId: string,
  slideId: string,
  completedVersion: number,
): boolean {
  const draft = readComunicadoSlideDraft(playlistId, slideId);
  if (!draft) return false;
  if (draft.version > completedVersion) return false;
  clearComunicadoSlideDraft(playlistId, slideId);
  return true;
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

type PlaylistWithSlides = {
  slides?: Array<{
    id: string;
    nativeScreenKey?: string | null;
    nativeConfig?: Record<string, unknown>;
  }>;
};

/** Hidrata todos os slides custom com drafts locais (playlist vinda da API). */
export function mergePlaylistSlidesWithComunicadoDrafts<T extends PlaylistWithSlides>(
  playlistId: string,
  playlist: T,
): T {
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

export type LocalComunicadoOverlay = {
  slideId: string;
  nativeConfig: Record<string, unknown>;
};

/**
 * Contrato canônico ao aplicar playlist da API/WS:
 * remote → drafts locais → pending in-memory → live do slide ativo.
 *
 * Anti-padrão: setPlaylist(slides da API) sem este merge.
 */
export function applyServerPlaylistPreservingLocalEdits<T extends PlaylistWithSlides>(args: {
  playlistId: string;
  remote: T;
  pending?: LocalComunicadoOverlay | null;
  live?: LocalComunicadoOverlay | null;
}): T {
  const withDrafts = mergePlaylistSlidesWithComunicadoDrafts(args.playlistId, args.remote);
  const slides = withDrafts.slides;
  if (!slides?.length) return withDrafts;

  let changed = false;
  const nextSlides = slides.map((slide) => {
    if (slide.nativeScreenKey !== "custom_message") return slide;
    if (args.pending?.slideId === slide.id) {
      changed = true;
      return { ...slide, nativeConfig: args.pending.nativeConfig };
    }
    if (args.live?.slideId === slide.id) {
      changed = true;
      return { ...slide, nativeConfig: args.live.nativeConfig };
    }
    return slide;
  });
  return changed ? { ...withDrafts, slides: nextSlides } : withDrafts;
}

/** Há edição local ainda não confirmada no servidor para o slide. */
export function hasLocalComunicadoEdits(args: {
  playlistId: string;
  slideId: string | null | undefined;
  pendingSlideId?: string | null;
}): boolean {
  const slideId = args.slideId?.trim();
  if (!slideId) return false;
  if (args.pendingSlideId === slideId) return true;
  return readComunicadoSlideDraft(args.playlistId, slideId) != null;
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
