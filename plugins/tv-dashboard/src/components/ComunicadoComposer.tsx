import {
  ensureComunicadoDualClass,
  comunicadoStageBemClasses,
} from "@delpi/plugin-ui/index";
import {
  buildViewDataLinkPatch,
  buildTextDataLinkPatch,
  comunicadoBackgroundCssProperties,
  isComunicadoVisualBoxBlock,
  isDataSourceBlockType,
  isDataViewBlockType,
  isFetchableDataBlockType,
  isBlockHiddenOnStage,
  resolveBlockSelectionBorderRadiusPx,
  resolveViewportPixelSize,
  isLineShapeKind,
  resolveBlockPlacementStyle,
  RichComunicadoMasterLogo,
  shapeBlockAllowsResize,
  useComunicadoGoogleFonts,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

const COMPOSER_STAGE_BEM = comunicadoStageBemClasses("tdp");

import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
import { useAuthenticatedComunicadoCustomFonts } from "../hooks/useAuthenticatedComunicadoCustomFonts";
import { beginBlockStageMoveDrag } from "../utils/beginBlockStageDrag";
import { resolveStageDblClickAction } from "../utils/stageInteractionPolicy";
import {
  blocksInMarquee,
  mergeMarqueeSelection,
  normalizeMarqueeRect,
  resolveMarqueeIntent,
  subtractMarqueeSelection,
  type MarqueeRect,
} from "../utils/comunicadoMarquee";
import {
  expandSelectionWithGroups,
  resolveFullySelectedGroups,
  resolveParentGroupHintFrame,
  unionFramePercent,
} from "../utils/comunicadoGrouping";
import {
  resolveBlockWrapChromeFlags,
  resolveStageSelectionHierarchy,
} from "../utils/stageGroupedSelection";
import {
  resolveStagePanGutterPx,
  shouldDeferToStagePan,
  stageScrollPreserveContentUnderViewportCenter,
  type StageScrollPoint,
} from "../utils/stagePan";
import {
  resolveSelectionChromeColors,
  selectionChromeContrastCssVars,
} from "../utils/selectionChromeContrast";
import {
  resolveSelectionChromeMetrics,
  selectionChromeCssVars,
} from "../utils/selectionChromeMetrics";
import { shouldRenderStageGrid } from "../utils/stageViewport";
import { clampStageGridSizePercent, stageGridSizePercentToDesignPx } from "../utils/stageGridSize";
import { ComunicadoStageContextMenu } from "./ComunicadoStageContextMenu";
import { ComunicadoStageShell } from "./ComunicadoStageShell";
import { BlockSelectionChrome } from "./BlockSelectionChrome";
import { GroupSelectionChrome } from "./GroupSelectionChrome";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoEditorBlockView } from "./ComunicadoEditorBlockView";
import {
  ComplexViewFloatToolbar,
  shouldShowComplexViewFloatToolbar,
} from "./ComplexViewFloatToolbar";
import { RemoteSelectionFrame } from "./RemoteSelectionFrame";
import type { BlockDragMode } from "./useCanvasBlockInteraction";

const MARQUEE_THRESHOLD_PX = 4;

function useCanvasBackgroundStyle() {
  const { background } = useComunicadoEditor();
  const imageApiUrl = background?.type === "image" ? background.url : undefined;
  const { src: imageBlobUrl } = useAuthenticatedBlobUrl(imageApiUrl);

  return useMemo(
    () => comunicadoBackgroundCssProperties(background, imageBlobUrl),
    [background, imageBlobUrl],
  );
}

function MasterLogoOverlay() {
  const { masterLogo } = useComunicadoEditor();
  const { src: logoBlobUrl } = useAuthenticatedBlobUrl(masterLogo?.url);
  // Nunca cair no URL da API: CSS `background-image` não envia Bearer → 401.
  if (!logoBlobUrl) return null;
  return (
    <RichComunicadoMasterLogo
      url={logoBlobUrl}
      frame={masterLogo?.frame}
      opacity={masterLogo?.opacity ?? 1}
      className={ensureComunicadoDualClass(
        `td-composer__master-logo ${COMPOSER_STAGE_BEM.masterLogo}`,
      )}
    />
  );
}

export function ComunicadoComposerCanvas() {
  const {
    config,
    background,
    blocks,
    selected,
    selectedId,
    selectedIds,
    remoteSelections,
    selectedChartPart,
    selectedKpiPart,
    selectedKpiParts,
    selectedTablePart,
    selectedInputPart,
    selectedInputParts,
    isBlockSelected,
    selectBlock,
    selectBlocksByIds,
    clearSelection,
    editingTextId,
    enterTextEdit,
    canvasRef,
    canvasWrapRef,
    startDrag,
    armMultiDragSelection,
    armTapDeselect,
    cancelPendingTapDeselect,
    dataPreviewLoading,
    showStageGrid,
    showStageGuides,
    activeSmartGuides,
    stageGridSizePercent,
    updateBlock,
    viewportProfile,
    stageZoom,
    stagePanMode,
    fitStageToView,
    bootstrapStageViewPosition,
    persistStageViewPosition,
    stageViewReady,
  } = useComunicadoEditor();
  useComunicadoGoogleFonts(config);
  useAuthenticatedComunicadoCustomFonts(config.customFonts);
  const canvasStyle = useCanvasBackgroundStyle();
  const designSize = useMemo(
    () => resolveViewportPixelSize(viewportProfile),
    [viewportProfile],
  );
  const selectionChromeStyle = useMemo(
    () => ({
      ...selectionChromeCssVars(resolveSelectionChromeMetrics(stageZoom)),
      ...selectionChromeContrastCssVars(resolveSelectionChromeColors(background)),
    }),
    [background, stageZoom],
  );
  const gridSizePx = useMemo(
    () => stageGridSizePercentToDesignPx(stageGridSizePercent, designSize),
    [stageGridSizePercent, designSize],
  );
  const [marquee, setMarquee] = useState<MarqueeRect | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);
  const [panGutter, setPanGutter] = useState({ x: 48, y: 48 });
  const marqueeActiveRef = useRef(false);
  const marqueeStartClientRef = useRef<{ x: number; y: number } | null>(null);
  const marqueeRectRef = useRef<MarqueeRect | null>(null);
  /** Último tamanho/gutter aplicados — base para preservar o ponto sob o centro ao reflow. */
  const stageViewportLayoutRef = useRef<{
    gutter: { x: number; y: number };
    clientWidth: number;
    clientHeight: number;
  } | null>(null);
  const pendingStageScrollRef = useRef<StageScrollPoint | null>(null);

  useEffect(() => {
    const wrap = canvasWrapRef.current;
    if (!wrap) return;
    const updateGutter = () => {
      const nextGutter = resolveStagePanGutterPx(wrap.clientWidth, wrap.clientHeight);
      const nextW = wrap.clientWidth;
      const nextH = wrap.clientHeight;
      const last = stageViewportLayoutRef.current;
      if (
        last &&
        last.clientWidth === nextW &&
        last.clientHeight === nextH &&
        last.gutter.x === nextGutter.x &&
        last.gutter.y === nextGutter.y
      ) {
        return;
      }
      // Durante bootstrap não compensar — o fit (Ajustar) define o scroll.
      if (stageViewReady && last && last.clientWidth > 0 && last.clientHeight > 0) {
        pendingStageScrollRef.current = stageScrollPreserveContentUnderViewportCenter({
          scrollLeft: wrap.scrollLeft,
          scrollTop: wrap.scrollTop,
          prevClientWidth: last.clientWidth,
          prevClientHeight: last.clientHeight,
          prevGutter: last.gutter,
          nextClientWidth: nextW,
          nextClientHeight: nextH,
          nextGutter,
        });
      } else {
        pendingStageScrollRef.current = null;
      }
      stageViewportLayoutRef.current = {
        gutter: nextGutter,
        clientWidth: nextW,
        clientHeight: nextH,
      };
      const gutterChanged =
        !last || last.gutter.x !== nextGutter.x || last.gutter.y !== nextGutter.y;
      if (gutterChanged) {
        setPanGutter(nextGutter);
        return;
      }
      const pending = pendingStageScrollRef.current;
      if (pending) {
        pendingStageScrollRef.current = null;
        wrap.scrollLeft = pending.scrollLeft;
        wrap.scrollTop = pending.scrollTop;
      }
    };
    updateGutter();
    const observer = new ResizeObserver(updateGutter);
    observer.observe(wrap);
    return () => observer.disconnect();
  }, [canvasWrapRef, stageViewReady]);

  // Só após paint do novo padding: aplica scroll preservando o ponto do slide (não recentra).
  useLayoutEffect(() => {
    if (!stageViewReady) {
      pendingStageScrollRef.current = null;
      return;
    }
    const wrap = canvasWrapRef.current;
    const pending = pendingStageScrollRef.current;
    if (!wrap || !pending) return;
    pendingStageScrollRef.current = null;
    wrap.scrollLeft = pending.scrollLeft;
    wrap.scrollTop = pending.scrollTop;
    persistStageViewPosition({ immediate: true });
  }, [panGutter.x, panGutter.y, persistStageViewPosition, stageViewReady]);

  // Mount: sempre Ajustar (fit). Depois: fit só se o formato do slide mudar.
  const designKeyRef = useRef<string | null>(null);
  useEffect(() => {
    const key = `${viewportProfile}:${designSize.width}x${designSize.height}`;
    const prev = designKeyRef.current;
    designKeyRef.current = key;

    const timer = window.setTimeout(() => {
      if (prev === null) {
        bootstrapStageViewPosition();
        return;
      }
      if (prev !== key) {
        fitStageToView();
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, [
    bootstrapStageViewPosition,
    designSize.width,
    designSize.height,
    fitStageToView,
    viewportProfile,
  ]);

  // Durante o bootstrap, o gutter (metade da viewport) só estabiliza após o 1º layout.
  // Refaz Ajustar para o scroll não ficar no zoom/scroll antigos do localStorage.
  const gutterBootRef = useRef<{ x: number; y: number } | null>(null);
  useEffect(() => {
    if (stageViewReady) {
      gutterBootRef.current = { x: panGutter.x, y: panGutter.y };
      return;
    }
    const prev = gutterBootRef.current;
    gutterBootRef.current = { x: panGutter.x, y: panGutter.y };
    if (!prev || (prev.x === panGutter.x && prev.y === panGutter.y)) return;
    const timer = window.setTimeout(() => fitStageToView(), 0);
    return () => window.clearTimeout(timer);
  }, [fitStageToView, panGutter.x, panGutter.y, stageViewReady]);

  // Painel oculto/remoto (client 0) → visível: reexecuta Ajustar.
  useEffect(() => {
    const wrap = canvasWrapRef.current;
    if (!wrap) return;
    let hadSize = wrap.clientWidth > 0 && wrap.clientHeight > 0;
    const observer = new ResizeObserver(() => {
      const hasSize = wrap.clientWidth > 0 && wrap.clientHeight > 0;
      if (!hadSize && hasSize) {
        bootstrapStageViewPosition();
      }
      hadSize = hasSize;
    });
    observer.observe(wrap);
    return () => observer.disconnect();
  }, [bootstrapStageViewPosition, canvasWrapRef]);

  const clientToCanvasPercent = useCallback((clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    return {
      x: ((clientX - rect.left) / rect.width) * 100,
      y: ((clientY - rect.top) / rect.height) * 100,
    };
  }, [canvasRef]);

  const finishMarquee = useCallback(
    (additive: boolean) => {
      const rect = marqueeRectRef.current;
      marqueeActiveRef.current = false;
      marqueeStartClientRef.current = null;
      marqueeRectRef.current = null;
      setMarquee(null);
      document.body.style.userSelect = "";
      document.body.classList.remove("td-composer--marqueeing");

      if (!rect) return;

      const intent = resolveMarqueeIntent(rect);
      const normalized = normalizeMarqueeRect(rect);
      const tiny =
        Math.abs(normalized.x2 - normalized.x1) < 0.5 && Math.abs(normalized.y2 - normalized.y1) < 0.5;
      if (tiny) {
        if (intent === "add" && !additive) clearSelection();
        return;
      }

      /* Marquee pega membros; expande para o grupo fechado (paridade Shift+clique). */
      const ids = expandSelectionWithGroups(blocks, blocksInMarquee(blocks, normalized));
      if (intent === "subtract") {
        selectBlocksByIds(subtractMarqueeSelection(selectedIds, ids));
        return;
      }
      if (ids.length === 0) {
        if (!additive) clearSelection();
        return;
      }
      if (additive) {
        selectBlocksByIds(mergeMarqueeSelection(selectedIds, ids));
      } else {
        selectBlocksByIds(ids);
      }
    },
    [blocks, clearSelection, selectBlocksByIds, selectedIds],
  );

  const startDragRespectingPan = useCallback(
    (
      event: React.PointerEvent<HTMLElement>,
      block: ComunicadoBlock,
      mode: BlockDragMode,
    ) => {
      if (shouldDeferToStagePan(event, stagePanMode)) return;
      // Handles do primary: arma a multi atual para move/resize em grupo.
      if (isBlockSelected(block.id) && selectedIds.length > 1) {
        armMultiDragSelection(selectedIds);
      } else {
        armMultiDragSelection([block.id]);
      }
      startDrag(event, block, mode);
    },
    [armMultiDragSelection, isBlockSelected, selectedIds, stagePanMode, startDrag],
  );

  const handleCanvasPointerDown = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (shouldDeferToStagePan(event, stagePanMode)) return;
      // Marquee só no fundo do slide — não iniciar sobre um bloco.
      const target = event.target as HTMLElement | null;
      if (
        target &&
        target !== event.currentTarget &&
        target.closest("[data-block-id]")
      ) {
        return;
      }
      if (editingTextId) return;

      // Impede seleção nativa de texto enquanto o retângulo de marquee arrasta.
      event.preventDefault();
      window.getSelection()?.removeAllRanges();
      document.body.style.userSelect = "none";
      document.body.classList.add("td-composer--marqueeing");

      const additive = event.shiftKey;
      const origin = clientToCanvasPercent(event.clientX, event.clientY);
      marqueeActiveRef.current = true;
      marqueeStartClientRef.current = { x: event.clientX, y: event.clientY };
      const initial: MarqueeRect = { x1: origin.x, y1: origin.y, x2: origin.x, y2: origin.y };
      marqueeRectRef.current = initial;
      setMarquee(initial);

      function onSelectStart(selectEvent: Event) {
        selectEvent.preventDefault();
      }

      function onMove(moveEvent: PointerEvent) {
        if (!marqueeActiveRef.current || !marqueeStartClientRef.current) return;
        moveEvent.preventDefault();
        const start = marqueeStartClientRef.current;
        const dx = Math.abs(moveEvent.clientX - start.x);
        const dy = Math.abs(moveEvent.clientY - start.y);
        if (dx < MARQUEE_THRESHOLD_PX && dy < MARQUEE_THRESHOLD_PX) return;

        const point = clientToCanvasPercent(moveEvent.clientX, moveEvent.clientY);
        const next: MarqueeRect = {
          x1: initial.x1,
          y1: initial.y1,
          x2: point.x,
          y2: point.y,
        };
        marqueeRectRef.current = next;
        setMarquee(next);
      }

      function onUp() {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        window.removeEventListener("pointercancel", onUp);
        document.removeEventListener("selectstart", onSelectStart, true);
        window.getSelection()?.removeAllRanges();
        finishMarquee(additive);
      }

      document.addEventListener("selectstart", onSelectStart, true);
      window.addEventListener("pointermove", onMove, { passive: false });
      window.addEventListener("pointerup", onUp);
      window.addEventListener("pointercancel", onUp);
    },
    [clientToCanvasPercent, editingTextId, finishMarquee, stagePanMode],
  );

  const handleStageContextMenu = useCallback(
    (event: React.MouseEvent<HTMLDivElement>, blockId?: string) => {
      event.preventDefault();
      if (editingTextId) return;
      if (blockId) {
        event.stopPropagation();
        if (!isBlockSelected(blockId)) {
          selectBlock(blockId);
        }
      } else {
        const target = event.target as HTMLElement | null;
        const onBlock = target?.closest?.("[data-block-id]");
        // Fundo do palco / wrap (ex.: modo pan): menu de inserção/colar sem seleção.
        if (!onBlock) {
          clearSelection();
        }
      }
      setContextMenu({ x: event.clientX, y: event.clientY });
    },
    [clearSelection, editingTextId, isBlockSelected, selectBlock],
  );

  const handleCanvasContextMenu = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      handleStageContextMenu(event);
    },
    [handleStageContextMenu],
  );

  const handleBlockContextMenu = useCallback(
    (event: React.MouseEvent<HTMLDivElement>, blockId: string) => {
      handleStageContextMenu(event, blockId);
    },
    [handleStageContextMenu],
  );

  const primarySelected = selectedId;
  const fullySelectedGroups = useMemo(
    () => resolveFullySelectedGroups(blocks, selectedIds),
    [blocks, selectedIds],
  );
  const fullySelectedMemberIds = useMemo(() => {
    const ids = new Set<string>();
    for (const group of fullySelectedGroups) {
      for (const id of group.memberIds) ids.add(id);
    }
    return ids;
  }, [fullySelectedGroups]);
  const selectionHierarchy = useMemo(() => {
    const primaryComplex = blocks.find((item) => item.id === selectedId);
    const selectedParts =
      primaryComplex?.type === "kpi_view"
        ? selectedKpiParts
        : primaryComplex?.type === "input"
          ? selectedInputParts
          : primaryComplex?.type === "table_view" && selectedTablePart
            ? [selectedTablePart]
            : primaryComplex?.type === "chart_view" && selectedChartPart
              ? [selectedChartPart]
              : undefined;
    const selectedPart =
      primaryComplex?.type === "kpi_view"
        ? selectedKpiPart
        : primaryComplex?.type === "chart_view"
          ? selectedChartPart
          : primaryComplex?.type === "table_view"
            ? selectedTablePart
            : primaryComplex?.type === "input"
              ? selectedInputPart
              : null;
    return resolveStageSelectionHierarchy({
      blocks,
      selectedIds,
      selectedPart,
      selectedParts,
    });
  }, [
    blocks,
    selectedId,
    selectedIds,
    selectedKpiPart,
    selectedKpiParts,
    selectedChartPart,
    selectedTablePart,
    selectedInputPart,
    selectedInputParts,
  ]);
  /** Contorno pontilhado do pai quando um (ou mais) filhos estão isolados. */
  const parentGroupHintFrame = useMemo(
    () => resolveParentGroupHintFrame(blocks, selectedIds),
    [blocks, selectedIds],
  );

  const showResizeHandles = (blockId: string) => {
    const block = blocks.find((item) => item.id === blockId);
    const partForChrome =
      block?.type === "kpi_view"
        ? selectedKpiPart
        : block?.type === "chart_view"
          ? selectedChartPart
          : block?.type === "table_view"
            ? selectedTablePart
            : block?.type === "input"
              ? selectedInputPart
              : null;
    const flags = resolveBlockWrapChromeFlags({
      hierarchy: selectionHierarchy,
      blockId,
      blockType: block?.type,
      isSelected: isBlockSelected(blockId),
      /* Membro de qualquer grupo fechado na seleção → chrome no grupo, não no filho. */
      closedGroupActive: fullySelectedMemberIds.has(blockId),
      selectedPart: partForChrome,
    });
    if (!flags.showHandles) return false;
    return block?.type === "shape" ? shapeBlockAllowsResize(block) : true;
  };

  const marqueeStyle = useMemo(() => {
    if (!marquee) return null;
    const rect = normalizeMarqueeRect(marquee);
    return {
      left: `${rect.x1}%`,
      top: `${rect.y1}%`,
      width: `${rect.x2 - rect.x1}%`,
      height: `${rect.y2 - rect.y1}%`,
    };
  }, [marquee]);

  const marqueeIntent = marquee ? resolveMarqueeIntent(marquee) : "add";

  return (
    <ComunicadoStageShell onStageContextMenu={handleStageContextMenu}>
      <div
        className="td-composer__canvas-zoom-sizer"
        style={{
          width: designSize.width * stageZoom,
          height: designSize.height * stageZoom,
          padding: `${panGutter.y}px ${panGutter.x}px`,
        }}
        onContextMenu={handleCanvasContextMenu}
      >
        <div
          ref={canvasRef}
          className={ensureComunicadoDualClass(
            [
              "td-composer__canvas",
              COMPOSER_STAGE_BEM.root,
              marquee ? "td-composer__canvas--marqueeing" : "",
            ]
              .filter(Boolean)
              .join(" "),
          )}
          data-viewport={viewportProfile || "1080p"}
          style={{
            ...canvasStyle,
            ...selectionChromeStyle,
            width: designSize.width,
            height: designSize.height,
            transform: `scale(${stageZoom})`,
            transformOrigin: "top left",
          }}
          onPointerDown={handleCanvasPointerDown}
          onContextMenu={handleCanvasContextMenu}
        >
          {/*
           * Mesma árvore da TV (`ComunicadoStageFrame`): root + __stage.
           * Blocos/logo posicionam no stage — paridade de containing block.
           */}
          <div className={ensureComunicadoDualClass(`td-composer__stage ${COMPOSER_STAGE_BEM.stage}`)}>
          <MasterLogoOverlay />
          {shouldRenderStageGrid(showStageGrid, stageZoom) ? (
            <div
              className="td-composer__stage-grid"
              aria-hidden="true"
              style={{
                backgroundSize: `${gridSizePx.xPx}px ${gridSizePx.yPx}px`,
              }}
            />
          ) : null}
          {showStageGuides ? (
            <>
              <div className="td-composer__stage-guide td-composer__stage-guide--v" aria-hidden="true" />
              <div className="td-composer__stage-guide td-composer__stage-guide--h" aria-hidden="true" />
            </>
          ) : null}
          {activeSmartGuides.length > 0
            ? activeSmartGuides.map((guide, index) => (
                <div
                  key={`smart-${guide.orientation}-${guide.position}-${index}`}
                  className={`td-composer__smart-guide td-composer__smart-guide--${guide.orientation}`}
                  style={
                    guide.orientation === "v"
                      ? { left: `${guide.position}%` }
                      : { top: `${guide.position}%` }
                  }
                  aria-hidden="true"
                />
              ))
            : null}
          {blocks.map((block) => {
            if (isBlockHiddenOnStage(block, blocks)) {
              return null;
            }
            const isSelected = isBlockSelected(block.id);
            const inClosedGroup = Boolean(isSelected && fullySelectedMemberIds.has(block.id));
            const remoteEditors = remoteSelections.filter((selection) =>
              selection.selectedIds.includes(block.id),
            );
            const isPrimary = block.id === primarySelected;
            const partForChrome =
              block.type === "kpi_view"
                ? selectedKpiPart
                : block.type === "chart_view"
                  ? selectedChartPart
                  : block.type === "table_view"
                    ? selectedTablePart
                    : block.type === "input"
                      ? selectedInputPart
                      : null;
            const wrapChrome = resolveBlockWrapChromeFlags({
              hierarchy: selectionHierarchy,
              blockId: block.id,
              blockType: block.type,
              isSelected,
              closedGroupActive: inClosedGroup,
              selectedPart: partForChrome,
            });
            const hasPartChrome = wrapChrome.partChildrenActive;
            const selectionRadius = isSelected || remoteEditors.length > 0
              ? resolveBlockSelectionBorderRadiusPx(block)
              : undefined;
            return (
              <div
                key={block.id}
                data-block-id={block.id}
                className={[
                  "td-composer__block-wrap",
                  wrapChrome.showOutline ? "td-composer__block-wrap--selected" : "",
                  isSelected && !isPrimary && wrapChrome.showOutline
                    ? "td-composer__block-wrap--multi"
                    : "",
                  wrapChrome.mutedAsGroupMember ? "td-composer__block-wrap--group-member" : "",
                  hasPartChrome ? "td-composer__block-wrap--part-chrome" : "",
                  block.type === "text" || block.type === "heading"
                    ? "td-composer__block-wrap--text"
                    : "",
                  block.type === "shape" && isLineShapeKind(block.shape)
                    ? "td-composer__block-wrap--line-shape"
                    : "",
                  block.type === "chart_view" ? "td-composer__block-wrap--chart" : "",
                  block.type === "kpi_view" ? "td-composer__block-wrap--kpi" : "",
                  block.type === "input" ? "td-composer__block-wrap--input" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                style={{
                  ...resolveBlockPlacementStyle(block),
                  zIndex: block.style?.zIndex ?? 1,
                  ...(block.style?.rotation
                    ? { transform: `rotate(${block.style.rotation}deg)` }
                    : {}),
                  ...(selectionRadius != null ? { borderRadius: selectionRadius } : {}),
                }}
                onContextMenu={(event) => handleBlockContextMenu(event, block.id)}
                onDoubleClick={(event) => {
                  if (shouldDeferToStagePan(event, stagePanMode)) return;
                  event.stopPropagation();
                  event.preventDefault();
                  cancelPendingTapDeselect();
                  const action = resolveStageDblClickAction({
                    block,
                    blocks,
                    selectedIds,
                  });
                  if (action.type === "enter-text-edit") {
                    enterTextEdit(action.blockId);
                    return;
                  }
                  if (action.type === "isolate-child") {
                    selectBlock(action.blockId, { expandGroup: false });
                  }
                }}
                onPointerDown={(event) => {
                  /* Ctrl/Cmd+clique: remove da seleção (não pan). */
                  if (
                    (event.ctrlKey || event.metaKey) &&
                    !event.shiftKey &&
                    !stagePanMode
                  ) {
                    event.stopPropagation();
                    event.preventDefault();
                    selectBlock(block.id, { subtract: true, expandGroup: false });
                    return;
                  }
                  // Pan (mão): não engolir o evento — o wrap do palco arrasta o scroll.
                  if (shouldDeferToStagePan(event, stagePanMode)) return;
                  event.stopPropagation();
                  if (
                    isDataSourceBlockType(block.type) &&
                    selected &&
                    (selected.type === "chart_view" ||
                      selected.type === "kpi_view" ||
                      selected.type === "table_view") &&
                    !selected.dataSourceId?.trim()
                  ) {
                    const resolved =
                      "resolved" in block ? block.resolved : undefined;
                    updateBlock(
                      selected.id,
                      buildViewDataLinkPatch({
                        viewType: selected.type,
                        dataSourceId: block.id,
                        resolved,
                        currentFrame: selected.frame,
                        existing: {
                          kpiProjection:
                            "kpiProjection" in selected ? selected.kpiProjection : undefined,
                          chartProjection:
                            "chartProjection" in selected ? selected.chartProjection : undefined,
                          tableProjection:
                            "tableProjection" in selected ? selected.tableProjection : undefined,
                        },
                      }) as Partial<ComunicadoBlock>,
                    );
                    return;
                  }
                  if (
                    isDataSourceBlockType(block.type) &&
                    selected &&
                    isComunicadoVisualBoxBlock(selected) &&
                    !selected.dataSourceId?.trim()
                  ) {
                    const resolved =
                      "resolved" in block ? block.resolved : undefined;
                    updateBlock(
                      selected.id,
                      buildTextDataLinkPatch({
                        dataSourceId: block.id,
                        resolved,
                        existing: selected.textProjection,
                      }) as Partial<ComunicadoBlock>,
                    );
                    return;
                  }
                  if (
                    editingTextId === block.id &&
                    (event.target as HTMLElement).closest(".td-composer__inline-text")
                  ) {
                    return;
                  }
                  beginBlockStageMoveDrag({
                    event,
                    block,
                    blocks,
                    isBlockSelected,
                    selectedIds,
                    selectedId,
                    selectBlock,
                    selectBlocksByIds,
                    armMultiDragSelection,
                    startDrag,
                    armTapDeselect,
                  });
                }}
              >
                <ComunicadoEditorBlockView
                  block={block}
                  fontScale={1}
                  isSelected={isSelected && !inClosedGroup}
                  isEditingText={editingTextId === block.id}
                  className={[
                    isSelected ? "td-composer__block--selected" : "",
                    block.type === "chart_view" ? "td-composer__block--chart" : "",
                    block.type === "kpi_view" ? "td-composer__block--kpi" : "",
                  ]
                    .filter(Boolean)
                    .join(" ") || undefined}
                  dataLoading={
                    (isFetchableDataBlockType(block.type) || isDataViewBlockType(block.type)) &&
                    !("resolved" in block && block.resolved) &&
                    dataPreviewLoading
                  }
                />
                {remoteEditors.length > 0 ? (
                  <RemoteSelectionFrame
                    displayNames={remoteEditors.map((selection) => selection.displayName)}
                  />
                ) : null}
                {showResizeHandles(block.id) ? (
                  <BlockSelectionChrome
                    block={block}
                    designShortSidePx={Math.min(
                      (block.frame.w / 100) * designSize.width,
                      (block.frame.h / 100) * designSize.height,
                    )}
                    allowResize={block.type === "shape" ? shapeBlockAllowsResize(block) : true}
                    onPointerDown={startDragRespectingPan}
                  />
                ) : null}
                {shouldShowComplexViewFloatToolbar({
                  block,
                  isPrimary,
                  selectedIdsLength: selectedIds.length,
                  selectedChartPart,
                  selectedKpiPart,
                  selectedTablePart,
                  selectedInputPart,
                }) ? (
                  <ComplexViewFloatToolbar block={block} />
                ) : null}
              </div>
            );
          })}
          {fullySelectedGroups.map((group) => {
            const frame = unionFramePercent(group.members.map((member) => member.frame));
            const anchor =
              group.members.find((member) => member.id === primarySelected) ??
              group.members[group.members.length - 1];
            if (!anchor) return null;
            return (
              <GroupSelectionChrome
                key={group.groupId}
                frame={frame}
                anchorBlock={anchor}
                onPointerDown={startDragRespectingPan}
              />
            );
          })}
          {parentGroupHintFrame ? (
            <div
              className="td-composer__group-chrome td-composer__group-chrome--parent-hint"
              style={{
                left: `${parentGroupHintFrame.x}%`,
                top: `${parentGroupHintFrame.y}%`,
                width: `${parentGroupHintFrame.w}%`,
                height: `${parentGroupHintFrame.h}%`,
              }}
              data-group-chrome="parent-hint"
              aria-hidden="true"
            />
          ) : null}
          {marqueeStyle ? (
            <div
              className={[
                "td-composer__marquee",
                marqueeIntent === "subtract"
                  ? "td-composer__marquee--subtract"
                  : "td-composer__marquee--add",
              ].join(" ")}
              style={marqueeStyle}
              aria-hidden="true"
            />
          ) : null}
          </div>
        </div>
      </div>
      <ComunicadoStageContextMenu
        open={contextMenu != null}
        position={contextMenu}
        onClose={() => setContextMenu(null)}
      />
    </ComunicadoStageShell>
  );
}
