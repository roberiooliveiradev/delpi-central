/**
 * PDF da programação — captura offscreen por slide ativo (NativeSlideView),
 * páginas no aspecto do design (px → mm CSS 96 dpi).
 */

import { createElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { NativeSlideView, type NativeSlidePayload } from "@delpi/tv-dashboard-presentation";

import type { PlaylistMasterConfig, PresentationPayload, Slide } from "../api/tvDashboardApi";
import { buildSlideThumbnailNative } from "../components/slideCardPreview";
import {
  captureSlideElementToPngDataUrl,
  exportPngDataUrlsToPdf,
  type ExportSlideCaptureOptions,
} from "./exportSlidePng";
import { resolveViewportPixelSize, type ViewportPixelSize } from "./viewportPixelSize";

export type ExportPdfScope = "playlist" | "current";

export type ExportPlaylistPdfProgress = {
  current: number;
  total: number;
  slideTitle?: string;
};

export type ExportPlaylistPdfOptions = ExportSlideCaptureOptions & {
  fileName?: string;
  designSize: ViewportPixelSize;
  playlistId: string;
  slides: Slide[];
  previewBySlideId?: Record<string, PresentationPayload["slides"][number]>;
  masterConfig?: PlaylistMasterConfig;
  publicToken?: string | null;
  onProgress?: (progress: ExportPlaylistPdfProgress) => void;
  signal?: AbortSignal;
};

function assertNotAborted(signal?: AbortSignal) {
  if (signal?.aborted) {
    throw new DOMException("Exportação cancelada.", "AbortError");
  }
}

function waitFrames(count = 2): Promise<void> {
  return new Promise((resolve) => {
    let left = count;
    const tick = () => {
      left -= 1;
      if (left <= 0) resolve();
      else requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
}

async function mountOffscreenNative(
  native: NativeSlidePayload,
  designSize: ViewportPixelSize,
): Promise<{ host: HTMLDivElement; stage: HTMLElement; root: Root }> {
  const host = document.createElement("div");
  host.className = "td-export-pdf-offscreen";
  host.setAttribute("data-export-ignore", "true");
  host.style.width = `${designSize.width}px`;
  host.style.height = `${designSize.height}px`;
  document.body.appendChild(host);

  const root = createRoot(host);
  await new Promise<void>((resolve) => {
    root.render(
      createElement(
        "div",
        {
          className: "td-export-pdf-offscreen__stage",
          style: {
            width: designSize.width,
            height: designSize.height,
            overflow: "hidden",
            background: "#ffffff",
          },
        },
        createElement(NativeSlideView, { native, comunicadoFontScale: 1 }),
      ),
    );
    requestAnimationFrame(() => resolve());
  });
  await waitFrames(2);
  const stage =
    host.querySelector<HTMLElement>(".td-export-pdf-offscreen__stage") ?? host;
  return { host, stage, root };
}

async function unmountOffscreen(host: HTMLDivElement, root: Root) {
  root.unmount();
  host.remove();
}

/** Captura PNG offscreen de um payload nativo no tamanho de design. */
export async function captureOffscreenNativeToPngDataUrl(
  native: NativeSlidePayload,
  designSize: ViewportPixelSize,
  options: ExportSlideCaptureOptions = {},
): Promise<string> {
  const { host, stage, root } = await mountOffscreenNative(native, designSize);
  try {
    return await captureSlideElementToPngDataUrl(stage, options);
  } finally {
    await unmountOffscreen(host, root);
  }
}

function resolveNativeForExport(
  slide: Slide,
  options: Pick<
    ExportPlaylistPdfOptions,
    "playlistId" | "previewBySlideId" | "masterConfig" | "publicToken"
  >,
): NativeSlidePayload | null {
  return buildSlideThumbnailNative(
    slide,
    options.playlistId,
    options.previewBySlideId?.[slide.id],
    options.masterConfig,
    options.publicToken,
  );
}

/**
 * Gera PDF com uma página por slide ativo nativo (ordem de apresentação).
 * Slides externos ou sem canvas visual são ignorados.
 */
export async function exportActivePlaylistSlidesToPdf(
  options: ExportPlaylistPdfOptions,
): Promise<{ pageCount: number; skipped: number }> {
  const active = options.slides
    .filter((slide) => slide.isActive !== false)
    .slice()
    .sort((a, b) => a.sortOrder - b.sortOrder);

  const pages: string[] = [];
  let skipped = 0;
  const total = active.length;

  for (let index = 0; index < active.length; index += 1) {
    assertNotAborted(options.signal);
    const slide = active[index];
    options.onProgress?.({
      current: index + 1,
      total,
      slideTitle: slide.title,
    });

    if (slide.slideType === "external") {
      skipped += 1;
      continue;
    }
    const native = resolveNativeForExport(slide, options);
    if (!native) {
      skipped += 1;
      continue;
    }
    const dataUrl = await captureOffscreenNativeToPngDataUrl(
      native,
      options.designSize,
      {
        pixelRatio: options.pixelRatio,
        backgroundColor: options.backgroundColor,
      },
    );
    pages.push(dataUrl);
  }

  if (!pages.length) {
    throw new Error("Nenhuma tela ativa exportável (nativa) encontrada.");
  }

  const safeName =
    options.fileName ??
    `programacao-${Date.now()}.pdf`;
  await exportPngDataUrlsToPdf(pages, {
    fileName: safeName,
    designSize: options.designSize,
  });
  return { pageCount: pages.length, skipped };
}

export function resolvePlaylistDesignSize(playlist: {
  viewportProfile?: string | null;
  viewportWidth?: number | null;
  viewportHeight?: number | null;
}): ViewportPixelSize {
  return resolveViewportPixelSize(playlist.viewportProfile, {
    width: playlist.viewportWidth,
    height: playlist.viewportHeight,
  });
}
