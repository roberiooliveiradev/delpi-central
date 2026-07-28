import { type ReactNode } from "react";

import type { PlaylistMasterConfig, PlaylistSection, PresentationPayload, Slide } from "../api/tvDashboardApi";
import { SlideFilmstrip } from "./SlideFilmstrip";

type Props = {
  slides: Slide[];
  sections?: PlaylistSection[];
  playlistId: string;
  selectedSlideId: string | null;
  previewBySlideId: Record<string, PresentationPayload["slides"][number]>;
  dragIndex: number | null;
  inactiveLabel: string;
  canPasteSlide: boolean;
  viewportProfile?: string;
  masterConfig?: PlaylistMasterConfig;
  publicToken?: string | null;
  onSelect: (slideId: string) => void;
  onDragStart: (index: number) => void;
  onDrop: (index: number) => void;
  onDragEnd: () => void;
  onAdd: () => void;
  onAddSection?: () => void;
  onCreateSection?: (slide: Slide) => void;
  onAddInSection?: (sectionId: string) => void;
  onCopySlide: (slide: Slide) => void;
  onPasteSlide: () => void;
  onDuplicateSlide: (slide: Slide) => void;
  onRenameSlide: (slide: Slide, title: string) => void;
  onToggleSlideActive: (slide: Slide) => void;
  onRemoveSlide: (slide: Slide) => void;
  onSectionNameCommit?: (sectionId: string, name: string) => void;
  onSectionToggleCollapsed?: (sectionId: string, collapsed: boolean) => void;
  onSectionToggleActive?: (sectionId: string, active: boolean) => void;
  onSectionDelete?: (sectionId: string, deleteSlides: boolean) => void;
  onSectionProperties?: (sectionId: string) => void;
  onDropOnSection?: (sectionId: string) => void;
  onDropOnUnsectioned?: () => void;
  stage: ReactNode;
  rightPanel?: ReactNode;
};

export function DeckWorkspace({
  slides,
  sections,
  playlistId,
  selectedSlideId,
  previewBySlideId,
  dragIndex,
  inactiveLabel,
  canPasteSlide,
  viewportProfile = "1080p",
  masterConfig,
  publicToken,
  onSelect,
  onDragStart,
  onDrop,
  onDragEnd,
  onAdd,
  onAddSection,
  onCreateSection,
  onAddInSection,
  onCopySlide,
  onPasteSlide,
  onDuplicateSlide,
  onRenameSlide,
  onToggleSlideActive,
  onRemoveSlide,
  onSectionNameCommit,
  onSectionToggleCollapsed,
  onSectionToggleActive,
  onSectionDelete,
  onSectionProperties,
  onDropOnSection,
  onDropOnUnsectioned,
  stage,
  rightPanel,
}: Props) {
  return (
    <div className="td-deck__workspace">
      <SlideFilmstrip
        slides={slides}
        sections={sections}
        playlistId={playlistId}
        selectedSlideId={selectedSlideId}
        previewBySlideId={previewBySlideId}
        dragIndex={dragIndex}
        inactiveLabel={inactiveLabel}
        canPasteSlide={canPasteSlide}
        viewportProfile={viewportProfile}
        masterConfig={masterConfig}
        publicToken={publicToken}
        onSelect={onSelect}
        onDragStart={onDragStart}
        onDrop={onDrop}
        onDragEnd={onDragEnd}
        onAdd={onAdd}
        onAddSection={onAddSection}
        onCreateSection={onCreateSection}
        onAddInSection={onAddInSection}
        onCopy={onCopySlide}
        onPaste={onPasteSlide}
        onDuplicate={onDuplicateSlide}
        onRename={onRenameSlide}
        onToggleActive={onToggleSlideActive}
        onRemove={onRemoveSlide}
        onSectionNameCommit={onSectionNameCommit}
        onSectionToggleCollapsed={onSectionToggleCollapsed}
        onSectionToggleActive={onSectionToggleActive}
        onSectionDelete={onSectionDelete}
        onSectionProperties={onSectionProperties}
        onDropOnSection={onDropOnSection}
        onDropOnUnsectioned={onDropOnUnsectioned}
      />
      <main className="td-deck-stage" aria-label="Palco da tela selecionada">
        <div className="td-deck-stage__inner">
          <div className="td-deck-stage__main">{stage}</div>
          {rightPanel ? (
            <div className="td-deck-stage__aside-slot">{rightPanel}</div>
          ) : null}
        </div>
      </main>
    </div>
  );
}
