import {
  DeckSectionContextMenu,
  DeckSectionList,
  type DeckSectionContextMenuAction,
} from "@delpi/plugin-ui/index";
import { ChevronLeft, ChevronRight, Clapperboard } from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type MouseEvent,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from "react";

import type {
  PlaylistMasterConfig,
  PlaylistSection,
  PresentationPayload,
  Slide,
} from "../api/tvDashboardApi";
import { useDeckSidePanelLayout } from "../hooks/useDeckSidePanelLayout";
import { useDragEdgeAutoScroll } from "../hooks/useDragEdgeAutoScroll";
import { groupSlidesBySection } from "../utils/groupSlidesBySection";
import { buildPresentationOrderIndexBySlideId } from "../utils/presentationSlideOrder";
import { shouldShowSectionChrome, shouldShowSectionInFilmstrip } from "../utils/sectionChromeVisibility";
import type { FilmstripSelectionModifiers } from "../utils/filmstripSlideSelection";
import {
  attachListDragGhost,
  listDropHintClassName,
  resolveListDropEdge,
  type ListDropEdge,
  type ListDropHint,
} from "../utils/listReorderDrag";
import {
  formatSlideTransitionLabel,
  resolveSlideDurationSec,
  resolveSlideTransitionStyle,
  slideDurationIsOverride,
} from "../utils/slideTimingInheritance";
import { SlideCardThumbnail } from "./SlideCardThumbnail";
import { SlideFilmstripContextMenu } from "./SlideFilmstripContextMenu";
import { SlideFilmstripControls } from "./SlideFilmstripControls";
import { mergeMasterConfigs } from "./slideCardPreview";

const LONG_PRESS_MS = 450;
const LONG_PRESS_MOVE_PX = 8;

type Props = {
  slides: Slide[];
  sections?: PlaylistSection[];
  playlistId: string;
  selectedSlideId: string | null;
  selectedSlideIds?: string[];
  previewBySlideId: Record<string, PresentationPayload["slides"][number]>;
  dragIndex: number | null;
  dragSlideIds?: string[];
  inactiveLabel?: string;
  canPasteSlide: boolean;
  viewportProfile?: string;
  viewportWidth?: number | null;
  viewportHeight?: number | null;
  masterConfig?: PlaylistMasterConfig;
  /** Duração padrão da playlist (para badge efetivo). */
  defaultDurationSec?: number;
  /** Transição padrão da playlist (tooltip). */
  defaultTransitionStyle?: string | null;
  publicToken?: string | null;
  multiMode?: boolean;
  onSelect: (slideId: string, modifiers?: FilmstripSelectionModifiers) => void;
  onLongPressSelect?: (slideId: string) => void;
  onClearMultiSelection?: () => void;
  onDragStart: (index: number) => void;
  onDrop: (index: number, edge?: ListDropEdge) => void;
  onDragEnd: () => void;
  onAdd: () => void;
  onAddSection?: () => void;
  onCreateSection?: (slide: Slide) => void;
  onAddInSection?: (sectionId: string) => void;
  onCopy: (slide: Slide) => void;
  onPaste: () => void;
  onDuplicate: (slides: Slide[]) => void;
  onRename: (slide: Slide, title: string) => void;
  onToggleActive: (slides: Slide[]) => void;
  onRemove: (slides: Slide[]) => void;
  onSectionNameCommit?: (sectionId: string, name: string) => void;
  onSectionToggleCollapsed?: (sectionId: string, collapsed: boolean) => void;
  onSectionToggleActive?: (sectionId: string, active: boolean) => void;
  onSectionDelete?: (sectionId: string, deleteSlides: boolean) => void;
  onSectionProperties?: (sectionId: string) => void;
  onDropOnSection?: (sectionId: string) => void;
  onDropOnUnsectioned?: () => void;
};

function modifiersFromMouseEvent(event: MouseEvent): FilmstripSelectionModifiers {
  if (event.shiftKey) return { range: true };
  if (event.ctrlKey || event.metaKey) return { toggle: true };
  return {};
}

export function SlideFilmstrip({
  slides,
  sections = [],
  playlistId,
  selectedSlideId,
  selectedSlideIds,
  previewBySlideId,
  dragIndex,
  dragSlideIds,
  inactiveLabel = "Pausada",
  canPasteSlide,
  viewportProfile = "1080p",
  viewportWidth = null,
  viewportHeight = null,
  masterConfig,
  defaultDurationSec = 30,
  defaultTransitionStyle = "fade",
  publicToken,
  multiMode = false,
  onSelect,
  onLongPressSelect,
  onClearMultiSelection,
  onDragStart,
  onDrop,
  onDragEnd,
  onAdd,
  onAddSection,
  onCreateSection,
  onAddInSection,
  onCopy,
  onPaste,
  onDuplicate,
  onRename,
  onToggleActive,
  onRemove,
  onSectionNameCommit,
  onSectionToggleCollapsed,
  onSectionToggleActive,
  onSectionDelete,
  onSectionProperties,
  onDropOnSection,
}: Props) {
  const { collapsed, toggleCollapsed, setCollapsed, startResize, panelWidthPx, limits } =
    useDeckSidePanelLayout("filmstrip", { growDirection: "east" });
  const [contextMenu, setContextMenu] = useState<{
    slide: Slide;
    x: number;
    y: number;
  } | null>(null);
  const [sectionMenu, setSectionMenu] = useState<{
    sectionId: string;
    x: number;
    y: number;
  } | null>(null);
  const [renamingSlideId, setRenamingSlideId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [sectionNameDrafts, setSectionNameDrafts] = useState<Record<string, string>>({});
  const renameInputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const skipBlurCommitRef = useRef(false);
  const longPressTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const longPressOriginRef = useRef<{ x: number; y: number; slideId: string } | null>(null);
  const longPressFiredRef = useRef(false);
  const suppressClickRef = useRef(false);
  const suppressDragRef = useRef(false);

  useDragEdgeAutoScroll(listRef, dragIndex != null || (dragSlideIds?.length ?? 0) > 0);

  const closeContextMenu = useCallback(() => setContextMenu(null), []);
  const closeSectionMenu = useCallback(() => setSectionMenu(null), []);

  const selectedIdSet = useMemo(() => {
    const ids =
      selectedSlideIds && selectedSlideIds.length > 0
        ? selectedSlideIds
        : selectedSlideId
          ? [selectedSlideId]
          : [];
    return new Set(ids);
  }, [selectedSlideId, selectedSlideIds]);

  const draggingIdSet = useMemo(() => new Set(dragSlideIds ?? []), [dragSlideIds]);
  const [dropHint, setDropHint] = useState<ListDropHint | null>(null);

  const clearLongPressTimer = useCallback(() => {
    if (longPressTimerRef.current != null) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
    longPressOriginRef.current = null;
  }, []);

  useEffect(() => () => clearLongPressTimer(), [clearLongPressTimer]);

  useEffect(() => {
    if (!multiMode && selectedIdSet.size <= 1) return;
    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (renamingSlideId) return;
      onClearMultiSelection?.();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [multiMode, onClearMultiSelection, renamingSlideId, selectedIdSet.size]);

  /** Índice flat do filmstrip (drag/reorder) — inclui pausados. */
  const filmstripIndexBySlideId = useMemo(() => {
    const map = new Map<string, number>();
    slides.forEach((slide, index) => map.set(slide.id, index));
    return map;
  }, [slides]);

  /** Índice na sequência da TV (badge) — só slides visíveis no `/present/`. */
  const tvOrderIndexBySlideId = useMemo(
    () => buildPresentationOrderIndexBySlideId(slides, sections),
    [slides, sections],
  );

  const grouped = useMemo(
    () => groupSlidesBySection(slides, sections),
    [slides, sections],
  );

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

  const resolveMenuTargets = useCallback(
    (slide: Slide): Slide[] => {
      if (selectedIdSet.has(slide.id) && selectedIdSet.size > 1) {
        return slides.filter((item) => selectedIdSet.has(item.id));
      }
      return [slide];
    },
    [selectedIdSet, slides],
  );

  const handleContextMenu = useCallback(
    (event: MouseEvent, slide: Slide) => {
      event.preventDefault();
      if (!selectedIdSet.has(slide.id)) {
        onSelect(slide.id);
      }
      setContextMenu({ slide, x: event.clientX, y: event.clientY });
    },
    [onSelect, selectedIdSet],
  );

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

  const handleSelectClick = useCallback(
    (event: MouseEvent, slideId: string) => {
      if (suppressClickRef.current) {
        suppressClickRef.current = false;
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      const modifiers = modifiersFromMouseEvent(event);
      if (multiMode && !modifiers.range && !modifiers.toggle) {
        onSelect(slideId, { toggle: true });
        return;
      }
      onSelect(slideId, modifiers);
    },
    [multiMode, onSelect],
  );

  const handlePointerDown = useCallback(
    (event: ReactPointerEvent, slideId: string) => {
      if (event.button !== 0) return;
      if (renamingSlideId) return;
      clearLongPressTimer();
      longPressFiredRef.current = false;
      suppressDragRef.current = false;
      longPressOriginRef.current = { x: event.clientX, y: event.clientY, slideId };
      longPressTimerRef.current = setTimeout(() => {
        longPressTimerRef.current = null;
        longPressFiredRef.current = true;
        suppressClickRef.current = true;
        suppressDragRef.current = true;
        onLongPressSelect?.(slideId);
      }, LONG_PRESS_MS);
    },
    [clearLongPressTimer, onLongPressSelect, renamingSlideId],
  );

  const handlePointerMove = useCallback(
    (event: ReactPointerEvent) => {
      const origin = longPressOriginRef.current;
      if (!origin || longPressTimerRef.current == null) return;
      const dx = event.clientX - origin.x;
      const dy = event.clientY - origin.y;
      if (dx * dx + dy * dy > LONG_PRESS_MOVE_PX * LONG_PRESS_MOVE_PX) {
        clearLongPressTimer();
      }
    },
    [clearLongPressTimer],
  );

  const handlePointerUpOrCancel = useCallback(() => {
    clearLongPressTimer();
  }, [clearLongPressTimer]);

  const renderSlideItem = (slide: Slide): ReactNode => {
    const filmstripIndex = filmstripIndexBySlideId.get(slide.id) ?? 0;
    const tvIndex = tvOrderIndexBySlideId.get(slide.id);
    const inPresentation = tvIndex != null;
    const indexLabel = inPresentation ? String(tvIndex + 1) : "–";
    const isPrimary = slide.id === selectedSlideId;
    const inMulti = selectedIdSet.has(slide.id);
    const renaming = renamingSlideId === slide.id;
    const section = slide.sectionId
      ? sections.find((item) => item.id === slide.sectionId)
      : undefined;
    const sectionMaster = section?.masterConfig;
    const effectiveMaster = mergeMasterConfigs(masterConfig, sectionMaster);
    const durationSec = resolveSlideDurationSec({
      slideDuration: slide.durationSec,
      sectionDefault: section?.defaultDurationSec,
      playlistDefault: defaultDurationSec,
    });
    const durationOverride = slideDurationIsOverride(slide.durationSec);
    const transitionStyle = resolveSlideTransitionStyle({
      slideTransition: slide.transitionStyle,
      sectionTransition: section?.transitionStyle,
      playlistTransition: defaultTransitionStyle,
    });
    const timingTitle = `${durationSec}s · ${formatSlideTransitionLabel(transitionStyle)}${
      durationOverride || slide.transitionStyle ? " (ajuste nesta tela)" : " (herdado)"
    }`;
    const itemClass = [
      "td-deck-filmstrip__item",
      isPrimary ? "td-deck-filmstrip__item--selected" : "",
      inMulti && !isPrimary ? "td-deck-filmstrip__item--multi-selected" : "",
      !slide.isActive ? "td-deck-filmstrip__item--inactive" : "",
      draggingIdSet.has(slide.id) || dragIndex === filmstripIndex
        ? "td-deck-filmstrip__item--dragging td-reorder--source"
        : "",
      listDropHintClassName(dropHint, slide.id),
    ]
      .filter(Boolean)
      .join(" ");

    return (
      <div
        key={slide.id}
        className={itemClass}
        data-reorder-id={slide.id}
        draggable={!renaming}
        onDragStart={(event) => {
          if (renaming) return;
          if (suppressDragRef.current || longPressFiredRef.current) {
            event.preventDefault();
            suppressDragRef.current = false;
            return;
          }
          clearLongPressTimer();
          attachListDragGhost(event);
          onDragStart(filmstripIndex);
        }}
        onDragOver={(event) => {
          event.preventDefault();
          if (draggingIdSet.has(slide.id)) {
            setDropHint(null);
            return;
          }
          const edge = resolveListDropEdge(event.clientY, event.currentTarget.getBoundingClientRect());
          setDropHint((current) =>
            current?.id === slide.id && current.edge === edge ? current : { id: slide.id, edge },
          );
        }}
        onDrop={(event) => {
          event.preventDefault();
          const edge =
            dropHint?.id === slide.id
              ? dropHint.edge
              : resolveListDropEdge(event.clientY, event.currentTarget.getBoundingClientRect());
          setDropHint(null);
          onDrop(filmstripIndex, edge);
        }}
        onDragEnd={() => {
          setDropHint(null);
          onDragEnd();
        }}
      >
        <div
          className="td-deck-filmstrip__select"
          aria-current={isPrimary ? "true" : undefined}
          aria-selected={inMulti || undefined}
        >
          <button
            type="button"
            className="td-deck-filmstrip__thumb-btn"
            onClick={(event) => handleSelectClick(event, slide.id)}
            onPointerDown={(event) => handlePointerDown(event, slide.id)}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUpOrCancel}
            onPointerCancel={handlePointerUpOrCancel}
            onDoubleClick={(event) => {
              event.preventDefault();
              beginRename(slide);
            }}
            onContextMenu={(event) => handleContextMenu(event, slide)}
            aria-label={inPresentation ? `Tela ${indexLabel} (ordem TV): ${slide.title}` : `Tela fora da TV: ${slide.title}`}
          >
            <span className="td-deck-filmstrip__index" title={inPresentation ? "Ordem na TV" : "Fora da apresentação"}>{indexLabel}</span>
            <SlideCardThumbnail
              slide={slide}
              playlistId={playlistId}
              previewSlide={previewBySlideId[slide.id]}
              viewportProfile={viewportProfile}
              viewportWidth={viewportWidth}
              viewportHeight={viewportHeight}
              masterConfig={effectiveMaster}
              publicToken={publicToken}
            />
          </button>
          {renaming ? (
            <input
              ref={renameInputRef}
              className="td-deck-filmstrip__title-input"
              value={renameDraft}
              aria-label={`Renomear tela ${slide.title}`}
              onChange={(event) => setRenameDraft(event.target.value)}
              onBlur={() => commitRename(slide)}
              onKeyDown={(event) => onRenameKeyDown(event, slide)}
            />
          ) : (
            <button
              type="button"
              className="td-deck-filmstrip__title"
              title="Duplo clique para renomear"
              onClick={(event) => handleSelectClick(event, slide.id)}
              onPointerDown={(event) => handlePointerDown(event, slide.id)}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUpOrCancel}
              onPointerCancel={handlePointerUpOrCancel}
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
          <span
            className={[
              "td-deck-filmstrip__timing",
              durationOverride ? "td-deck-filmstrip__timing--override" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            title={timingTitle}
          >
            {durationSec}s
          </span>
        </div>
      </div>
    );
  };

  const sectionMenuTarget = sectionMenu
    ? sections.find((section) => section.id === sectionMenu.sectionId)
    : null;

  const handleSectionMenuAction = (action: DeckSectionContextMenuAction) => {
    if (!sectionMenuTarget) return;
    const id = sectionMenuTarget.id;
    if (action === "add-slide") {
      onAddInSection?.(id);
      return;
    }
    if (action === "rename") {
      /* foco no input do header — o usuário edita o nome inline */
      return;
    }
    if (action === "properties") {
      onSectionProperties?.(id);
      return;
    }
    if (action === "toggle-active") {
      onSectionToggleActive?.(id, !(sectionMenuTarget.isActive !== false));
      return;
    }
    if (action === "collapse") {
      onSectionToggleCollapsed?.(id, true);
      return;
    }
    if (action === "expand") {
      onSectionToggleCollapsed?.(id, false);
      return;
    }
    if (action === "delete-section") {
      onSectionDelete?.(id, false);
      return;
    }
    if (action === "delete-section-and-slides") {
      onSectionDelete?.(id, true);
    }
  };

  const shellStyle = {
    "--td-filmstrip-width": `${panelWidthPx}px`,
  } as CSSProperties;

  const showSectionChrome = shouldShowSectionChrome(sections);

  const listBody =
    slides.length === 0 && sections.length === 0 ? (
      <p className="td-deck-filmstrip__empty">Nenhuma tela na programação.</p>
    ) : !showSectionChrome ? (
      <div
        ref={listRef}
        className="td-deck-filmstrip__list"
        role="list"
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={(event) => {
          const next = event.relatedTarget;
          if (next instanceof Node && event.currentTarget.contains(next)) return;
          setDropHint(null);
        }}
      >
        {slides.map((slide) => renderSlideItem(slide))}
      </div>
    ) : (
      <div
        ref={listRef}
        className="td-deck-filmstrip__list"
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={(event) => {
          const next = event.relatedTarget;
          if (next instanceof Node && event.currentTarget.contains(next)) return;
          setDropHint(null);
        }}
      >
        <DeckSectionList
          prefix="td"
          emptyDropHint="Solte telas aqui"
          sections={grouped.sections
            .filter(({ section, slides: sectionSlides }) =>
              shouldShowSectionInFilmstrip(section, sectionSlides.length),
            )
            .map(({ section, slides: sectionSlides }) => ({
              id: section.id,
              name: sectionNameDrafts[section.id] ?? section.name,
              collapsed: Boolean(section.isCollapsed),
              inactive: section.isActive === false,
              slideCount: sectionSlides.length,
              children: sectionSlides.map((slide) => renderSlideItem(slide)),
            }))}
          onToggleCollapsed={(sectionId) => {
            const section = sections.find((item) => item.id === sectionId);
            if (!section) return;
            onSectionToggleCollapsed?.(sectionId, !section.isCollapsed);
          }}
          onNameChange={(sectionId, name) =>
            setSectionNameDrafts((prev) => ({ ...prev, [sectionId]: name }))
          }
          onNameCommit={(sectionId, name) => {
            setSectionNameDrafts((prev) => {
              const next = { ...prev };
              delete next[sectionId];
              return next;
            });
            onSectionNameCommit?.(sectionId, name);
          }}
          onSectionMenuPointerDown={(sectionId, event) => {
            event.preventDefault();
            event.stopPropagation();
            setSectionMenu({
              sectionId,
              x: event.clientX,
              y: event.clientY,
            });
          }}
          onDropOnSection={onDropOnSection}
        />
      </div>
    );

  const menuTargets = contextMenu ? resolveMenuTargets(contextMenu.slide) : [];

  return (
    <>
      <div
        className={`td-deck-filmstrip-shell${collapsed ? " td-deck-filmstrip-shell--collapsed" : ""}${multiMode ? " td-deck-filmstrip-shell--multi" : ""}`}
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
            <SlideFilmstripControls onAdd={onAdd} onAddSection={onAddSection} />
            {listBody}
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
          slideTitle={
            menuTargets.length > 1
              ? `${menuTargets.length} telas`
              : contextMenu.slide.title
          }
          slideActive={contextMenu.slide.isActive}
          selectionCount={menuTargets.length}
          canPaste={canPasteSlide}
          onClose={closeContextMenu}
          onCopy={() => onCopy(contextMenu.slide)}
          onPaste={onPaste}
          onDuplicate={() => onDuplicate(menuTargets)}
          onAdd={onAdd}
          onCreateSection={
            onCreateSection ? () => onCreateSection(contextMenu.slide) : undefined
          }
          onRename={() => beginRename(contextMenu.slide)}
          onToggleActive={() => onToggleActive(menuTargets)}
          onRemove={() => onRemove(menuTargets)}
        />
      ) : null}

      {sectionMenu && sectionMenuTarget ? (
        <DeckSectionContextMenu
          open
          position={{ x: sectionMenu.x, y: sectionMenu.y }}
          collapsed={Boolean(sectionMenuTarget.isCollapsed)}
          active={sectionMenuTarget.isActive !== false}
          allowDelete={!sectionMenuTarget.isMain}
          portalScopeClassName="dashboard-tv-dashboard"
          onClose={closeSectionMenu}
          onAction={handleSectionMenuAction}
        />
      ) : null}
    </>
  );
}
