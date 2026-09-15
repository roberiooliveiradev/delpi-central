import { useEffect } from "react";

import { slideNativeHasVideo } from "./videoElementLoadState";

export type PresentationMediaPrefetchSlide = {
  native?: unknown;
};

type MediaUrlPair = {
  videoUrl?: string;
  posterUrl?: string;
};

/**
 * Extrai URLs de vídeo/poster já enriquecidas dos blocos do slide nativo.
 */
export function collectSlideVideoMediaUrls(native: unknown): MediaUrlPair[] {
  if (!native || typeof native !== "object") return [];
  const data = (native as { data?: unknown }).data;
  if (!data || typeof data !== "object") return [];
  const blocks = (data as { blocks?: unknown }).blocks;
  if (!Array.isArray(blocks)) return [];
  const out: MediaUrlPair[] = [];
  for (const raw of blocks) {
    if (!raw || typeof raw !== "object") continue;
    const block = raw as { type?: string; url?: unknown; posterUrl?: unknown };
    if (block.type !== "video") continue;
    const videoUrl = typeof block.url === "string" && block.url.trim() ? block.url.trim() : undefined;
    const posterUrl =
      typeof block.posterUrl === "string" && block.posterUrl.trim()
        ? block.posterUrl.trim()
        : undefined;
    if (videoUrl || posterUrl) out.push({ videoUrl, posterUrl });
  }
  return out;
}

export function nextPresentationSlideIndex(index: number, total: number): number {
  if (!(total > 0)) return 0;
  return (Math.max(0, index) + 1) % total;
}

/**
 * URLs a aquecer para o próximo slide (wrap no fim do deck).
 */
export function collectNextSlideVideoPrefetchUrls(
  slides: ReadonlyArray<PresentationMediaPrefetchSlide | null | undefined>,
  index: number,
): string[] {
  if (!Array.isArray(slides) || slides.length === 0) return [];
  const nextIndex = nextPresentationSlideIndex(index, slides.length);
  const next = slides[nextIndex];
  if (!next || !slideNativeHasVideo(next.native)) return [];
  const urls: string[] = [];
  for (const pair of collectSlideVideoMediaUrls(next.native)) {
    if (pair.posterUrl) urls.push(pair.posterUrl);
    if (pair.videoUrl) urls.push(pair.videoUrl);
  }
  return urls;
}

function ensureLinkPreload(href: string, asAttr: "video" | "image"): () => void {
  if (typeof document === "undefined") return () => undefined;
  const safeHref = href.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  const existing = document.head.querySelector(`link[data-tdp-media-prefetch="${safeHref}"]`);
  if (existing) {
    return () => undefined;
  }
  const link = document.createElement("link");
  link.rel = "preload";
  link.as = asAttr;
  link.href = href;
  link.setAttribute("data-tdp-media-prefetch", href);
  document.head.appendChild(link);
  return () => {
    link.remove();
  };
}

/**
 * Prefetch do próximo slide: poster (image) + vídeo via link preload.
 */
export function usePresentationMediaPrefetch(
  index: number,
  slides: ReadonlyArray<PresentationMediaPrefetchSlide | null | undefined>,
): void {
  useEffect(() => {
    const urls = collectNextSlideVideoPrefetchUrls(slides, index);
    const releases = urls.map((href) => {
      const asAttr = href.includes("/poster") || /\.(jpe?g|png|webp)(\?|$)/i.test(href)
        ? "image"
        : "video";
      return ensureLinkPreload(href, asAttr);
    });
    return () => {
      for (const release of releases) release();
    };
  }, [index, slides]);
}
