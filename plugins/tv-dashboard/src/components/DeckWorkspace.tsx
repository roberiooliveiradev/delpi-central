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
  onSelect: (slideId: string) => void;
  onDragStart: (index: number) => void;
  onDrop: (index: number) => void;
  onDragEnd: () => void;
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
  onSelect,
  onDragStart,
  onDrop,
  onDragEnd,
  stage,
  rightPanel,
}: Props) {
  return (
    <div
      className={[
        "td-deck__workspace",
        rightPanel ? null : "td-deck__workspace--wide",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <SlideFilmstrip
        slides={slides}
        playlistId={playlistId}
        selectedSlideId={selectedSlideId}
        previewBySlideId={previewBySlideId}
        dragIndex={dragIndex}
        inactiveLabel={inactiveLabel}
        onSelect={onSelect}
        onDragStart={onDragStart}
        onDrop={onDrop}
        onDragEnd={onDragEnd}
      />
      <main className="td-deck-stage" aria-label="Palco da tela selecionada">
        {stage}
      </main>
      {rightPanel}
    </div>
  );
}
