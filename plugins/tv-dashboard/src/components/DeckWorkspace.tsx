import { type ReactNode } from "react";

import type { PresentationPayload, Slide } from "../api/tvDashboardApi";
import { SlideFilmstrip } from "./SlideFilmstrip";

type Props = {
  slides: Slide[];
  playlistId: string;
  selectedSlideId: string | null;
  previewBySlideId: Record<string, PresentationPayload["slides"][number]>;
  dragIndex: number | null;
  inactiveLabel: string;
  canPasteSlide: boolean;
  viewportProfile?: string;
  onSelect: (slideId: string) => void;
  onDragStart: (index: number) => void;
  onDrop: (index: number) => void;
  onDragEnd: () => void;
  onAdd: () => void;
  onCopySlide: (slide: Slide) => void;
  onPasteSlide: () => void;
  onDuplicateSlide: (slide: Slide) => void;
  onToggleSlideActive: (slide: Slide) => void;
  onRemoveSlide: (slide: Slide) => void;
  stage: ReactNode;
  rightPanel?: ReactNode;
};

export function DeckWorkspace({
  slides,
  playlistId,
  selectedSlideId,
  previewBySlideId,
  dragIndex,
  inactiveLabel,
  canPasteSlide,
  viewportProfile = "1080p",
  onSelect,
  onDragStart,
  onDrop,
  onDragEnd,
  onAdd,
  onCopySlide,
  onPasteSlide,
  onDuplicateSlide,
  onToggleSlideActive,
  onRemoveSlide,
  stage,
  rightPanel,
}: Props) {
  return (
    <div className="td-deck__workspace">
      <SlideFilmstrip
        slides={slides}
        playlistId={playlistId}
        selectedSlideId={selectedSlideId}
        previewBySlideId={previewBySlideId}
        dragIndex={dragIndex}
        inactiveLabel={inactiveLabel}
        canPasteSlide={canPasteSlide}
        viewportProfile={viewportProfile}
        onSelect={onSelect}
        onDragStart={onDragStart}
        onDrop={onDrop}
        onDragEnd={onDragEnd}
        onAdd={onAdd}
        onCopy={onCopySlide}
        onPaste={onPasteSlide}
        onDuplicate={onDuplicateSlide}
        onToggleActive={onToggleSlideActive}
        onRemove={onRemoveSlide}
      />
      <main className="td-deck-stage" aria-label="Palco da tela selecionada">
        <div className="td-deck-stage__inner">
          <div className="td-deck-stage__main">{stage}</div>
          {rightPanel}
        </div>
      </main>
    </div>
  );
}
