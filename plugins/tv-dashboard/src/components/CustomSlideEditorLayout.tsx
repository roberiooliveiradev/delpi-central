import type { ComponentProps } from "react";
import { useMemo } from "react";
import { serializeComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import type { Slide } from "../api/tvDashboardApi";
import { ComunicadoComposerCanvas } from "./ComunicadoComposer";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckEditorChrome } from "./DeckEditorChrome";
import { DeckWorkspace } from "./DeckWorkspace";
import { DeckElementSidePanel } from "./deck";

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
  const { config } = useComunicadoEditor();

  const slidesForFilmstrip = useMemo(
    () =>
      workspaceProps.slides.map((slide) =>
        slide.id === selectedSlide.id
          ? { ...slide, nativeConfig: serializeComunicadoConfig(config) }
          : slide,
      ),
    [workspaceProps.slides, selectedSlide.id, config],
  );

  return (
    <>
      <DeckEditorChrome {...chromeProps} />
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
