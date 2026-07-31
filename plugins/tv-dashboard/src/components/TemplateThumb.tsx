import { CenteredScaledPreview } from "@delpi/plugin-ui/index";
import { NativeSlideView } from "@delpi/tv-dashboard-presentation";

import type { SlideTemplate } from "../api/tvDashboardApi";
import { resolveViewportPixelSize } from "../utils/viewportPixelSize";
import { buildSlideThumbnailNative } from "./slideCardPreview";

type Props = {
  template: Pick<SlideTemplate, "id" | "nativeConfig" | "nativeScreenKey" | "label">;
  viewportProfile?: string;
};

/** Miniatura client-side a partir do nativeConfig (sem upload). */
export function TemplateThumb({ template, viewportProfile = "1080p" }: Props) {
  const fakeSlide = {
    id: template.id,
    playlistId: "template-library",
    slideType: "native" as const,
    title: template.label,
    nativeScreenKey: template.nativeScreenKey || "custom_message",
    nativeConfig: template.nativeConfig,
    isActive: true,
    sortOrder: 0,
  };
  const native = buildSlideThumbnailNative(fakeSlide, "template-library");
  const { width, height } = resolveViewportPixelSize(viewportProfile);

  if (!native) {
    return (
      <div className="td-slide-thumb td-slide-thumb--empty td-slide-thumb--fill" aria-hidden="true" />
    );
  }

  return (
    <div className="td-slide-thumb td-slide-thumb--fill" aria-hidden="true">
      <CenteredScaledPreview
        referenceWidth={width}
        referenceHeight={height}
        className="td-slide-thumb__preview"
        contentClassName="td-slide-thumb__preview-content"
      >
        <div
          className="td-slide-thumb__stage"
          data-viewport={viewportProfile}
          style={{ width, height }}
        >
          <NativeSlideView native={native} comunicadoFontScale={1} />
        </div>
      </CenteredScaledPreview>
    </div>
  );
}
