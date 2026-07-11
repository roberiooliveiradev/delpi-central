import { useCallback, useState, type MouseEvent } from "react";

import type { PresentationPayload, Slide } from "../api/tvDashboardApi";
import { SlideCardThumbnail } from "./SlideCardThumbnail";
import { SlideFilmstripContextMenu } from "./SlideFilmstripContextMenu";

type Props = {
  slides: Slide[];
  playlistId: string;
  selectedSlideId: string | null;
  previewBySlideId: Record<string, PresentationPayload["slides"][number]>;
  dragIndex: number | null;
  inactiveLabel?: string;
  canPasteSlide: boolean;
  viewportProfile?: string;
  onSelect: (slideId: string) => void;
  onDragStart: (index: number) => void;
  onDrop: (index: number) => void;
  onDragEnd: () => void;
  onAdd: () => void;
  onCopy: (slide: Slide) => void;
  onPaste: () => void;
  onDuplicate: (slide: Slide) => void;
  onToggleActive: (slide: Slide) => void;
  onRemove: (slide: Slide) => void;
};

export function SlideFilmstrip({
  slides,
  playlistId,
  selectedSlideId,
  previewBySlideId,
  dragIndex,
  inactiveLabel = "Pausada",
  canPasteSlide,
  viewportProfile = "1080p",
  onSelect,
  onDragStart,
  onDrop,
  onDragEnd,
  onAdd,
  onCopy,
  onPaste,
  onDuplicate,
  onToggleActive,
  onRemove,
}: Props) {
  const [contextMenu, setContextMenu] = useState<{
    slide: Slide;
    x: number;
    y: number;
  } | null>(null);

  const closeContextMenu = useCallback(() => setContextMenu(null), []);

  const handleContextMenu = useCallback((event: MouseEvent, slide: Slide) => {
    event.preventDefault();
    onSelect(slide.id);
    setContextMenu({ slide, x: event.clientX, y: event.clientY });
  }, [onSelect]);

  return (
    <>
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
                    onContextMenu={(event) => handleContextMenu(event, slide)}
                    aria-current={selected ? "true" : undefined}
                    aria-label={`Tela ${index + 1}: ${slide.title}`}
                  >
                    <span className="td-deck-filmstrip__index">{index + 1}</span>
                    <SlideCardThumbnail
                      slide={slide}
                      playlistId={playlistId}
                      previewSlide={previewBySlideId[slide.id]}
                      viewportProfile={viewportProfile}
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

      {contextMenu ? (
        <SlideFilmstripContextMenu
          open
          position={{ x: contextMenu.x, y: contextMenu.y }}
          slideTitle={contextMenu.slide.title}
          slideActive={contextMenu.slide.isActive}
          canPaste={canPasteSlide}
          onClose={closeContextMenu}
          onCopy={() => onCopy(contextMenu.slide)}
          onPaste={onPaste}
          onDuplicate={() => onDuplicate(contextMenu.slide)}
          onAdd={onAdd}
          onToggleActive={() => onToggleActive(contextMenu.slide)}
          onRemove={() => onRemove(contextMenu.slide)}
        />
      ) : null}
    </>
  );
}
