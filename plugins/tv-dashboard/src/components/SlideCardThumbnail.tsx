import { Globe } from "lucide-react";
import {
  COMUNICADO_EDITOR_FONT_SCALE,
  NativeSlideView,
} from "@delpi/tv-dashboard-presentation";
import { CenteredScaledPreview } from "@delpi/plugin-ui/index";

import type { PlaylistMasterConfig, Slide } from "../api/tvDashboardApi";
import type { PresentationPayload } from "../api/tvDashboardApi";
import { resolveViewportPixelSize } from "../utils/viewportPixelSize";
import { buildSlideThumbnailNative, externalSlideHost } from "./slideCardPreview";

type Props = {
  slide: Slide;
  playlistId: string;
  previewSlide?: PresentationPayload["slides"][number];
  /** Viewport da playlist — miniaturiza o slide canônico (print exato). */
  viewportProfile?: string;
  masterConfig?: PlaylistMasterConfig;
};

export function SlideCardThumbnail({
  slide,
  playlistId,
  previewSlide,
  viewportProfile = "1080p",
  masterConfig,
}: Props) {
  if (slide.slideType === "external") {
    return (
      <div className="td-slide-thumb td-slide-thumb--external" aria-hidden="true">
        <Globe size={18} strokeWidth={1.6} />
        <span>{externalSlideHost(slide.externalUrl)}</span>
      </div>
    );
  }

  const native = buildSlideThumbnailNative(slide, playlistId, previewSlide, masterConfig);
  if (!native) {
    return <div className="td-slide-thumb td-slide-thumb--empty" aria-hidden="true" />;
  }

  const { width, height } = resolveViewportPixelSize(viewportProfile);

  return (
    <div className="td-slide-thumb" aria-hidden="true">
      <CenteredScaledPreview
        referenceWidth={width}
        referenceHeight={height}
        className="td-slide-thumb__preview"
        contentClassName="td-slide-thumb__preview-content"
      >
        <div
          className="td-slide-thumb__stage"
          data-viewport={viewportProfile || "1080p"}
          style={{ width, height }}
        >
          <NativeSlideView native={native} comunicadoFontScale={COMUNICADO_EDITOR_FONT_SCALE} />
        </div>
      </CenteredScaledPreview>
    </div>
  );
}
