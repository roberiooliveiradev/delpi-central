import { Globe } from "lucide-react";
import {
  COMUNICADO_EDITOR_FONT_SCALE,
  NativeSlideView,
} from "@delpi/tv-dashboard-presentation";
import { CenteredScaledPreview } from "@delpi/plugin-ui/index";

import type { Slide } from "../api/tvDashboardApi";
import type { PresentationPayload } from "../api/tvDashboardApi";
import { buildSlideThumbnailNative, externalSlideHost } from "./slideCardPreview";

/** Referência 16:9 — mesma proporção do palco. */
const THUMB_REF_WIDTH = 320;
const THUMB_REF_HEIGHT = 180;

type Props = {
  slide: Slide;
  playlistId: string;
  previewSlide?: PresentationPayload["slides"][number];
};

export function SlideCardThumbnail({ slide, playlistId, previewSlide }: Props) {
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
    <div className="td-slide-thumb" aria-hidden="true">
      <CenteredScaledPreview
        referenceWidth={THUMB_REF_WIDTH}
        referenceHeight={THUMB_REF_HEIGHT}
        className="td-slide-thumb__preview"
        contentClassName="td-slide-thumb__preview-content"
      >
        <NativeSlideView native={native} comunicadoFontScale={COMUNICADO_EDITOR_FONT_SCALE} />
      </CenteredScaledPreview>
    </div>
  );
}
