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
  exportBusy?: boolean;
};

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

export function SlideDeckRibbon({
  slides,
  selectedSlide,
  onAdd,
  onSelect,
  onDuplicate,
  onToggleActive,
  onRemove,
  onExportPng,
  exportBusy = false,
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
      <DeckRibbonGroup label="Slides" hint={H.slides}>
        <div className="td-deck-ribbon__split">
          <DeckRibbonLargeButton
            icon={Plus}
            label="Nova tela"
            hint={H.newSlide}
            primary
            onClick={onAdd}
          />
          <div className="td-deck-ribbon__slide-nav" role="group" aria-label="Trocar slide">
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
            <span className="td-deck-ribbon__counter" aria-live="polite">
              {slides.length ? `${Math.max(selectedIndex, 0) + 1} / ${slides.length}` : "0 / 0"}
            </span>
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
              onClick={() => onToggleActive(selectedSlide)}
            />
            <DeckRibbonTile
              icon={Copy}
              label="Duplicar"
              hint={H.duplicate}
              onClick={() => onDuplicate(selectedSlide)}
            />
            {onExportPng ? (
              <DeckRibbonTile
                icon={Download}
                label={exportBusy ? "…" : "PNG"}
                hint="Exportar a tela atual como PNG (4E.5)."
                disabled={exportBusy}
                onClick={onExportPng}
              />
            ) : null}
            <DeckRibbonTile
              icon={Trash2}
              label="Excluir"
              hint={H.delete}
              onClick={() => onRemove(selectedSlide)}
            />
          </div>
        </DeckRibbonGroup>
      ) : null}
    </div>
  );
}
