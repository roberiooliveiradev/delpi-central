/**
 * Canonical render page — mounts the SAME shared presentation stage used by
 * the TV kiosk (`DesignViewportStage` surface="kiosk" + `NativeSlideView`).
 *
 * This is NOT a renderer: it only mounts the shared package. Capture happens
 * in the worker via Playwright rasterization of the painted stage element.
 *
 * Contract (bounded):
 *   window.__tvRenderSlide({ presentation, slideId }) →
 *     { ok: true, width, height } | { ok: false, code }
 */
import { createElement } from "react";
import { createRoot } from "react-dom/client";
import {
  DesignViewportStage,
  NativeSlideView,
  type NativeSlidePayload,
} from "@delpi/tv-dashboard-presentation";

type RenderSlideInput = {
  presentation: {
    playlist?: {
      viewportProfile?: string | null;
      viewportWidth?: number | null;
      viewportHeight?: number | null;
    };
    slides?: Array<{
      id?: string;
      slideType?: string;
      native?: NativeSlidePayload | null;
    }>;
  };
  slideId: string;
};

type RenderSlideResult =
  | { ok: true; width: number; height: number }
  | { ok: false; code: string };

declare global {
  interface Window {
    __tvRenderSlide?: (input: RenderSlideInput) => Promise<RenderSlideResult>;
  }
}

const IMAGE_WAIT_MS = 8000;

const rootEl = document.getElementById("tv-render-root")!;
const reactRoot = createRoot(rootEl);

function nextFrame(): Promise<void> {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

/** Deterministic settle: pause videos at stable initial frame (poster/first). */
function settleMedia(stage: HTMLElement) {
  stage.querySelectorAll("video").forEach((video) => {
    try {
      video.pause();
      if (Number.isFinite(video.duration) && video.currentTime !== 0) {
        video.currentTime = 0;
      }
    } catch {
      // evidence render — poster/stable state is the contract
    }
  });
}

async function waitForImages(stage: HTMLElement): Promise<void> {
  const images = Array.from(stage.querySelectorAll("img"));
  await Promise.race([
    Promise.all(
      images.map((img) =>
        img.complete && img.naturalWidth > 0
          ? Promise.resolve()
          : img
              .decode()
              .then(() => undefined)
              .catch(() => undefined),
      ),
    ),
    new Promise<void>((resolve) => setTimeout(resolve, IMAGE_WAIT_MS)),
  ]);
}

async function renderSlide(input: RenderSlideInput): Promise<RenderSlideResult> {
  const slide = (input.presentation?.slides ?? []).find(
    (item) => String(item?.id ?? "") === String(input.slideId),
  );
  if (!slide) return { ok: false, code: "SLIDE_NOT_IN_PAYLOAD" };
  if ((slide.slideType ?? "native") !== "native" || !slide.native) {
    // External iframes are never navigated/captured — typed refusal.
    return { ok: false, code: "UNSUPPORTED_EXTERNAL_CONTENT" };
  }

  const playlist = input.presentation?.playlist ?? {};
  reactRoot.render(
    createElement(
      DesignViewportStage,
      {
        viewportProfile: playlist.viewportProfile ?? "1080p",
        viewportWidth: playlist.viewportWidth ?? null,
        viewportHeight: playlist.viewportHeight ?? null,
        surface: "kiosk",
        fit: "auto",
        className: "tdp-stage__design",
      },
      createElement(NativeSlideView, {
        native: slide.native,
        comunicadoFontScale: 1,
        inputsInteractive: false,
      }),
    ),
  );

  await nextFrame();
  await nextFrame();
  const painted =
    rootEl.querySelector<HTMLElement>(".tdp-stage") ?? rootEl.firstElementChild as HTMLElement | null ?? rootEl;
  try {
    await document.fonts.ready;
  } catch {
    // fonts readiness is best-effort; bounded by worker timeout
  }
  settleMedia(painted);
  await waitForImages(painted);
  await nextFrame();
  await nextFrame();

  const rect = painted.getBoundingClientRect();
  return {
    ok: true,
    width: Math.max(1, Math.round(rect.width)),
    height: Math.max(1, Math.round(rect.height)),
  };
}

window.__tvRenderSlide = renderSlide;
