import { Copy, Download, Eye, EyeOff, Trash2 } from "lucide-react";

import type { Slide } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DECK_HOME_ACTION_KEYTIPS } from "../utils/deckKeyTips";
import {
  DeckHomePlaylistChrome,
  type DeckHomePlaylistChromeProps,
} from "./deck/DeckEditorHeaderActions";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

type Props = {
  selectedSlide: Slide | null;
  onDuplicate: (slide: Slide) => void;
  onToggleActive: (slide: Slide) => void;
  onRemove: (slide: Slide) => void;
  onExportPng?: () => void;
  onExportPdf?: () => void;
  onExportPptx?: () => void;
  exportBusy?: boolean;
  /** Controles da programação/TV na ribbon; nome/status vão à barra superior. */
  playlistChrome?: DeckHomePlaylistChromeProps;
  /** @deprecated Nova tela / nav ficam no filmstrip — ignorados se passados via spread. */
  slides?: Slide[];
  onAdd?: () => void;
  onSelect?: (slideId: string) => void;
};

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const K = DECK_HOME_ACTION_KEYTIPS;

export function SlideDeckRibbon({
  selectedSlide,
  onDuplicate,
  onToggleActive,
  onRemove,
  onExportPng,
  onExportPdf,
  onExportPptx,
  exportBusy = false,
  playlistChrome,
}: Props) {
  return (
    <div className="td-deck-ribbon__groups">
      {playlistChrome ? <DeckHomePlaylistChrome {...playlistChrome} /> : null}

      {selectedSlide ? (
        <DeckRibbonGroup label="Tela atual" hint={H.currentSlide}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            <DeckRibbonTile
              icon={selectedSlide.isActive ? Eye : EyeOff}
              label={selectedSlide.isActive ? "Pausar" : "Ativar"}
              hint={selectedSlide.isActive ? H.pause : H.activate}
              keyTip={K.toggleActive}
              onClick={() => onToggleActive(selectedSlide)}
            />
            <DeckRibbonTile
              icon={Copy}
              label="Duplicar"
              hint={H.duplicate}
              keyTip={K.duplicate}
              onClick={() => onDuplicate(selectedSlide)}
            />
            {onExportPng ? (
              <DeckRibbonTile
                icon={Download}
                label={exportBusy ? "…" : "PNG"}
                hint="Exportar a tela atual como PNG (4E.5)."
                disabled={exportBusy}
                keyTip={K.exportPng}
                onClick={onExportPng}
              />
            ) : null}
            {onExportPdf ? (
              <DeckRibbonTile
                icon={Download}
                label={exportBusy ? "…" : "PDF"}
                hint="Exportar a tela atual como PDF (captura PNG em página A4)."
                disabled={exportBusy}
                keyTip={K.exportPdf}
                onClick={onExportPdf}
              />
            ) : null}
            {onExportPptx ? (
              <DeckRibbonTile
                icon={Download}
                label={exportBusy ? "…" : "PPTX"}
                hint="Exportar a tela atual como arquivo PPTX editável (MVP)."
                disabled={exportBusy}
                keyTip={K.exportPptx}
                onClick={onExportPptx}
              />
            ) : null}
            <DeckRibbonTile
              icon={Trash2}
              label="Excluir"
              hint={H.delete}
              keyTip={K.remove}
              onClick={() => onRemove(selectedSlide)}
            />
          </div>
        </DeckRibbonGroup>
      ) : null}
    </div>
  );
}
