/**
 * VISTA-LIVE-EDITOR-VISUAL-VERIFICATION-003 — captura sob demanda do palco
 * REAL e visível do editor, disparada pelo backend via realtime
 * (`visual_capture_request`).
 *
 * Invariantes de produto:
 * - só captura o slide que o usuário está vendo (nunca troca de slide);
 * - só captura quando o modelo autoritativo corresponde à revisão pedida;
 * - nunca captura estado otimista pré-ack (edições locais pendentes → skip);
 * - nunca usa renderer offscreen — a evidência visual da VISTA é o DOM vivo;
 * - falhas são silenciosas: o caller recebe EDITOR_CAPTURE_PENDING e pode
 *   retentar de forma bounded.
 */

import { getPlaylist, uploadSlideRenderedPreview, type Playlist } from "../api/tvDashboardApi";
import {
  captureSlideElementToPngDataUrl,
  resolveSlideExportTarget,
} from "./exportSlidePng";
import type { PresentationVisualCaptureRequestEvent } from "@delpi/tv-dashboard-presentation";

export type LiveStageCaptureContext = {
  /** Playlist aberta no editor. */
  playlistId: string;
  /** Slide atualmente visível no palco. */
  getSelectedSlideId: () => string | null;
  /** Revisão carregada no modelo local (playlist.revision). */
  getLocalRevision: () => number | null;
  /** Re-aplica o estado autoritativo remoto (presentation_updated). */
  reloadFromServer: () => Promise<void>;
  /** Editor efetivamente ativo/visível na página. */
  isEditorActive: () => boolean;
  /** clientId de presença deste editor (proveniência do artifact). */
  getClientId: () => string | null | undefined;
  /** True quando há edição local ainda não persistida (pré-ack). */
  hasPendingLocalEdits: () => boolean;
};

const FONT_READY_TIMEOUT_MS = 2000;
const _inflight = new Set<string>();

function dataUrlToPngBlob(dataUrl: string): Blob | null {
  const comma = dataUrl.indexOf(",");
  if (!dataUrl.startsWith("data:image/png") || comma < 0) return null;
  const raw = atob(dataUrl.slice(comma + 1));
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) bytes[i] = raw.charCodeAt(i);
  return new Blob([bytes], { type: "image/png" });
}

/** Fonts prontas (bounded) + dois frames — paint estável sem sleep arbitrário. */
export async function waitForStagePaintStability(
  timeoutMs: number = FONT_READY_TIMEOUT_MS,
): Promise<void> {
  try {
    const fontsReady =
      typeof document !== "undefined" && document.fonts?.ready
        ? document.fonts.ready
        : Promise.resolve();
    await Promise.race([
      fontsReady.then(() => undefined).catch(() => undefined),
      new Promise<void>((resolve) => {
        window.setTimeout(resolve, timeoutMs);
      }),
    ]);
  } catch {
    // fonts API indisponível — segue para o frame boundary
  }
  await new Promise<void>((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => resolve());
    });
  });
}

/**
 * Atende um `visual_capture_request`: valida playlist/slide/revisão, espera o
 * modelo autoritativo convergir, captura o palco visível e publica o artifact.
 * Retorna "captured" | "skipped" — nunca lança nem muta a programação.
 */
export async function handleVisualCaptureRequest(
  event: PresentationVisualCaptureRequestEvent,
  ctx: LiveStageCaptureContext,
): Promise<"captured" | "skipped"> {
  if (!event || typeof event.revision !== "number") return "skipped";
  if (String(event.playlistId ?? "") !== String(ctx.playlistId)) return "skipped";
  if (!ctx.isEditorActive()) return "skipped";
  if (ctx.getSelectedSlideId() !== event.slideId) return "skipped";
  const clientId = ctx.getClientId()?.trim();
  if (!clientId) return "skipped";

  const key = `${event.slideId}:${event.revision}`;
  if (_inflight.has(key)) return "skipped";
  _inflight.add(key);
  try {
    // Revisão autoritativa atual — capture só vale se o pedido ainda é atual.
    const remote: Playlist = await getPlaylist(ctx.playlistId);
    const remoteRevision =
      typeof remote.revision === "number"
        ? remote.revision
        : typeof remote.currentRevision === "number"
          ? remote.currentRevision
          : null;
    if (remoteRevision == null || remoteRevision !== event.revision) return "skipped";

    // Modelo local precisa espelhar a revisão pedida — nunca capturar pre-ack.
    if (ctx.getLocalRevision() !== remoteRevision) {
      await ctx.reloadFromServer();
      if (ctx.getLocalRevision() !== remoteRevision) return "skipped";
    }
    if (ctx.getSelectedSlideId() !== event.slideId) return "skipped";
    if (ctx.hasPendingLocalEdits()) return "skipped";

    await waitForStagePaintStability();
    const target = resolveSlideExportTarget(
      document.querySelector(".td-deck-stage__main"),
    );
    if (!target) return "skipped";

    const dataUrl = await captureSlideElementToPngDataUrl(target, { pixelRatio: 1 });
    const blob = dataUrlToPngBlob(dataUrl);
    if (!blob) return "skipped";
    await uploadSlideRenderedPreview(
      ctx.playlistId,
      event.slideId,
      event.revision,
      blob,
      { clientId },
    );
    return "captured";
  } catch {
    return "skipped";
  } finally {
    _inflight.delete(key);
  }
}
