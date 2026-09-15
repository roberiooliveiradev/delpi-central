/**
 * Estado de carga de `<video>` — fonte única para editor e apresentação.
 *
 * Stream com URL pronta ≠ metadados prontos: sem overlay, o usuário vê
 * retângulo preto + `0:00 / 0:00` e acha que quebrou.
 */

export type VideoElementLoadPhase = "idle" | "loading" | "ready" | "error";

/** Espelha HTMLMediaElement.readyState (HAVE_NOTHING=0 … HAVE_ENOUGH_DATA=4). */
export const VIDEO_HAVE_METADATA = 1;

export type DeriveVideoElementLoadPhaseInput = {
  hasSrc: boolean;
  readyState: number;
  error: boolean;
  /** Buffering após play (evento `waiting`). */
  waiting?: boolean;
};

export type DeriveVideoElementLoadPhaseResult = {
  phase: VideoElementLoadPhase;
  /** Overlay “Carregando…” até metadados (ou durante waiting). */
  showLoadingOverlay: boolean;
};

/**
 * Deriva fase observável a partir do elemento de mídia.
 *
 * - Sem src → idle (sem overlay).
 * - error → error.
 * - readyState &lt; HAVE_METADATA → loading (overlay).
 * - waiting mid-playback → loading (overlay leve).
 * - senão ready.
 */
export function deriveVideoElementLoadPhase(
  input: DeriveVideoElementLoadPhaseInput,
): DeriveVideoElementLoadPhaseResult {
  if (!input.hasSrc) {
    return { phase: "idle", showLoadingOverlay: false };
  }
  if (input.error) {
    return { phase: "error", showLoadingOverlay: false };
  }
  if (input.readyState < VIDEO_HAVE_METADATA) {
    return { phase: "loading", showLoadingOverlay: true };
  }
  if (input.waiting) {
    return { phase: "loading", showLoadingOverlay: true };
  }
  return { phase: "ready", showLoadingOverlay: false };
}

/** True se a lista de blocos (ou estrutura com `type`) contém bloco de vídeo. */
export function comunicadoBlocksHaveVideo(
  blocks: ReadonlyArray<{ type?: string } | null | undefined> | null | undefined,
): boolean {
  if (!Array.isArray(blocks) || blocks.length === 0) return false;
  return blocks.some((block) => block?.type === "video");
}

/**
 * Detecta vídeo em `native.data.blocks` de um slide (payload público/prévia).
 */
export function slideNativeHasVideo(native: unknown): boolean {
  if (!native || typeof native !== "object") return false;
  const data = (native as { data?: unknown }).data;
  if (!data || typeof data !== "object") return false;
  const blocks = (data as { blocks?: unknown }).blocks;
  if (!Array.isArray(blocks)) return false;
  return comunicadoBlocksHaveVideo(blocks as Array<{ type?: string }>);
}

/** True se qualquer slide da playlist carrega bloco de vídeo no palco. */
export function presentationSlidesHaveVideo(
  slides: ReadonlyArray<{ native?: unknown } | null | undefined> | null | undefined,
): boolean {
  if (!Array.isArray(slides) || slides.length === 0) return false;
  return slides.some((slide) => slideNativeHasVideo(slide?.native));
}
