import { Globe } from "lucide-react";
import { NativeSlideView } from "@delpi/tv-dashboard-presentation";
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
  viewportWidth?: number | null;
  viewportHeight?: number | null;
  masterConfig?: PlaylistMasterConfig;
  /** Token público — mídia do filmstrip via `/public/present/...` (sem JWT). */
  publicToken?: string | null;
  /**
   * Preenche o container pai (home / biblioteca) em vez do tamanho fixo do filmstrip.
   */
  fillContainer?: boolean;
};

export function SlideCardThumbnail({
  slide,
  playlistId,
  previewSlide,
  viewportProfile = "1080p",
  viewportWidth = null,
  viewportHeight = null,
  masterConfig,
  publicToken,
  fillContainer = false,
}: Props) {
  if (slide.slideType === "external") {
    return (
      <div
        className={[
          "td-slide-thumb",
          "td-slide-thumb--external",
          fillContainer ? "td-slide-thumb--fill" : null,
        ]
          .filter(Boolean)
          .join(" ")}
        aria-hidden="true"
      >
        <Globe size={18} strokeWidth={1.6} />
        <span>{externalSlideHost(slide.externalUrl)}</span>
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
    return (
      <div
        className={[
          "td-slide-thumb",
          "td-slide-thumb--empty",
          fillContainer ? "td-slide-thumb--fill" : null,
        ]
          .filter(Boolean)
          .join(" ")}
        aria-hidden="true"
      />
    );
  }

  const { width, height } = resolveViewportPixelSize(viewportProfile, {
    width: viewportWidth,
    height: viewportHeight,
  });

  return (
    <div
      className={["td-slide-thumb", fillContainer ? "td-slide-thumb--fill" : null]
        .filter(Boolean)
        .join(" ")}
      aria-hidden="true"
      style={fillContainer ? undefined : { aspectRatio: `${width} / ${height}` }}
    >
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
          <NativeSlideView native={native} comunicadoFontScale={1} />
        </div>
      </CenteredScaledPreview>
    </div>
  );
}
