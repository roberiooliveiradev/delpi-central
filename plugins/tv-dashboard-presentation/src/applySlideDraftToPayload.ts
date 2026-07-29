import type { PresentationPayloadLike, PresentationSlide } from "./types";

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

/**
 * Aplica `nativeConfig` do WS `slide_draft` sobre o slide da apresentação.
 * Mantém `resolved` (e demais campos) do servidor quando o rascunho ainda não tem.
 */
export function mergeSlideDraftOntoNative(
  liveConfig: Record<string, unknown>,
  serverData: Record<string, unknown> | undefined,
): Record<string, unknown> {
  const server = serverData ?? {};
  const liveBlocks = Array.isArray(liveConfig.blocks) ? liveConfig.blocks : null;
  const serverBlocks = Array.isArray(server.blocks) ? server.blocks : [];
  const serverById = new Map<string, Record<string, unknown>>();
  for (const block of serverBlocks) {
    if (isRecord(block) && typeof block.id === "string") {
      serverById.set(block.id, block);
    }
  }

  const mergedBlocks = liveBlocks
    ? liveBlocks.map((block) => {
        if (!isRecord(block) || typeof block.id !== "string") return block;
        const prev = serverById.get(block.id);
        if (!prev) return block;
        return {
          ...prev,
          ...block,
          resolved: block.resolved ?? prev.resolved,
        };
      })
    : serverBlocks;

  return {
    ...server,
    ...liveConfig,
    blocks: mergedBlocks,
  };
}

export function applySlideDraftToPayload<T extends PresentationPayloadLike>(
  payload: T,
  slideId: string,
  nativeConfig: Record<string, unknown>,
): T {
  const slides = payload.slides;
  if (!slides?.length) return payload;

  let changed = false;
  const nextSlides = slides.map((slide: PresentationSlide) => {
    if (slide.id !== slideId || slide.slideType !== "native" || !slide.native) {
      return slide;
    }
    changed = true;
    const serverData = isRecord(slide.native.data) ? slide.native.data : {};
    return {
      ...slide,
      native: {
        ...slide.native,
        config: nativeConfig,
        data: mergeSlideDraftOntoNative(nativeConfig, serverData),
      },
    };
  });

  return changed ? { ...payload, slides: nextSlides } : payload;
}
