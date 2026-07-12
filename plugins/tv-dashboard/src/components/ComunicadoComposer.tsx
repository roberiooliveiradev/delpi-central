import {
  adjustmentHandleCssPosition,
  blockShapeChromeAdjustmentSpecs,
  blockSupportsShapeChromeHandles,
  comunicadoBackgroundCssProperties,
  isDataSourceBlockType,
  isDataViewBlockType,
  isFetchableDataBlockType,
  resolveBlockSelectionBorderRadiusPx,
  resolveBlockShapeChromeAdjustmentValues,
  resolveViewportPixelSize,
  shouldHideDataSourceOnStage,
  resolveBlockPlacementStyle,
  shapeBlockAllowsResize,
  useComunicadoGoogleFonts,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
import { blocksInMarquee, normalizeMarqueeRect, type MarqueeRect } from "../utils/comunicadoMarquee";
import { ComunicadoStageContextMenu } from "./ComunicadoStageContextMenu";
import { ComunicadoStageShell } from "./ComunicadoStageShell";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoEditorBlockView } from "./ComunicadoEditorBlockView";
import type { BlockDragMode } from "./useCanvasBlockInteraction";

const MARQUEE_THRESHOLD_PX = 4;

const BLOCK_RESIZE_HANDLES: Array<{
  mode: Exclude<BlockDragMode, "move" | `adjust-${number}`>;
  position: string;
  label: string;
}> = [
  { mode: "resize-nw", position: "nw", label: "Redimensionar canto superior esquerdo" },
  { mode: "resize-n", position: "n", label: "Redimensionar borda superior" },
  { mode: "resize-ne", position: "ne", label: "Redimensionar canto superior direito" },
  { mode: "resize-w", position: "w", label: "Redimensionar borda esquerda" },
  { mode: "resize-e", position: "e", label: "Redimensionar borda direita" },
  { mode: "resize-sw", position: "sw", label: "Redimensionar canto inferior esquerdo" },
  { mode: "resize-s", position: "s", label: "Redimensionar borda inferior" },
  { mode: "resize-se", position: "se", label: "Redimensionar canto inferior direito" },
];

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
  if (!masterLogo?.url && !logoBlobUrl) return null;
  const frame = masterLogo?.frame;
  return (
    <div
      className="td-composer__master-logo"
      aria-hidden
      style={{
        position: "absolute",
        left: `${frame?.x ?? 2}%`,
        top: `${frame?.y ?? 2}%`,
        width: `${frame?.w ?? 12}%`,
        height: `${frame?.h ?? 10}%`,
        opacity: masterLogo?.opacity ?? 1,
        zIndex: 0,
        pointerEvents: "none",
        backgroundImage: `url(${logoBlobUrl ?? masterLogo?.url})`,
        backgroundSize: "contain",
        backgroundRepeat: "no-repeat",
        backgroundPosition: "center",
      }}
    />
  );
}

export function ComunicadoComposerCanvas() {
  const {
    config,
    blocks,
    selected,
    selectedId,
    selectedIds,
    selectedChartPart,
    selectedKpiPart,
    isBlockSelected,
    selectBlock,
    selectBlocksByIds,
    clearSelection,
    editingTextId,
    canvasRef,
    startDrag,
    dataPreviewLoading,
    showStageGrid,
    showStageGuides,
    updateBlock,
    viewportProfile,
    stageZoom,
    fitStageToView,
  } = useComunicadoEditor();
  useComunicadoGoogleFonts(config);
  const canvasStyle = useCanvasBackgroundStyle();
  const designSize = useMemo(
    () => resolveViewportPixelSize(viewportProfile),
    [viewportProfile],
  );
  const [marquee, setMarquee] = useState<MarqueeRect | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);
  const marqueeActiveRef = useRef(false);
  const marqueeStartClientRef = useRef<{ x: number; y: number } | null>(null);
  const marqueeRectRef = useRef<MarqueeRect | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => fitStageToView(), 0);
    return () => window.clearTimeout(timer);
  }, [designSize.width, designSize.height, fitStageToView, viewportProfile]);

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

      if (!rect) return;

      const normalized = normalizeMarqueeRect(rect);
      const tiny =
        Math.abs(normalized.x2 - normalized.x1) < 0.5 && Math.abs(normalized.y2 - normalized.y1) < 0.5;
      if (tiny) {
        if (!additive) clearSelection();
        return;
      }

      const ids = blocksInMarquee(blocks, normalized);
      if (ids.length === 0) {
        if (!additive) clearSelection();
        return;
      }
      if (additive) {
        const merged = new Set([...selectedIds, ...ids]);
        selectBlocksByIds([...merged]);
      } else {
        selectBlocksByIds(ids);
      }
    },
    [blocks, clearSelection, selectBlocksByIds, selectedIds],
  );

  const handleCanvasPointerDown = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (event.target !== event.currentTarget) return;
      if (editingTextId) return;

      const additive = event.shiftKey;
      const origin = clientToCanvasPercent(event.clientX, event.clientY);
      marqueeActiveRef.current = true;
      marqueeStartClientRef.current = { x: event.clientX, y: event.clientY };
      const initial: MarqueeRect = { x1: origin.x, y1: origin.y, x2: origin.x, y2: origin.y };
      marqueeRectRef.current = initial;
      setMarquee(initial);

      function onMove(moveEvent: PointerEvent) {
        if (!marqueeActiveRef.current || !marqueeStartClientRef.current) return;
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
        finishMarquee(additive);
      }

      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    },
    [clientToCanvasPercent, editingTextId, finishMarquee],
  );

  const handleCanvasContextMenu = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      event.preventDefault();
      if (editingTextId) return;
      setContextMenu({ x: event.clientX, y: event.clientY });
    },
    [editingTextId],
  );

  const handleBlockContextMenu = useCallback(
    (event: React.MouseEvent<HTMLDivElement>, blockId: string) => {
      event.preventDefault();
      event.stopPropagation();
      if (editingTextId) return;
      if (!isBlockSelected(blockId)) {
        selectBlock(blockId);
      }
      setContextMenu({ x: event.clientX, y: event.clientY });
    },
    [editingTextId, isBlockSelected, selectBlock],
  );

  const primarySelected = selectedId;
  const showResizeHandles = (blockId: string) => {
    if (blockId !== primarySelected || editingTextId === blockId || selectedIds.length > 1) {
      return false;
    }
    const block = blocks.find((item) => item.id === blockId);
    // Handles do bloco só no nível global — com parte interna selecionada, chrome da parte manda.
    if (block?.type === "chart_view" && selectedChartPart) {
      return false;
    }
    if (
      block?.type === "kpi_view" &&
      selectedKpiPart &&
      selectedKpiPart.kind !== "card"
    ) {
      return false;
    }
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

  return (
    <ComunicadoStageShell>
      <div
        className="td-composer__canvas-zoom-sizer"
        style={{
          width: designSize.width * stageZoom,
          height: designSize.height * stageZoom,
        }}
      >
        <div
          ref={canvasRef}
          className="td-composer__canvas"
          data-viewport={viewportProfile || "1080p"}
          style={{
            ...canvasStyle,
            width: designSize.width,
            height: designSize.height,
            transform: `scale(${stageZoom})`,
            transformOrigin: "top left",
          }}
          onPointerDown={handleCanvasPointerDown}
          onContextMenu={handleCanvasContextMenu}
        >
          <MasterLogoOverlay />
          {showStageGrid ? <div className="td-composer__stage-grid" aria-hidden="true" /> : null}
          {showStageGuides ? (
            <>
              <div className="td-composer__stage-guide td-composer__stage-guide--v" aria-hidden="true" />
              <div className="td-composer__stage-guide td-composer__stage-guide--h" aria-hidden="true" />
            </>
          ) : null}
          {blocks.map((block) => {
            if (isDataSourceBlockType(block.type) && shouldHideDataSourceOnStage(block.id, blocks)) {
              return null;
            }
            const isSelected = isBlockSelected(block.id);
            const isPrimary = block.id === primarySelected;
            const selectionRadius = isSelected
              ? resolveBlockSelectionBorderRadiusPx(block)
              : undefined;
            return (
              <div
                key={block.id}
                className={[
                  "td-composer__block-wrap",
                  isSelected ? "td-composer__block-wrap--selected" : "",
                  isSelected && !isPrimary ? "td-composer__block-wrap--multi" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                style={{
                  ...resolveBlockPlacementStyle(block),
                  ...(block.style?.rotation
                    ? { transform: `rotate(${block.style.rotation}deg)` }
                    : {}),
                  ...(selectionRadius != null ? { borderRadius: selectionRadius } : {}),
                }}
                onContextMenu={(event) => handleBlockContextMenu(event, block.id)}
                onPointerDown={(event) => {
                  event.stopPropagation();
                  if (
                    isDataSourceBlockType(block.type) &&
                    selected &&
                    (selected.type === "chart_view" ||
                      selected.type === "kpi_view" ||
                      selected.type === "table_view") &&
                    !selected.dataSourceId?.trim()
                  ) {
                    updateBlock(selected.id, { dataSourceId: block.id } as Partial<ComunicadoBlock>);
                    return;
                  }
                  selectBlock(block.id, { additive: event.shiftKey });
                  if (
                    editingTextId === block.id &&
                    (event.target as HTMLElement).closest(".td-composer__inline-text")
                  ) {
                    return;
                  }
                  startDrag(event, block, "move");
                }}
              >
                <ComunicadoEditorBlockView
                  block={block}
                  fontScale={1}
                  isSelected={isSelected}
                  isEditingText={editingTextId === block.id}
                  className={isSelected ? "td-composer__block--selected" : ""}
                  dataLoading={
                    (isFetchableDataBlockType(block.type) || isDataViewBlockType(block.type)) &&
                    !("resolved" in block && block.resolved) &&
                    dataPreviewLoading
                  }
                />
                {showResizeHandles(block.id) ? (
                  <div className="td-composer__block-handles">
                    <button
                      type="button"
                      className="td-composer__rotate"
                      aria-label="Girar elemento"
                      onPointerDown={(event) => startDrag(event, block, "rotate")}
                    />
                    {BLOCK_RESIZE_HANDLES.map(({ mode, position, label }) => (
                      <button
                        key={mode}
                        type="button"
                        className={`td-composer__resize td-composer__resize--${position}`}
                        aria-label={label}
                        onPointerDown={(event) => startDrag(event, block, mode)}
                      />
                    ))}
                    {blockSupportsShapeChromeHandles(block)
                      ? blockShapeChromeAdjustmentSpecs(block).map((spec) => {
                          const shortSidePx = Math.min(
                            (block.frame.w / 100) * designSize.width,
                            (block.frame.h / 100) * designSize.height,
                          );
                          const values = resolveBlockShapeChromeAdjustmentValues(
                            block,
                            shortSidePx,
                          );
                          const pos = adjustmentHandleCssPosition(spec, values);
                          return (
                            <button
                              key={`adj-${spec.index}`}
                              type="button"
                              className="td-composer__adjust"
                              style={{ left: pos.left, top: pos.top }}
                              aria-label={`Ajustar ${spec.label}`}
                              title={spec.label}
                              onPointerDown={(event) =>
                                startDrag(event, block, `adjust-${spec.index}`)
                              }
                            />
                          );
                        })
                      : null}
                  </div>
                ) : null}
              </div>
            );
          })}
          {marqueeStyle ? (
            <div className="td-composer__marquee" style={marqueeStyle} aria-hidden="true" />
          ) : null}
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
