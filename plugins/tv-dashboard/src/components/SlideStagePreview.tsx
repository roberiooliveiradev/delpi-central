import { Globe } from "lucide-react";
import { DesignViewportStage, NativeSlideView } from "@delpi/tv-dashboard-presentation";

import type { PlaylistMasterConfig, PresentationPayload, Slide } from "../api/tvDashboardApi";
import { ExternalSlidePreview } from "../presentation/ExternalSlidePreview";
import { buildSlideThumbnailNative, externalSlideHost } from "./slideCardPreview";

type Props = {
  slide: Slide;
  playlistId: string;
  previewSlide?: PresentationPayload["slides"][number];
  viewportProfile?: string;
  viewportWidth?: number | null;
  viewportHeight?: number | null;
  masterConfig?: PlaylistMasterConfig;
  publicToken?: string | null;
};

export function SlideStagePreview({
  slide,
  playlistId,
  previewSlide,
  viewportProfile = "1080p",
  viewportWidth = null,
  viewportHeight = null,
  masterConfig,
  publicToken,
}: Props) {
  if (slide.slideType === "external") {
    return (
      <div className="td-deck-stage__preview">
        <ExternalSlidePreview
          url={slide.externalUrl}
          title={slide.title}
          sandbox={previewSlide?.external?.sandbox}
          active
        />
        <div className="td-deck-stage__external-label">
          <Globe size={14} strokeWidth={1.6} aria-hidden="true" />
          <span>{externalSlideHost(slide.externalUrl)}</span>
        </div>
      </div>
    );
  }

  const native = buildSlideThumbnailNative(
    slide,
    playlistId,
    previewSlide,
    masterConfig,
    publicToken,
  );
  if (!native) {
    return <div className="td-deck-stage__preview td-deck-stage__preview--empty" />;
  }

  return (
    <div className="td-deck-stage__preview">
      <DesignViewportStage
        viewportProfile={viewportProfile}
        viewportWidth={viewportWidth}
        viewportHeight={viewportHeight}
        surface="thumbnail"
        fit="auto"
      >
        <NativeSlideView native={native} comunicadoFontScale={1} />
      </DesignViewportStage>
    </div>
  );
}
