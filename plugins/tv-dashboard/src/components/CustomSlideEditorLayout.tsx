import type { ComponentProps } from "react";
import { useMemo } from "react";

import type { Slide } from "../api/tvDashboardApi";
import { ComunicadoComposerCanvas } from "./ComunicadoComposer";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckEditorChrome } from "./DeckEditorChrome";
import { DeckWorkspace } from "./DeckWorkspace";
import { ComunicadoSlideTemplatesPanel } from "./deck/ComunicadoSlideTemplatesPanel";
import { DeckElementSidePanel } from "./deck";
import { SlideDataFiltersPanel } from "./SlideDataFiltersPanel";
import { serializeComunicadoConfigForThumbnail } from "./slideCardPreview";

type WorkspaceProps = ComponentProps<typeof DeckWorkspace>;
type ChromeProps = ComponentProps<typeof DeckEditorChrome>;

type Props = {
  selectedSlide: Slide;
  workspaceProps: WorkspaceProps;
  chromeProps: ChromeProps;
  adminLabels: Record<string, string>;
};

/** Palco + filmstrip dentro do provider — miniatura usa config ao vivo do editor. */
export function CustomSlideEditorLayout({
  selectedSlide,
  workspaceProps,
  chromeProps,
  adminLabels,
}: Props) {
  const { config, blocks, dataPreviewLoading, dataPreviewError } = useComunicadoEditor();

  const slidesForFilmstrip = useMemo(
    () =>
      workspaceProps.slides.map((slide) =>
        slide.id === selectedSlide.id
          ? {
              ...slide,
              // Inclui `resolved` dos blocos de dados — print exato do gráfico/tabela no palco.
              nativeConfig: serializeComunicadoConfigForThumbnail(config, blocks),
            }
          : slide,
      ),
    [workspaceProps.slides, selectedSlide.id, config, blocks],
  );

  const slideTabExtra = (
    <div className="td-deck-settings-tools-row">
      <ComunicadoSlideTemplatesPanel compact />
      <SlideDataFiltersPanel branchScope={chromeProps.branchScope} compact />
    </div>
  );

  const chromeWithSlideExtras = { ...chromeProps, slideTabExtra };

  return (
    <>
      {dataPreviewError ? (
        <p className="td-deck-preview-banner td-deck-preview-banner--error" role="status">
          Preview de dados: {dataPreviewError}
        </p>
      ) : dataPreviewLoading ? (
        <p className="td-deck-preview-banner" role="status">
          Atualizando dados…
        </p>
      ) : null}
      <DeckEditorChrome {...chromeWithSlideExtras} />
      <DeckWorkspace
        {...workspaceProps}
        slides={slidesForFilmstrip}
        selectedSlideId={selectedSlide.id}
        rightPanel={<DeckElementSidePanel labels={adminLabels} />}
        stage={
          <div className="td-deck-stage__editor">
            <ComunicadoComposerCanvas />
          </div>
        }
      />
    </>
  );
}
