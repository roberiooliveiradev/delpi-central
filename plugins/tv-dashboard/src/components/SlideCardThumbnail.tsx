import { Globe } from "lucide-react";
import { NativeSlideView } from "@delpi/tv-dashboard-presentation";

import type { Slide } from "../api/tvDashboardApi";
import type { PresentationPayload } from "../api/tvDashboardApi";
import { buildSlideThumbnailNative, externalSlideHost } from "./slideCardPreview";

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
      <div className="td-slide-thumb__scale">
        <NativeSlideView native={native} />
      </div>
    </div>
  );
}
