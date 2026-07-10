import { Globe } from "lucide-react";
import { useLayoutEffect, useRef, useState } from "react";
import { COMUNICADO_EDITOR_FONT_SCALE, NativeSlideView } from "@delpi/tv-dashboard-presentation";

import type { Slide } from "../api/tvDashboardApi";
import type { PresentationPayload } from "../api/tvDashboardApi";
import { buildSlideThumbnailNative, externalSlideHost } from "./slideCardPreview";

/** Referência 16:9 — mesma proporção do palco; a miniatura escala a partir deste tamanho. */
const THUMB_REF_WIDTH = 320;
const THUMB_REF_HEIGHT = 180;

type Props = {
  slide: Slide;
  playlistId: string;
  previewSlide?: PresentationPayload["slides"][number];
};

export function SlideCardThumbnail({ slide, playlistId, previewSlide }: Props) {
  const thumbRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0.4);

  useLayoutEffect(() => {
    const node = thumbRef.current;
    if (!node) return;

    const updateScale = () => {
      const width = node.clientWidth;
      if (width > 0) {
        setScale(width / THUMB_REF_WIDTH);
      }
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  if (slide.slideType === "external") {
    return (
      <div className="td-slide-thumb td-slide-thumb--external" aria-hidden="true">
        <Globe size={18} strokeWidth={1.6} />
        <span>{externalSlideHost(slide.externalUrl)}</span>
      </div>
    );
  }

  const native = buildSlideThumbnailNative(slide, playlistId, previewSlide);
  if (!native) {
    return <div className="td-slide-thumb td-slide-thumb--empty" aria-hidden="true" />;
  }

  return (
    <div ref={thumbRef} className="td-slide-thumb" aria-hidden="true">
      <div
        className="td-slide-thumb__scale"
        style={{
          width: THUMB_REF_WIDTH,
          height: THUMB_REF_HEIGHT,
          transform: `scale(${scale})`,
        }}
      >
        <NativeSlideView native={native} comunicadoFontScale={COMUNICADO_EDITOR_FONT_SCALE} />
      </div>
    </div>
  );
}
