import {
  ChevronLeft,
  ChevronRight,
  Copy,
  Eye,
  EyeOff,
  Plus,
  Trash2,
} from "lucide-react";

import type { Slide } from "../api/tvDashboardApi";

type Props = {
  slides: Slide[];
  selectedSlide: Slide | null;
  onAdd: () => void;
  onSelect: (slideId: string) => void;
  onDuplicate: (slide: Slide) => void;
  onToggleActive: (slide: Slide) => void;
  onRemove: (slide: Slide) => void;
};

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
        <span className="td-deck-ribbon__label">Slides</span>
        <div className="td-deck-ribbon__controls">
          <button type="button" className="td-btn td-btn--primary td-btn--sm" onClick={onAdd}>
            <Plus size={15} />
            Nova tela
          </button>
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={slides.length < 2}
            onClick={() => goTo(-1)}
            aria-label="Slide anterior"
          >
            <ChevronLeft size={15} />
          </button>
          <span className="td-deck-ribbon__counter">
            {slides.length ? `${selectedIndex + 1} / ${slides.length}` : "0 / 0"}
          </span>
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={slides.length < 2}
            onClick={() => goTo(1)}
            aria-label="Próximo slide"
          >
            <ChevronRight size={15} />
          </button>
        </div>
      </div>

      {selectedSlide ? (
        <div className="td-deck-ribbon__group">
          <span className="td-deck-ribbon__label">Tela atual</span>
          <div className="td-deck-ribbon__controls">
            <button
              type="button"
              className="td-btn td-btn--sm"
              onClick={() => onToggleActive(selectedSlide)}
            >
              {selectedSlide.isActive ? <Eye size={15} /> : <EyeOff size={15} />}
              {selectedSlide.isActive ? "Pausar" : "Ativar"}
            </button>
            <button type="button" className="td-btn td-btn--sm" onClick={() => onDuplicate(selectedSlide)}>
              <Copy size={15} />
              Duplicar
            </button>
            <button
              type="button"
              className="td-btn td-btn--danger td-btn--sm"
              onClick={() => onRemove(selectedSlide)}
            >
              <Trash2 size={15} />
              Excluir
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
