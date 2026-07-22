import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { FormatRibbonOpacityFields } from "../formatRibbon/FormatRibbonOrganizeSection";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const APPEARANCE_HINT =
  H.display ??
  "Opacidade e ajuste de mídia (como a imagem/vídeo preenche o quadro).";

/**
 * Exibição — opacidade (+ objectFit em mídia).
 * Não misturar com Tamanho e posição (geometria).
 */
export function AppearanceSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected } = useComunicadoEditor();
  if (!selected) return null;

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Exibição" hint={APPEARANCE_HINT} defaultOpen={false}>
        <div className="td-selection-section td-selection-section--pane-appearance">
          <FormatRibbonOpacityFields />
        </div>
      </SelectionPaneSection>
    );
  }

  return (
    <DeckRibbonGroup
      groupId="appearance-display"
      label="Exibição"
      hint={APPEARANCE_HINT}
      captionPlacement="below"
    >
      <FormatRibbonOpacityFields className="td-deck-ribbon__organize-props td-deck-ribbon__appearance-props" />
    </DeckRibbonGroup>
  );
}
