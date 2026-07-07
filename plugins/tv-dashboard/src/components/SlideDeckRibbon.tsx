import {
  ChevronLeft,
  ChevronRight,
  Copy,
  Eye,
  EyeOff,
  Plus,
  Trash2,
} from "lucide-react";
import { HintAction, SectionHintLabel } from "@delpi/plugin-ui";

import type { Slide } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";

type Props = {
  slides: Slide[];
  selectedSlide: Slide | null;
  onAdd: () => void;
  onSelect: (slideId: string) => void;
  onDuplicate: (slide: Slide) => void;
  onToggleActive: (slide: Slide) => void;
  onRemove: (slide: Slide) => void;
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
}: Props) {
  const selectedIndex = selectedSlide
    ? slides.findIndex((slide) => slide.id === selectedSlide.id)
    : -1;

  function goTo(offset: number) {
    if (!slides.length) return;
    const base = selectedIndex >= 0 ? selectedIndex : 0;
    const next = (base + offset + slides.length) % slides.length;
    onSelect(slides[next].id);
  }

  return (
    <div className="td-deck-ribbon__groups">
      <div className="td-deck-ribbon__group">
        <SectionHintLabel label="Slides" hint={H.slides} className="td-deck-ribbon__label" />
        <div className="td-deck-ribbon__controls">
          <HintAction hint={H.newSlide} ariaLabel="Ajuda: Nova tela">
            <button type="button" className="td-btn td-btn--primary td-btn--sm" onClick={onAdd}>
              <Plus size={15} aria-hidden="true" />
              Nova tela
            </button>
          </HintAction>
          <HintAction hint={H.prevSlide} ariaLabel="Ajuda: Anterior">
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--icon"
              disabled={slides.length < 2}
              onClick={() => goTo(-1)}
              aria-label="Slide anterior"
            >
              <ChevronLeft size={15} aria-hidden="true" />
            </button>
          </HintAction>
          <span className="td-deck-ribbon__counter">
            {slides.length ? `${selectedIndex + 1} / ${slides.length}` : "0 / 0"}
          </span>
          <HintAction hint={H.nextSlide} ariaLabel="Ajuda: Próximo">
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--icon"
              disabled={slides.length < 2}
              onClick={() => goTo(1)}
              aria-label="Próximo slide"
            >
              <ChevronRight size={15} aria-hidden="true" />
            </button>
          </HintAction>
        </div>
      </div>

      {selectedSlide ? (
        <div className="td-deck-ribbon__group">
          <SectionHintLabel label="Tela atual" hint={H.currentSlide} className="td-deck-ribbon__label" />
          <div className="td-deck-ribbon__controls">
            <HintAction
              hint={selectedSlide.isActive ? H.pause : H.activate}
              ariaLabel={selectedSlide.isActive ? "Ajuda: Pausar" : "Ajuda: Ativar"}
            >
              <button
                type="button"
                className="td-btn td-btn--sm"
                onClick={() => onToggleActive(selectedSlide)}
              >
                {selectedSlide.isActive ? <Eye size={15} aria-hidden="true" /> : <EyeOff size={15} aria-hidden="true" />}
                {selectedSlide.isActive ? "Pausar" : "Ativar"}
              </button>
            </HintAction>
            <HintAction hint={H.duplicate} ariaLabel="Ajuda: Duplicar">
              <button type="button" className="td-btn td-btn--sm" onClick={() => onDuplicate(selectedSlide)}>
                <Copy size={15} aria-hidden="true" />
                Duplicar
              </button>
            </HintAction>
            <HintAction hint={H.delete} ariaLabel="Ajuda: Excluir">
              <button
                type="button"
                className="td-btn td-btn--danger td-btn--sm"
                onClick={() => onRemove(selectedSlide)}
              >
                <Trash2 size={15} aria-hidden="true" />
                Excluir
              </button>
            </HintAction>
          </div>
        </div>
      ) : null}
    </div>
  );
}
