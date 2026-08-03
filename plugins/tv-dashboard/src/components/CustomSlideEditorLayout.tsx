import type { ComponentProps } from "react";
import { useMemo, useRef } from "react";

import type { Slide } from "../api/tvDashboardApi";
import { ComunicadoComposerCanvas } from "./ComunicadoComposer";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataCatalogModalHost } from "./DataCatalogModalHost";
import { DeckEditorChrome } from "./DeckEditorChrome";
import { DeckWorkspace } from "./DeckWorkspace";
import { ComunicadoSlideTemplatesPanel } from "./deck/ComunicadoSlideTemplatesPanel";
import { DeckElementSidePanel } from "./deck";
import { SlideDataFiltersPanel } from "./SlideDataFiltersPanel";
import {
  buildFilmstripSlidesWithThumbnailCache,
  serializeComunicadoConfigForThumbnail,
} from "./slideCardPreview";

type WorkspaceProps = Omit<ComponentProps<typeof DeckWorkspace>, "stage">;
type ChromeProps = ComponentProps<typeof DeckEditorChrome>;

type Props = {
  selectedSlide: Slide;
  workspaceProps: WorkspaceProps;
  chromeProps: ChromeProps;
  adminLabels: Record<string, string>;
  /**
   * `template` — mesmo compositor da playlist, sem filmstrip/seções/aba Programação.
   */
  variant?: "playlist" | "template";
};

/** Palco + (opcional) filmstrip dentro do provider — miniatura usa config ao vivo. */
export function CustomSlideEditorLayout({
  selectedSlide,
  workspaceProps,
  chromeProps,
  adminLabels,
  variant = "playlist",
}: Props) {
  const {
    config,
    blocks,
    appliedSlideId,
    isDataPreviewStale,
    dataPreviewLoading,
    refreshDataPreview,
  } = useComunicadoEditor();
  const thumbnailCacheRef = useRef<Record<string, Record<string, unknown>>>({});
  const isTemplate = variant === "template";

  const liveThumbnailConfig = useMemo(
    () => serializeComunicadoConfigForThumbnail(config, blocks),
    [config, blocks],
  );

  const slidesForFilmstrip = useMemo(
    () =>
      isTemplate
        ? workspaceProps.slides
        : buildFilmstripSlidesWithThumbnailCache({
            slides: workspaceProps.slides,
            selectedSlideId: selectedSlide.id,
            liveSlideId: appliedSlideId ?? selectedSlide.id,
            liveThumbnailConfig,
            cache: thumbnailCacheRef.current,
          }),
    [
      isTemplate,
      workspaceProps.slides,
      selectedSlide.id,
      appliedSlideId,
      liveThumbnailConfig,
    ],
  );

  const slideTabExtra = isTemplate ? (
    <SlideDataFiltersPanel
      branchScope={chromeProps.branchScope}
      compact
      playlistDefaults={chromeProps.playlist.dataDefaults}
    />
  ) : (
    <>
      <ComunicadoSlideTemplatesPanel compact />
      <SlideDataFiltersPanel
        branchScope={chromeProps.branchScope}
        compact
        playlistDefaults={chromeProps.playlist.dataDefaults}
      />
    </>
  );

  const playlistChrome = chromeProps.slideDeck?.playlistChrome
    ? {
        ...chromeProps.slideDeck.playlistChrome,
        onRefreshVisual: () => {
          void refreshDataPreview({ force: true });
          chromeProps.slideDeck?.playlistChrome?.onRefreshVisual?.();
        },
        dataPreviewStale: isDataPreviewStale,
        dataPreviewLoading,
      }
    : chromeProps.slideDeck?.playlistChrome;

  const chromeWithSlideExtras = {
    ...chromeProps,
    variant,
    slideTabExtra,
    slideDeck: chromeProps.slideDeck
      ? { ...chromeProps.slideDeck, playlistChrome }
      : chromeProps.slideDeck,
  };

  return (
    <>
      <DeckEditorChrome {...chromeWithSlideExtras} />
      <DataCatalogModalHost branchScope={chromeProps.branchScope} />
      <DeckWorkspace
        {...workspaceProps}
        slides={slidesForFilmstrip}
        selectedSlideId={selectedSlide.id}
        hideFilmstrip={isTemplate}
        sections={isTemplate ? undefined : workspaceProps.sections}
        rightPanel={
          <div className="td-deck-right-stack">
            <DeckElementSidePanel labels={adminLabels} branchScope={chromeProps.branchScope} />
          </div>
        }
        stage={
          <div className="td-deck-stage__editor">
            <ComunicadoComposerCanvas />
          </div>
        }
      />
    </>
  );
}
