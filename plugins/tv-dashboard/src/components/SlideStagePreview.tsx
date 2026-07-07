import { Globe } from "lucide-react";
import { NativeSlideView } from "@delpi/tv-dashboard-presentation";

import type { PresentationPayload, Slide } from "../api/tvDashboardApi";
import { ExternalSlidePreview } from "../presentation/ExternalSlidePreview";
import { buildSlideThumbnailNative, externalSlideHost } from "./slideCardPreview";

type Props = {
  slide: Slide;
  playlistId: string;
  previewSlide?: PresentationPayload["slides"][number];
};

export function SlideStagePreview({ slide, playlistId, previewSlide }: Props) {
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

  const native = buildSlideThumbnailNative(slide, playlistId, previewSlide);
  if (!native) {
    return <div className="td-deck-stage__preview td-deck-stage__preview--empty" />;
  }

  return (
    <div className="td-deck-stage__preview">
      <NativeSlideView native={native} />
    </div>
  );
}
