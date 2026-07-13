import {
  ChevronLeft,
  ChevronRight,
  Copy,
  Download,
  Eye,
  EyeOff,
  Plus,
  Trash2,
} from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";

import type { Slide } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DECK_HOME_ACTION_KEYTIPS } from "../utils/deckKeyTips";
import { DeckKeyTip } from "./DeckKeyTip";
import {
  DeckHomePlaylistChrome,
  type DeckHomePlaylistChromeProps,
} from "./deck/DeckEditorHeaderActions";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonLargeButton } from "./deck/DeckRibbonLargeButton";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

type Props = {
  slides: Slide[];
  selectedSlide: Slide | null;
  onAdd: () => void;
  onSelect: (slideId: string) => void;
  onDuplicate: (slide: Slide) => void;
  onToggleActive: (slide: Slide) => void;
  onRemove: (slide: Slide) => void;
  onExportPng?: () => void;
  onExportPdf?: () => void;
  onExportPptx?: () => void;
  exportBusy?: boolean;
  /** Controles da programação/TV na ribbon; nome/status vão à barra superior. */
  playlistChrome?: DeckHomePlaylistChromeProps;
};

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const K = DECK_HOME_ACTION_KEYTIPS;

export function SlideDeckRibbon({
  slides,
  selectedSlide,
  onAdd,
  onSelect,
  onDuplicate,
  onToggleActive,
  onRemove,
  onExportPng,
  onExportPdf,
  onExportPptx,
  exportBusy = false,
  playlistChrome,
}: Props) {
  const selectedIndex = selectedSlide
    ? slides.findIndex((slide) => slide.id === selectedSlide.id)
    : -1;

  function goTo(offset: number) {
    if (!slides.length) return;
    const base = selectedIndex >= 0 ? selectedIndex : 0;
    const next = (base + offset + slides.length) % slides.length;
    onSelect(slides[next]!.id);
  }

  return (
    <div className="td-deck-ribbon__groups">
      {playlistChrome ? <DeckHomePlaylistChrome {...playlistChrome} /> : null}

      <DeckRibbonGroup label="Slides" hint={H.slides}>
        <div className="td-deck-ribbon__split">
          <DeckRibbonLargeButton
            icon={Plus}
            label="Nova tela"
            hint={H.newSlide}
            primary
            keyTip={K.newSlide}
            onClick={onAdd}
          />
          <div className="td-deck-ribbon__slide-nav" role="group" aria-label="Trocar slide">
            <DeckKeyTip letter={K.prevSlide} scope="actions">
              <HintAction hint={H.prevSlide} ariaLabel="Ajuda: Anterior">
                <button
                  type="button"
                  className="td-btn td-btn--sm td-btn--icon td-deck-ribbon__slide-nav-btn"
                  disabled={slides.length < 2}
                  onClick={() => goTo(-1)}
                  aria-label="Slide anterior"
                >
                  <ChevronLeft size={16} aria-hidden="true" />
                </button>
              </HintAction>
            </DeckKeyTip>
            <span className="td-deck-ribbon__counter" aria-live="polite">
              {slides.length ? `${Math.max(selectedIndex, 0) + 1} / ${slides.length}` : "0 / 0"}
            </span>
            <DeckKeyTip letter={K.nextSlide} scope="actions">
              <HintAction hint={H.nextSlide} ariaLabel="Ajuda: Próximo">
                <button
                  type="button"
                  className="td-btn td-btn--sm td-btn--icon td-deck-ribbon__slide-nav-btn"
                  disabled={slides.length < 2}
                  onClick={() => goTo(1)}
                  aria-label="Próximo slide"
                >
                  <ChevronRight size={16} aria-hidden="true" />
                </button>
              </HintAction>
            </DeckKeyTip>
          </div>
        </div>
      </DeckRibbonGroup>

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
                hint="Exportar a tela atual como PowerPoint editável (MVP)."
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
