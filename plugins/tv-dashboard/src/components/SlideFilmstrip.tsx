import type { PresentationPayload, Slide } from "../api/tvDashboardApi";
import { SlideCardThumbnail } from "./SlideCardThumbnail";

type Props = {
  slides: Slide[];
  playlistId: string;
  selectedSlideId: string | null;
  previewBySlideId: Record<string, PresentationPayload["slides"][number]>;
  dragIndex: number | null;
  inactiveLabel?: string;
  onSelect: (slideId: string) => void;
  onDragStart: (index: number) => void;
  onDrop: (index: number) => void;
  onDragEnd: () => void;
};

export function SlideFilmstrip({
  slides,
  playlistId,
  selectedSlideId,
  previewBySlideId,
  dragIndex,
  inactiveLabel = "Pausada",
  onSelect,
  onDragStart,
  onDrop,
  onDragEnd,
}: Props) {
  return (
    <aside className="td-deck-filmstrip" aria-label="Slides da programação">
      {slides.length === 0 ? (
        <p className="td-deck-filmstrip__empty">Nenhuma tela na programação.</p>
      ) : (
        <ol className="td-deck-filmstrip__list">
          {slides.map((slide, index) => {
            const selected = slide.id === selectedSlideId;
            return (
              <li
                key={slide.id}
                className={`td-deck-filmstrip__item${selected ? " td-deck-filmstrip__item--selected" : ""}${!slide.isActive ? " td-deck-filmstrip__item--inactive" : ""}${dragIndex === index ? " td-deck-filmstrip__item--dragging" : ""}`}
                draggable
                onDragStart={() => onDragStart(index)}
                onDragOver={(event) => event.preventDefault()}
                onDrop={() => onDrop(index)}
                onDragEnd={onDragEnd}
              >
                <button
                  type="button"
                  className="td-deck-filmstrip__select"
                  onClick={() => onSelect(slide.id)}
                  aria-current={selected ? "true" : undefined}
                  aria-label={`Tela ${index + 1}: ${slide.title}`}
                >
                  <span className="td-deck-filmstrip__index">{index + 1}</span>
                  <SlideCardThumbnail
                    slide={slide}
                    playlistId={playlistId}
                    previewSlide={previewBySlideId[slide.id]}
                  />
                  <span className="td-deck-filmstrip__title">{slide.title}</span>
                  {!slide.isActive ? (
                    <span className="td-deck-filmstrip__badge">{inactiveLabel}</span>
                  ) : null}
                </button>
              </li>
            );
          })}
        </ol>
      )}
    </aside>
  );
}
