import { ChevronLeft, ChevronRight, Clapperboard } from "lucide-react";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type MouseEvent,
} from "react";

import type { PlaylistMasterConfig, PresentationPayload, Slide } from "../api/tvDashboardApi";
import { useDeckSidePanelLayout } from "../hooks/useDeckSidePanelLayout";
import { useDragEdgeAutoScroll } from "../hooks/useDragEdgeAutoScroll";
import { SlideCardThumbnail } from "./SlideCardThumbnail";
import { SlideFilmstripContextMenu } from "./SlideFilmstripContextMenu";
import { SlideFilmstripControls } from "./SlideFilmstripControls";

type Props = {
  slides: Slide[];
  playlistId: string;
  selectedSlideId: string | null;
  previewBySlideId: Record<string, PresentationPayload["slides"][number]>;
  dragIndex: number | null;
  inactiveLabel?: string;
  canPasteSlide: boolean;
  viewportProfile?: string;
  masterConfig?: PlaylistMasterConfig;
  onSelect: (slideId: string) => void;
  onDragStart: (index: number) => void;
  onDrop: (index: number) => void;
  onDragEnd: () => void;
  onAdd: () => void;
  onCopy: (slide: Slide) => void;
  onPaste: () => void;
  onDuplicate: (slide: Slide) => void;
  onRename: (slide: Slide, title: string) => void;
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
  masterConfig,
  onSelect,
  onDragStart,
  onDrop,
  onDragEnd,
  onAdd,
  onCopy,
  onPaste,
  onDuplicate,
  onRename,
  onToggleActive,
  onRemove,
}: Props) {
  const { collapsed, toggleCollapsed, setCollapsed, startResize, panelWidthPx, limits } =
    useDeckSidePanelLayout("filmstrip", { growDirection: "east" });
  const [contextMenu, setContextMenu] = useState<{
    slide: Slide;
    x: number;
    y: number;
  } | null>(null);
  const [renamingSlideId, setRenamingSlideId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const renameInputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLOListElement>(null);
  const skipBlurCommitRef = useRef(false);

  useDragEdgeAutoScroll(listRef, dragIndex != null);

  const closeContextMenu = useCallback(() => setContextMenu(null), []);

  const beginRename = useCallback(
    (slide: Slide) => {
      skipBlurCommitRef.current = false;
      setRenamingSlideId(slide.id);
      setRenameDraft(slide.title);
      onSelect(slide.id);
    },
    [onSelect],
  );

  const cancelRename = useCallback(() => {
    skipBlurCommitRef.current = true;
    setRenamingSlideId(null);
    setRenameDraft("");
  }, []);

  const commitRename = useCallback(
    (slide: Slide) => {
      if (skipBlurCommitRef.current) {
        skipBlurCommitRef.current = false;
        return;
      }
      const next = renameDraft.trim();
      setRenamingSlideId(null);
      setRenameDraft("");
      if (!next || next === slide.title) return;
      onRename(slide, next);
    },
    [onRename, renameDraft],
  );

  useEffect(() => {
    if (!renamingSlideId) return;
    const el = renameInputRef.current;
    if (!el) return;
    el.focus();
    el.select();
  }, [renamingSlideId]);

  const handleContextMenu = useCallback((event: MouseEvent, slide: Slide) => {
    event.preventDefault();
    /* Direito só abre opções — seleção de tela fica no clique esquerdo. */
    setContextMenu({ slide, x: event.clientX, y: event.clientY });
  }, []);

  const onRenameKeyDown = (event: KeyboardEvent<HTMLInputElement>, slide: Slide) => {
    if (event.key === "Enter") {
      event.preventDefault();
      commitRename(slide);
    }
    if (event.key === "Escape") {
      event.preventDefault();
      cancelRename();
    }
  };

  const shellStyle = {
    "--td-filmstrip-width": `${panelWidthPx}px`,
  } as CSSProperties;

  return (
    <>
      <div
        className={`td-deck-filmstrip-shell${collapsed ? " td-deck-filmstrip-shell--collapsed" : ""}`}
        style={shellStyle}
      >
        {collapsed ? (
          <aside className="td-deck-filmstrip td-deck-filmstrip--collapsed" aria-label="Slides da programação">
            <button
              type="button"
              className="td-deck-filmstrip__reopen"
              onClick={() => setCollapsed(false)}
              aria-label="Expandir lista de slides"
              title="Expandir slides"
            >
              <ChevronRight size={18} aria-hidden="true" />
            </button>
            <span className="td-deck-filmstrip__rail-icon" aria-hidden="true">
              <Clapperboard size={16} />
            </span>
            <span className="td-deck-filmstrip__rail-count" title={`${slides.length} telas`}>
              {slides.length}
            </span>
          </aside>
        ) : (
          <aside className="td-deck-filmstrip" aria-label="Slides da programação">
            <div className="td-deck-filmstrip__toolbar">
              <span className="td-deck-filmstrip__toolbar-label">Slides</span>
              <button
                type="button"
                className="td-deck-filmstrip__collapse"
                onClick={toggleCollapsed}
                aria-label="Recolher lista de slides"
                title="Recolher"
              >
                <ChevronLeft size={16} aria-hidden="true" />
              </button>
            </div>
            <SlideFilmstripControls onAdd={onAdd} />
            {slides.length === 0 ? (
              <p className="td-deck-filmstrip__empty">Nenhuma tela na programação.</p>
            ) : (
              <ol
                ref={listRef}
                className="td-deck-filmstrip__list"
                onDragOver={(event) => {
                  /* Mantém drop permitido na lista e alimenta o auto-scroll das bordas. */
                  event.preventDefault();
                }}
              >
                {slides.map((slide, index) => {
                  const selected = slide.id === selectedSlideId;
                  const renaming = renamingSlideId === slide.id;
                  return (
                    <li
                      key={slide.id}
                      className={`td-deck-filmstrip__item${selected ? " td-deck-filmstrip__item--selected" : ""}${!slide.isActive ? " td-deck-filmstrip__item--inactive" : ""}${dragIndex === index ? " td-deck-filmstrip__item--dragging" : ""}`}
                      draggable={!renaming}
                      onDragStart={() => {
                        if (renaming) return;
                        onDragStart(index);
                      }}
                      onDragOver={(event) => event.preventDefault()}
                      onDrop={() => onDrop(index)}
                      onDragEnd={onDragEnd}
                    >
                      <div
                        className="td-deck-filmstrip__select"
                        aria-current={selected ? "true" : undefined}
                      >
                        <button
                          type="button"
                          className="td-deck-filmstrip__thumb-btn"
                          onClick={() => onSelect(slide.id)}
                          onDoubleClick={(event) => {
                            event.preventDefault();
                            beginRename(slide);
                          }}
                          onContextMenu={(event) => handleContextMenu(event, slide)}
                          aria-label={`Tela ${index + 1}: ${slide.title}`}
                        >
                          <span className="td-deck-filmstrip__index">{index + 1}</span>
                          <SlideCardThumbnail
                            slide={slide}
                            playlistId={playlistId}
                            previewSlide={previewBySlideId[slide.id]}
                            viewportProfile={viewportProfile}
                            masterConfig={masterConfig}
                          />
                        </button>
                        {renaming ? (
                          <input
                            ref={renameInputRef}
                            className="td-deck-filmstrip__title-input"
                            value={renameDraft}
                            aria-label={`Renomear tela ${index + 1}`}
                            onChange={(event) => setRenameDraft(event.target.value)}
                            onBlur={() => commitRename(slide)}
                            onKeyDown={(event) => onRenameKeyDown(event, slide)}
                          />
                        ) : (
                          <button
                            type="button"
                            className="td-deck-filmstrip__title"
                            title="Duplo clique para renomear"
                            onClick={() => onSelect(slide.id)}
                            onDoubleClick={(event) => {
                              event.preventDefault();
                              beginRename(slide);
                            }}
                            onContextMenu={(event) => handleContextMenu(event, slide)}
                          >
                            {slide.title}
                          </button>
                        )}
                        {!slide.isActive ? (
                          <span className="td-deck-filmstrip__badge">{inactiveLabel}</span>
                        ) : null}
                      </div>
                    </li>
                  );
                })}
              </ol>
            )}
          </aside>
        )}
        {!collapsed ? (
          <div
            className="td-deck-panel-resize td-deck-panel-resize--east"
            role="separator"
            aria-orientation="vertical"
            aria-label="Redimensionar lista de slides"
            aria-valuenow={panelWidthPx}
            aria-valuemin={limits.minWidth}
            aria-valuemax={limits.maxWidth}
            onPointerDown={startResize}
          />
        ) : null}
      </div>

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
          onRename={() => beginRename(contextMenu.slide)}
          onToggleActive={() => onToggleActive(contextMenu.slide)}
          onRemove={() => onRemove(contextMenu.slide)}
        />
      ) : null}
    </>
  );
}
