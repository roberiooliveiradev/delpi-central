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
  masterConfig?: PlaylistMasterConfig;
};

export function SlideStagePreview({
  slide,
  playlistId,
  previewSlide,
  viewportProfile = "1080p",
  masterConfig,
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

  const native = buildSlideThumbnailNative(slide, playlistId, previewSlide, masterConfig);
  if (!native) {
    return <div className="td-deck-stage__preview td-deck-stage__preview--empty" />;
  }

  return (
    <div className="td-deck-stage__preview">
      <DesignViewportStage viewportProfile={viewportProfile}>
        <NativeSlideView native={native} comunicadoFontScale={1} />
      </DesignViewportStage>
    </div>
  );
}
