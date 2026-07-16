import {
  ChartViewBlockView,
  TableViewBlockView,
  ComunicadoBlockView,
  ComunicadoMediaPlaceholder,
  blockCssStyle,
  chartOptionsToParts,
  chartPartAllowsMove,
  chartPartAllowsEdit,
  chartPartAllowsResize,
  clampChartPartFrame,
  comunicadoImageCropCssProperties,
  getChartPartState,
  isChartPartRefEqual,
  isComunicadoVisualBoxBlock,
  mergeComunicadoChartOptions,
  partsToChartOptions,
  resolveChartPartFrameRoot,
  scaleChartPartTypographyOnResize,
  scaleKpiPartTypographyOnResize,
  upsertChartPartState,
  KpiViewBlockView,
  KPI_ICON_DEFAULT_RADIUS_PX,
  borderRadiusPxToKpiCornerAdj,
  clampKpiPartFrame,
  getKpiPartState,
  kpiCornerAdjToBorderRadiusPx,
  kpiPartAllowsEdit,
  kpiPartAllowsFrame,
  kpiPartAllowsMove,
  kpiPartAllowsResize,
  kpiPartCornerAdjFromLocalX,
  isKpiPartRefEqual,
  materializeMissingKpiPartFramesFromRoot,
  partsToKpiOptions,
  resolveKpiPartFrameRoot,
  upsertKpiPartState,
  isFetchableDataBlockType,
  clampInputPartFrame,
  getInputPartState,
  inputPartAllowsMove,
  inputPartAllowsResize,
  materializeMissingInputPartFramesFromRoot,
  resolveInputParamSchemaField,
  resolveInputPartFrameRoot,
  resolveInputRefreshSourceIds,
  resolveInputTargetScope,
  resizeInputPartFrame,
  scaleInputPartTypographyOnResize,
  upsertInputPartState,
  type ComunicadoBlock,
  type ComunicadoChartPartFrame,
  type ComunicadoChartPartRef,
  type ComunicadoChartPartResizeHandle,
  type ComunicadoChartViewBlock,
  type ComunicadoInputBlock,
  type ComunicadoInputPartRef,
  type ComunicadoInputPartResizeHandle,
  type ComunicadoKpiPartFrame,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiPartResizeHandle,
  type ComunicadoKpiViewBlock,
  type ComunicadoMediaBlock,
  type ComunicadoTablePartRef,
  type ComunicadoTableViewBlock,
  type InputParamSchema,
} from "@delpi/tv-dashboard-presentation";
import { useCallback, useEffect, useMemo, useState, type CSSProperties, type PointerEvent as ReactPointerEvent } from "react";

import { listDataRoutes, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { ENUM_OPTION_LABELS, resolveParamFieldLabel } from "../content/dataParamCatalog";
import { DATE_RANGE_PRESET_OPTIONS } from "../utils/dateRangePresets";

import { beginBlockStageMoveDrag } from "../utils/beginBlockStageDrag";
import { resizeFrameWithOptionalAspect } from "../utils/resizeFrameAspect";

import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
import { resolveCompositePartPointerAction, isCompositeContentPart } from "../utils/compositePartSelection";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoEditorVisualBoxBlock } from "./ComunicadoEditorVisualBoxBlock";
import { ComunicadoEditorVideoPreview } from "./ComunicadoEditorVideoPreview";

type Props = {
  block: ComunicadoBlock;
  fontScale?: number;
  className?: string;
  isSelected?: boolean;
  isEditingText?: boolean;
  dataLoading?: boolean;
};

function EditorImageBlock({
  block,
  style,
  className,
}: {
  block: ComunicadoMediaBlock;
  style: CSSProperties;
  className?: string;
  isSelected?: boolean;
}) {
  const { src, loading, error } = useAuthenticatedBlobUrl(block.url);

  const blockClass = [
    "tdp-comunicado__block",
    "tdp-comunicado__block--image",
    "tdp-comunicado__block--media",
    "td-composer__media-block",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const fit = block.style?.objectFit ?? "contain";

  return (
    <div className={blockClass} style={style}>
      {src ? (
        <img
          className="td-composer__media-preview"
          src={src}
          alt=""
          style={comunicadoImageCropCssProperties(block.imageCrop, fit)}
        />
      ) : block.url && loading ? (
        <ComunicadoMediaPlaceholder kind="image" state="loading" />
      ) : block.url && error ? (
        <ComunicadoMediaPlaceholder kind="image" state="error" />
      ) : (
        <ComunicadoMediaPlaceholder kind="image" />
      )}
    </div>
  );
}

function EditorChartViewBlock({
  block,
  style,
  className,
  dataLoading,
}: {
  block: ComunicadoChartViewBlock;
  style: CSSProperties;
  className?: string;
  dataLoading?: boolean;
}) {
  const {
    selectedId,
    selectedIds,
    isBlockSelected,
    selectedChartPart,
    editingChartPart,
    selectBlock,
    selectBlocksByIds,
    selectChartPart,
    beginEditChartPart,
    commitChartPartContent,
    cancelEditChartPart,
    requestRibbonTab,
    updateBlock,
    startDrag,
    armMultiDragSelection,
  } = useComunicadoEditor();

  /**
   * Clique simples: com bloco já selecionado, parte de conteúdo → seleciona a parte (Excel-like).
   * Moldura/fundo → arraste do bloco. Mesma parte móvel → move a parte.
   */
  const onPartPointerDown = useCallback(
    (ref: ComunicadoChartPartRef, event?: ReactPointerEvent) => {
      if (!event) return;
      if (event.shiftKey) {
        selectBlock(block.id, { additive: true });
        return;
      }
      const samePartSelected =
        selectedId === block.id &&
        Boolean(selectedChartPart && isChartPartRefEqual(selectedChartPart, ref));
      const contentPart = isCompositeContentPart("chart_view", ref);
      const action = resolveCompositePartPointerAction({
        blockSelected: selectedId === block.id,
        samePartSelected,
        partAllowsMove: chartPartAllowsMove(ref),
        contentPart,
      });
      if (action === "part-move") return;
      if (action === "select-part") {
        selectChartPart(block.id, ref);
        const primitiveKinds = new Set([
          "marker",
          "series",
          "chartArea",
          "plotArea",
          "axis",
          "grid",
        ]);
        requestRibbonTab(primitiveKinds.has(ref.kind) ? "shape" : "chart");
        return;
      }
      beginBlockStageMoveDrag({
        event,
        block,
        isBlockSelected,
        selectedIds,
        selectedId,
        selectBlock,
        selectBlocksByIds,
        armMultiDragSelection,
        startDrag,
      });
    },
    [
      armMultiDragSelection,
      block,
      isBlockSelected,
      requestRibbonTab,
      selectBlock,
      selectBlocksByIds,
      selectChartPart,
      selectedChartPart,
      selectedId,
      selectedIds,
      startDrag,
    ],
  );

  /** Duplo clique: seleciona a parte; se já era a mesma e editável, abre inline. */
  const onPartDoubleClick = useCallback(
    (ref: ComunicadoChartPartRef) => {
      const same =
        selectedId === block.id &&
        selectedChartPart &&
        isChartPartRefEqual(selectedChartPart, ref);
      selectChartPart(block.id, ref);
      const primitiveKinds = new Set([
        "marker",
        "series",
        "chartArea",
        "plotArea",
        "axis",
        "grid",
      ]);
      if (primitiveKinds.has(ref.kind)) {
        requestRibbonTab("shape");
      } else {
        requestRibbonTab("chart");
      }
      if (same && chartPartAllowsEdit(ref)) {
        beginEditChartPart(block.id, ref);
      }
    },
    [
      beginEditChartPart,
      block.id,
      requestRibbonTab,
      selectChartPart,
      selectedChartPart,
      selectedId,
    ],
  );

  const onPartContentCommit = useCallback(
    (ref: ComunicadoChartPartRef, content: string) => {
      if (
        editingChartPart &&
        ref.kind === editingChartPart.kind &&
        (ref.kind !== "axisTitle" ||
          (editingChartPart.kind === "axisTitle" && ref.axis === editingChartPart.axis))
      ) {
        commitChartPartContent(content);
        return;
      }
      const nextParts = upsertChartPartState(block.chartParts, ref, { content, visible: true });
      const nextOptions = mergeComunicadoChartOptions({
        ...block.chartOptions,
        ...partsToChartOptions(nextParts),
      });
      if (ref.kind === "title") {
        nextOptions.title = content;
        nextOptions.showTitle = true;
      } else if (ref.kind === "legend" || ref.kind === "series") {
        nextOptions.seriesName = content;
      } else if (ref.kind === "axisTitle" && ref.axis === "x") {
        nextOptions.xAxisTitle = content;
        nextOptions.showXAxisTitle = true;
      } else if (ref.kind === "axisTitle" && ref.axis === "y") {
        nextOptions.yAxisTitle = content;
        nextOptions.showYAxisTitle = true;
      }
      updateBlock(block.id, {
        chartParts: { ...chartOptionsToParts(nextOptions), ...nextParts },
        chartOptions: nextOptions,
      } as Partial<ComunicadoBlock>);
    },
    [block, commitChartPartContent, editingChartPart, updateBlock],
  );

  const onPartMovePointerDown = useCallback(
    (ref: ComunicadoChartPartRef, event: ReactPointerEvent) => {
      if (!chartPartAllowsMove(ref)) return;
      const chartRoot = resolveChartPartFrameRoot(ref, event.currentTarget as HTMLElement);
      if (!chartRoot) return;
      event.preventDefault();
      const rect = chartRoot.getBoundingClientRect();
      const elRect = (event.currentTarget as HTMLElement).getBoundingClientRect();
      const existing = getChartPartState(block.chartParts, ref)?.frame;
      const origin = {
        x: existing?.x ?? ((elRect.left - rect.left) / Math.max(rect.width, 1)) * 100,
        y: existing?.y ?? ((elRect.top - rect.top) / Math.max(rect.height, 1)) * 100,
        w: existing?.w ?? (elRect.width / Math.max(rect.width, 1)) * 100,
        h: existing?.h ?? (elRect.height / Math.max(rect.height, 1)) * 100,
      };
      const startClientX = event.clientX;
      const startClientY = event.clientY;
      let lastParts = block.chartParts;
      let dragged = false;

      const onMove = (ev: PointerEvent) => {
        const dx = ((ev.clientX - startClientX) / Math.max(rect.width, 1)) * 100;
        const dy = ((ev.clientY - startClientY) / Math.max(rect.height, 1)) * 100;
        if (!dragged && Math.abs(dx) + Math.abs(dy) < 0.4) return;
        dragged = true;
        const nextFrame = clampChartPartFrame({
          ...origin,
          x: origin.x + dx,
          y: origin.y + dy,
        });
        lastParts = upsertChartPartState(lastParts, ref, { frame: nextFrame });
        updateBlock(block.id, { chartParts: lastParts } as Partial<ComunicadoBlock>);
      };

      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
      };
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    },
    [block.chartParts, block.id, updateBlock],
  );

  const onPartResizePointerDown = useCallback(
    (ref: ComunicadoChartPartRef, event: ReactPointerEvent, handle: ComunicadoChartPartResizeHandle) => {
      if (!chartPartAllowsResize(ref)) return;
      const chartRoot = resolveChartPartFrameRoot(ref, event.currentTarget as HTMLElement);
      const host = (event.currentTarget as HTMLElement).closest("[data-chart-part]");
      if (!chartRoot || !host) return;
      event.preventDefault();
      const rect = chartRoot.getBoundingClientRect();
      const elRect = host.getBoundingClientRect();
      const existing = getChartPartState(block.chartParts, ref)?.frame;
      const origin = clampChartPartFrame({
        x: existing?.x ?? ((elRect.left - rect.left) / Math.max(rect.width, 1)) * 100,
        y: existing?.y ?? ((elRect.top - rect.top) / Math.max(rect.height, 1)) * 100,
        w: existing?.w ?? (elRect.width / Math.max(rect.width, 1)) * 100,
        h: existing?.h ?? (elRect.height / Math.max(rect.height, 1)) * 100,
      });
      const startClientX = event.clientX;
      const startClientY = event.clientY;
      /** Tipografia pré-resize — base fixa para não acumular fator a cada move. */
      const originParts = block.chartParts;
      const originSize = { w: origin.w ?? 20, h: origin.h ?? 20 };
      const aspectRatio = originSize.w / Math.max(originSize.h, 0.1);

      const applyLive = (nextFrame: ReturnType<typeof clampChartPartFrame>) => {
        let nextParts = upsertChartPartState(originParts, ref, { frame: nextFrame });
        nextParts = scaleChartPartTypographyOnResize(nextParts, ref, originSize, {
          w: nextFrame.w ?? originSize.w,
          h: nextFrame.h ?? originSize.h,
        });
        updateBlock(block.id, { chartParts: nextParts } as Partial<ComunicadoBlock>);
      };

      const onMove = (ev: PointerEvent) => {
        const dx = ((ev.clientX - startClientX) / Math.max(rect.width, 1)) * 100;
        const dy = ((ev.clientY - startClientY) / Math.max(rect.height, 1)) * 100;
        const next = resizeFrameWithOptionalAspect(
          { x: origin.x, y: origin.y, w: originSize.w, h: originSize.h },
          dx,
          dy,
          handle,
          aspectRatio,
          ev.shiftKey,
        );
        applyLive(clampChartPartFrame(next));
      };

      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
      };
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    },
    [block.chartParts, block.id, updateBlock],
  );

  const onPartFrameChange = useCallback(
    (ref: ComunicadoChartPartRef, frame: ComunicadoChartPartFrame) => {
      if (!chartPartAllowsResize(ref) && !chartPartAllowsMove(ref)) return;
      const nextParts = upsertChartPartState(block.chartParts, ref, { frame });
      updateBlock(block.id, { chartParts: nextParts } as Partial<ComunicadoBlock>);
    },
    [block.chartParts, block.id, updateBlock],
  );

  /** Partes interceptam ponteiro com o grupo já selecionado. */
  const interaction =
    selectedId === block.id
      ? {
          selectedPart: selectedChartPart,
          editingPart: editingChartPart,
          onPartPointerDown,
          onPartDoubleClick,
          onPartContentCommit,
          onPartEditCancel: cancelEditChartPart,
          onPartMovePointerDown,
          onPartResizePointerDown,
          onPartFrameChange,
        }
      : null;

  return (
    <div
      className={["tdp-comunicado__block", "tdp-comunicado__block--chart-view", "td-composer__chart-view", className]
        .filter(Boolean)
        .join(" ")}
      style={style}
    >
      <ChartViewBlockView
        block={block}
        interactive={Boolean(interaction)}
        loading={dataLoading}
        interaction={interaction}
      />
    </div>
  );
}

function EditorTableViewBlock({
  block,
  style,
  className,
  dataLoading,
}: {
  block: ComunicadoTableViewBlock;
  style: CSSProperties;
  className?: string;
  dataLoading?: boolean;
}) {
  const {
    selectedId,
    selectedIds,
    isBlockSelected,
    selectedTablePart,
    selectBlock,
    selectBlocksByIds,
    selectTablePart,
    requestRibbonTab,
    startDrag,
    armMultiDragSelection,
  } = useComunicadoEditor();

  const onPartPointerDown = useCallback(
    (ref: ComunicadoTablePartRef, event?: ReactPointerEvent) => {
      if (!event) return;
      if (event.shiftKey) {
        selectBlock(block.id, { additive: true });
        return;
      }
      const samePartSelected =
        selectedId === block.id &&
        Boolean(selectedTablePart && selectedTablePart.kind === ref.kind);
      const contentPart = isCompositeContentPart("table_view", ref);
      const action = resolveCompositePartPointerAction({
        blockSelected: selectedId === block.id,
        samePartSelected,
        /* Tabela ainda não move frame no palco. */
        partAllowsMove: false,
        contentPart,
      });
      if (action === "part-move") return;
      if (action === "select-part") {
        selectTablePart(block.id, ref);
        requestRibbonTab(ref.kind === "frame" ? "shape" : "table");
        return;
      }
      beginBlockStageMoveDrag({
        event,
        block,
        isBlockSelected,
        selectedIds,
        selectedId,
        selectBlock,
        selectBlocksByIds,
        armMultiDragSelection,
        startDrag,
      });
    },
    [
      armMultiDragSelection,
      block,
      isBlockSelected,
      requestRibbonTab,
      selectBlock,
      selectBlocksByIds,
      selectTablePart,
      selectedId,
      selectedIds,
      selectedTablePart,
      startDrag,
    ],
  );

  const onPartDoubleClick = useCallback(
    (ref: ComunicadoTablePartRef) => {
      selectTablePart(block.id, ref);
      requestRibbonTab(ref.kind === "frame" ? "shape" : "table");
    },
    [block.id, requestRibbonTab, selectTablePart],
  );

  const interaction =
    selectedId === block.id
      ? {
          selectedPart: selectedTablePart,
          onPartPointerDown,
          onPartDoubleClick,
        }
      : null;

  return (
    <div
      className={["tdp-comunicado__block", "tdp-comunicado__block--table-view", className]
        .filter(Boolean)
        .join(" ")}
      style={style}
    >
      <TableViewBlockView
        block={block}
        interactive={Boolean(interaction)}
        loading={dataLoading}
        interaction={interaction}
      />
    </div>
  );
}

function EditorKpiViewBlock({
  block,
  style,
  className,
  dataLoading = false,
}: {
  block: ComunicadoKpiViewBlock;
  style: CSSProperties;
  className?: string;
  dataLoading?: boolean;
}) {
  const {
    selectedId,
    selectedKpiPart,
    editingKpiPart,
    selectedIds,
    isBlockSelected,
    selectBlock,
    selectBlocksByIds,
    selectKpiPart,
    beginEditKpiPart,
    commitKpiPartContent,
    cancelEditKpiPart,
    requestRibbonTab,
    updateBlock,
    startDrag,
    armMultiDragSelection,
  } = useComunicadoEditor();

  const onPartPointerDown = useCallback(
    (part: ComunicadoKpiPartRef, event?: ReactPointerEvent) => {
      if (!event) return;
      if (event.shiftKey) {
        selectBlock(block.id, { additive: true });
        return;
      }
      const samePartSelected =
        selectedId === block.id &&
        Boolean(selectedKpiPart && isKpiPartRefEqual(selectedKpiPart, part));
      const contentPart = isCompositeContentPart("kpi_view", part);
      const action = resolveCompositePartPointerAction({
        blockSelected: selectedId === block.id,
        samePartSelected,
        partAllowsMove: kpiPartAllowsMove(part),
        contentPart,
      });
      if (action === "part-move") return;
      if (action === "select-part") {
        selectKpiPart(block.id, part);
        if (part.kind === "metricCard") requestRibbonTab("data");
        else requestRibbonTab("shape");
        return;
      }
      beginBlockStageMoveDrag({
        event,
        block,
        isBlockSelected,
        selectedIds,
        selectedId,
        selectBlock,
        selectBlocksByIds,
        armMultiDragSelection,
        startDrag,
      });
    },
    [
      armMultiDragSelection,
      block,
      isBlockSelected,
      requestRibbonTab,
      selectBlock,
      selectBlocksByIds,
      selectKpiPart,
      selectedId,
      selectedIds,
      selectedKpiPart,
      startDrag,
    ],
  );

  const onPartDoubleClick = useCallback(
    (part: ComunicadoKpiPartRef) => {
      const same =
        selectedId === block.id &&
        selectedKpiPart &&
        isKpiPartRefEqual(selectedKpiPart, part);
      selectKpiPart(block.id, part);
      if (part.kind === "metricCard") {
        requestRibbonTab("data");
        return;
      }
      requestRibbonTab("shape");
      if (same && kpiPartAllowsEdit(part)) {
        beginEditKpiPart(block.id, part);
      }
    },
    [
      beginEditKpiPart,
      block.id,
      requestRibbonTab,
      selectKpiPart,
      selectedId,
      selectedKpiPart,
    ],
  );

  const onPartContentCommit = useCallback(
    (part: ComunicadoKpiPartRef, content: string) => {
      if (editingKpiPart && editingKpiPart.kind === part.kind) {
        commitKpiPartContent(content);
        return;
      }
      const nextParts = upsertKpiPartState(block.kpiParts, part, {
        content,
        visible: true,
      });
      const nextOptions = {
        ...block.kpiOptions,
        ...partsToKpiOptions(nextParts),
      };
      if (part.kind === "title") nextOptions.title = content.trim() || undefined;
      if (part.kind === "hint") nextOptions.subtitle = content.trim() || undefined;
      updateBlock(block.id, {
        kpiParts: nextParts,
        kpiOptions: nextOptions,
      } as Partial<ComunicadoBlock>);
    },
    [block, commitKpiPartContent, editingKpiPart, updateBlock],
  );

  const onPartMovePointerDown = useCallback(
    (ref: ComunicadoKpiPartRef, event: ReactPointerEvent) => {
      if (!kpiPartAllowsMove(ref)) return;
      const cardRoot = resolveKpiPartFrameRoot(event.currentTarget as HTMLElement, ref);
      if (!cardRoot) return;
      event.preventDefault();
      const rect = cardRoot.getBoundingClientRect();
      const elRect = (event.currentTarget as HTMLElement).getBoundingClientRect();
      let lastParts = block.kpiParts ?? {};
      if (!getKpiPartState(lastParts, ref)?.frame) {
        lastParts = materializeMissingKpiPartFramesFromRoot(cardRoot, lastParts);
      }
      const existing = getKpiPartState(lastParts, ref)?.frame;
      const origin = clampKpiPartFrame({
        x: existing?.x ?? ((elRect.left - rect.left) / Math.max(rect.width, 1)) * 100,
        y: existing?.y ?? ((elRect.top - rect.top) / Math.max(rect.height, 1)) * 100,
        w: existing?.w ?? (elRect.width / Math.max(rect.width, 1)) * 100,
        h: existing?.h ?? (elRect.height / Math.max(rect.height, 1)) * 100,
      });
      const startClientX = event.clientX;
      const startClientY = event.clientY;
      let dragged = false;

      const onMove = (ev: PointerEvent) => {
        const dx = ((ev.clientX - startClientX) / Math.max(rect.width, 1)) * 100;
        const dy = ((ev.clientY - startClientY) / Math.max(rect.height, 1)) * 100;
        if (!dragged && Math.abs(dx) + Math.abs(dy) < 0.4) return;
        dragged = true;
        const nextFrame = clampKpiPartFrame({
          ...origin,
          x: origin.x + dx,
          y: origin.y + dy,
        });
        lastParts = upsertKpiPartState(lastParts, ref, { frame: nextFrame });
        updateBlock(block.id, { kpiParts: lastParts } as Partial<ComunicadoBlock>);
      };

      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
      };
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    },
    [block.id, block.kpiParts, updateBlock],
  );

  const onPartResizePointerDown = useCallback(
    (
      ref: ComunicadoKpiPartRef,
      event: ReactPointerEvent,
      handle: ComunicadoKpiPartResizeHandle,
    ) => {
      if (!kpiPartAllowsResize(ref)) return;
      const cardRoot = resolveKpiPartFrameRoot(event.currentTarget as HTMLElement, ref);
      const host = (event.currentTarget as HTMLElement).closest("[data-kpi-part]");
      if (!cardRoot || !host) return;
      event.preventDefault();
      const rect = cardRoot.getBoundingClientRect();
      const elRect = host.getBoundingClientRect();
      let lastParts = block.kpiParts ?? {};
      if (!getKpiPartState(lastParts, ref)?.frame) {
        lastParts = materializeMissingKpiPartFramesFromRoot(cardRoot, lastParts);
      }
      const existing = getKpiPartState(lastParts, ref)?.frame;
      const origin = clampKpiPartFrame({
        x: existing?.x ?? ((elRect.left - rect.left) / Math.max(rect.width, 1)) * 100,
        y: existing?.y ?? ((elRect.top - rect.top) / Math.max(rect.height, 1)) * 100,
        w: existing?.w ?? (elRect.width / Math.max(rect.width, 1)) * 100,
        h: existing?.h ?? (elRect.height / Math.max(rect.height, 1)) * 100,
      });
      const startClientX = event.clientX;
      const startClientY = event.clientY;
      const originParts = lastParts;
      const originSize = { w: origin.w ?? 20, h: origin.h ?? 20 };
      const aspectRatio = originSize.w / Math.max(originSize.h, 0.1);
      let resized = false;

      const applyLive = (nextFrame: ReturnType<typeof clampKpiPartFrame>) => {
        let nextParts = upsertKpiPartState(originParts, ref, { frame: nextFrame });
        nextParts = scaleKpiPartTypographyOnResize(nextParts, ref, originSize, {
          w: nextFrame.w ?? originSize.w,
          h: nextFrame.h ?? originSize.h,
        });
        updateBlock(block.id, { kpiParts: nextParts } as Partial<ComunicadoBlock>);
      };

      const onMove = (ev: PointerEvent) => {
        const dx = ((ev.clientX - startClientX) / Math.max(rect.width, 1)) * 100;
        const dy = ((ev.clientY - startClientY) / Math.max(rect.height, 1)) * 100;
        if (!resized && Math.abs(dx) + Math.abs(dy) < 0.15) return;
        resized = true;
        const next = resizeFrameWithOptionalAspect(
          { x: origin.x, y: origin.y, w: originSize.w, h: originSize.h },
          dx,
          dy,
          handle,
          aspectRatio,
          ev.shiftKey,
        );
        applyLive(clampKpiPartFrame(next));
      };

      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
      };
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    },
    [block.id, block.kpiParts, updateBlock],
  );

  const onPartFrameChange = useCallback(
    (ref: ComunicadoKpiPartRef, frame: ComunicadoKpiPartFrame) => {
      if (!kpiPartAllowsResize(ref) && !kpiPartAllowsMove(ref)) return;
      const nextParts = upsertKpiPartState(block.kpiParts, ref, { frame });
      updateBlock(block.id, { kpiParts: nextParts } as Partial<ComunicadoBlock>);
    },
    [block.id, block.kpiParts, updateBlock],
  );

  const onPartCornerAdjustPointerDown = useCallback(
    (ref: ComunicadoKpiPartRef, event: ReactPointerEvent) => {
      if (ref.kind !== "card" && !kpiPartAllowsFrame(ref)) return;
      const host = (event.currentTarget as HTMLElement).closest("[data-kpi-part]");
      if (!host) return;
      event.preventDefault();
      const rect = host.getBoundingClientRect();
      const shortSide = Math.min(Math.max(1, rect.width), Math.max(1, rect.height));
      const originPx =
        getKpiPartState(block.kpiParts, ref)?.style?.borderRadius ??
        (ref.kind === "icon" ? KPI_ICON_DEFAULT_RADIUS_PX : 0);
      const startAdj = borderRadiusPxToKpiCornerAdj(originPx, shortSide);
      const startLocalX = ((event.clientX - rect.left) / Math.max(rect.width, 1)) * 100;
      const startRaw = kpiPartCornerAdjFromLocalX(startLocalX);
      let lastParts = block.kpiParts;

      const onMove = (ev: PointerEvent) => {
        const localX = ((ev.clientX - rect.left) / Math.max(rect.width, 1)) * 100;
        const rawNow = kpiPartCornerAdjFromLocalX(localX);
        const nextAdj = Math.min(
          0.5,
          Math.max(0, startAdj + (rawNow - startRaw)),
        );
        const nextRadius = kpiCornerAdjToBorderRadiusPx(nextAdj, shortSide);
        lastParts = upsertKpiPartState(lastParts, ref, {
          style: { borderRadius: nextRadius },
        });
        updateBlock(block.id, { kpiParts: lastParts } as Partial<ComunicadoBlock>);
      };

      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
      };
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    },
    [block.id, block.kpiParts, updateBlock],
  );

  const interaction =
    selectedId === block.id
      ? {
          selectedPart: selectedKpiPart,
          editingPart: editingKpiPart,
          onPartPointerDown,
          onPartDoubleClick,
          onPartContentCommit,
          onPartEditCancel: cancelEditKpiPart,
          onPartMovePointerDown,
          onPartResizePointerDown,
          onPartFrameChange,
          onPartCornerAdjustPointerDown,
        }
      : null;

  return (
    <div
      className={["tdp-comunicado__block", "tdp-comunicado__block--kpi-view", className]
        .filter(Boolean)
        .join(" ")}
      style={style}
    >
      <KpiViewBlockView
        block={block}
        interactive={Boolean(interaction)}
        loading={dataLoading}
        interaction={interaction}
      />
    </div>
  );
}

function EditorInputBlock({
  block,
  fontScale,
  className,
  configBlocks,
  patchInputBlock,
  scheduleInputFilterRefreshById,
  refreshingSourceIds,
}: {
  block: ComunicadoInputBlock;
  fontScale?: number;
  className?: string;
  configBlocks: ComunicadoBlock[];
  patchInputBlock: (blockId: string, inputPatch: Partial<ComunicadoInputBlock["input"]>) => void;
  scheduleInputFilterRefreshById: (blockId: string) => void;
  refreshingSourceIds: string[];
}) {
  const {
    selectedId,
    selectedIds,
    isBlockSelected,
    selectedInputPart,
    selectBlock,
    selectBlocksByIds,
    selectInputPart,
    requestRibbonTab,
    updateBlock,
    startDrag,
    armMultiDragSelection,
  } = useComunicadoEditor();

  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  useEffect(() => {
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, []);

  const linkedIds = useMemo(
    () => resolveInputRefreshSourceIds(block, configBlocks),
    [block, configBlocks],
  );

  const dataLoading = useMemo(
    () => linkedIds.some((id) => refreshingSourceIds.includes(id)),
    [linkedIds, refreshingSourceIds],
  );

  const decorated = useMemo(() => {
    const scope = resolveInputTargetScope(block.input);
    const fetchable = configBlocks.filter((item) => isFetchableDataBlockType(item.type));
    const targets =
      scope === "slide"
        ? fetchable
        : fetchable.filter((item) => (block.input.targetSourceIds ?? []).includes(item.id));
    const schemas: InputParamSchema[] = targets
      .map((item) => {
        const operationId =
          "dataBinding" in item && item.dataBinding?.operationId
            ? item.dataBinding.operationId
            : "";
        const route = routes.find((entry) => entry.operationId === operationId);
        return (route?.paramSchema ?? {}) as InputParamSchema;
      })
      .filter((schema) => Object.keys(schema).length > 0);
    const field = block.input.paramKey
      ? resolveInputParamSchemaField(block.input.paramKey, schemas)
      : null;
    return {
      ...block,
      input: {
        ...block.input,
        resolvedField: field ?? undefined,
        paramAvailable: Boolean(field),
      },
    } as ComunicadoInputBlock & {
      input: ComunicadoInputBlock["input"] & {
        resolvedField?: InputParamSchema[string];
        paramAvailable?: boolean;
      };
    };
  }, [block, configBlocks, routes]);

  const onPartPointerDown = useCallback(
    (part: ComunicadoInputPartRef, event?: ReactPointerEvent) => {
      if (!event) return;
      if (event.shiftKey) {
        selectBlock(block.id, { additive: true });
        return;
      }
      const blockSelected = selectedId === block.id;
      const samePartSelected =
        blockSelected && Boolean(selectedInputPart && selectedInputPart.kind === part.kind);
      const contentPart = isCompositeContentPart("input", part);
      const action = resolveCompositePartPointerAction({
        blockSelected,
        samePartSelected,
        partAllowsMove: inputPartAllowsMove(part),
        contentPart,
      });
      if (action === "part-move") return;
      if (action === "select-part") {
        selectInputPart(block.id, part);
        requestRibbonTab("shape");
        return;
      }
      beginBlockStageMoveDrag({
        event,
        block,
        isBlockSelected,
        selectedIds,
        selectedId,
        selectBlock,
        selectBlocksByIds,
        armMultiDragSelection,
        startDrag,
      });
    },
    [
      armMultiDragSelection,
      block,
      isBlockSelected,
      requestRibbonTab,
      selectBlock,
      selectBlocksByIds,
      selectInputPart,
      selectedId,
      selectedIds,
      selectedInputPart,
      startDrag,
    ],
  );

  const onPartDoubleClick = useCallback(
    (part: ComunicadoInputPartRef) => {
      selectInputPart(block.id, part);
      requestRibbonTab("shape");
    },
    [block.id, requestRibbonTab, selectInputPart],
  );

  const onPartMovePointerDown = useCallback(
    (ref: ComunicadoInputPartRef, event: ReactPointerEvent) => {
      if (!inputPartAllowsMove(ref)) return;
      const root = resolveInputPartFrameRoot(event.currentTarget as HTMLElement);
      if (!root) return;
      event.preventDefault();
      const rect = root.getBoundingClientRect();
      const elRect = (event.currentTarget as HTMLElement).getBoundingClientRect();
      // Sempre materializar irmãos sem frame — evita híbrido badge-framed / control-flow.
      let lastParts = materializeMissingInputPartFramesFromRoot(
        root,
        block.inputParts ?? {},
      );
      const existing = getInputPartState(lastParts, ref)?.frame;
      const origin = clampInputPartFrame({
        x: existing?.x ?? ((elRect.left - rect.left) / Math.max(rect.width, 1)) * 100,
        y: existing?.y ?? ((elRect.top - rect.top) / Math.max(rect.height, 1)) * 100,
        w: existing?.w ?? (elRect.width / Math.max(rect.width, 1)) * 100,
        h: existing?.h ?? (elRect.height / Math.max(rect.height, 1)) * 100,
      });
      const startClientX = event.clientX;
      const startClientY = event.clientY;
      let dragged = false;

      const onMove = (ev: PointerEvent) => {
        const dx = ((ev.clientX - startClientX) / Math.max(rect.width, 1)) * 100;
        const dy = ((ev.clientY - startClientY) / Math.max(rect.height, 1)) * 100;
        if (!dragged && Math.abs(dx) + Math.abs(dy) < 0.4) return;
        dragged = true;
        const nextFrame = clampInputPartFrame({
          ...origin,
          x: origin.x + dx,
          y: origin.y + dy,
        });
        lastParts = upsertInputPartState(lastParts, ref, { frame: nextFrame });
        updateBlock(block.id, { inputParts: lastParts } as Partial<ComunicadoBlock>);
      };

      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        // Clique sem arrastar na caixa → foca o valor (edição).
        if (!dragged && ref.kind === "control") {
          const host = event.currentTarget as HTMLElement;
          const form = host.querySelector("input, select, textarea");
          if (form instanceof HTMLElement) form.focus();
        }
      };
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    },
    [block.id, block.inputParts, updateBlock],
  );

  const onPartResizePointerDown = useCallback(
    (
      ref: ComunicadoInputPartRef,
      event: ReactPointerEvent,
      handle: ComunicadoInputPartResizeHandle,
    ) => {
      if (!inputPartAllowsResize(ref)) return;
      const root = resolveInputPartFrameRoot(event.currentTarget as HTMLElement);
      const host = (event.currentTarget as HTMLElement).closest("[data-input-part]");
      if (!root || !host) return;
      event.preventDefault();
      const rect = root.getBoundingClientRect();
      const elRect = host.getBoundingClientRect();
      let lastParts = materializeMissingInputPartFramesFromRoot(
        root,
        block.inputParts ?? {},
      );
      const existing = getInputPartState(lastParts, ref)?.frame;
      const origin = clampInputPartFrame({
        x: existing?.x ?? ((elRect.left - rect.left) / Math.max(rect.width, 1)) * 100,
        y: existing?.y ?? ((elRect.top - rect.top) / Math.max(rect.height, 1)) * 100,
        w: existing?.w ?? (elRect.width / Math.max(rect.width, 1)) * 100,
        h: existing?.h ?? (elRect.height / Math.max(rect.height, 1)) * 100,
      });
      const startClientX = event.clientX;
      const startClientY = event.clientY;
      const beforeSize = { w: origin.w ?? 20, h: origin.h ?? 20 };

      const onMove = (ev: PointerEvent) => {
        const dx = ((ev.clientX - startClientX) / Math.max(rect.width, 1)) * 100;
        const dy = ((ev.clientY - startClientY) / Math.max(rect.height, 1)) * 100;
        const nextFrame = resizeInputPartFrame(origin, handle, dx, dy);
        lastParts = upsertInputPartState(lastParts, ref, { frame: nextFrame });
        lastParts = scaleInputPartTypographyOnResize(lastParts, ref, beforeSize, {
          w: nextFrame.w ?? beforeSize.w,
          h: nextFrame.h ?? beforeSize.h,
        });
        updateBlock(block.id, { inputParts: lastParts } as Partial<ComunicadoBlock>);
      };

      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
      };
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    },
    [block.id, block.inputParts, updateBlock],
  );

  /**
   * Interaction sempre ligada no editor: 1º clique no valor (hit-through) seleciona o bloco;
   * com o grupo ativo, clique na caixa seleciona a parte; parte control ativa → edita.
   * Kiosk/presentação passa `inputInteraction` null e edita direto.
   */
  const interaction = useMemo(
    () => ({
      selectedPart: selectedId === block.id ? selectedInputPart : null,
      onPartPointerDown,
      onPartDoubleClick,
      onPartMovePointerDown,
      onPartResizePointerDown,
    }),
    [
      block.id,
      onPartDoubleClick,
      onPartMovePointerDown,
      onPartPointerDown,
      onPartResizePointerDown,
      selectedId,
      selectedInputPart,
    ],
  );

  return (
    <ComunicadoBlockView
      block={decorated}
      fontScale={fontScale}
      interactive
      inputsInteractive
      embedded
      className={className}
      dataLoading={dataLoading}
      inputInteraction={interaction}
      onInputValueChange={(_blockId, value) => {
        patchInputBlock(block.id, { defaultValue: value });
        scheduleInputFilterRefreshById(block.id);
      }}
    />
  );
}

function resolveEditorDataParamValueLabel(key: string, value: string): string {
  const fromEnum = ENUM_OPTION_LABELS[key]?.[value];
  if (fromEnum) return fromEnum;
  const fromPreset = DATE_RANGE_PRESET_OPTIONS.find((item) => item.value === value)?.label;
  if (key === "dateRangePreset" && fromPreset) return fromPreset;
  if (value === "true") return "Sim";
  if (value === "false") return "Não";
  return value;
}

/** Renderização de blocos no editor — mídia autenticada e controles de vídeo. */
export function ComunicadoEditorBlockView({
  block,
  fontScale = 1,
  className = "",
  isSelected = false,
  isEditingText = false,
  dataLoading = false,
}: Props) {
  const {
    updateBlock,
    config,
    patchInputBlock,
    scheduleInputFilterRefreshById,
    refreshingSourceIds,
  } = useComunicadoEditor();
  const slideDataFilters = config.dataFilters ?? null;
  const dataParamLabelProps = useMemo(
    () => ({
      slideDataFilters,
      labelForDataParamKey: (key: string) => resolveParamFieldLabel(key),
      labelForDataParamValue: resolveEditorDataParamValueLabel,
    }),
    [slideDataFilters],
  );
  const style: CSSProperties = {
    ...blockCssStyle(block, { fontScale }),
    position: "relative",
    left: undefined,
    top: undefined,
    width: "100%",
    height: "100%",
    // Rotação fica no wrap de seleção (handles/outline alinhados ao bloco).
    transform: undefined,
  };

  if (isComunicadoVisualBoxBlock(block)) {
    return (
      <ComunicadoEditorVisualBoxBlock
        block={block}
        fontScale={fontScale}
        className={className}
        isSelected={isSelected}
        isEditingText={isEditingText}
      />
    );
  }

  if (block.type === "image") {
    return <EditorImageBlock block={block} style={style} className={className} isSelected={isSelected} />;
  }

  if (block.type === "video") {
    return (
      <div style={{ position: "relative", width: "100%", height: "100%" }}>
        <ComunicadoEditorVideoPreview block={block} style={style} className={className} />
      </div>
    );
  }

  if (block.type === "chart_view") {
    return (
      <EditorChartViewBlock
        block={block}
        style={style}
        className={className}
        dataLoading={dataLoading}
      />
    );
  }

  if (block.type === "table_view") {
    return (
      <EditorTableViewBlock
        block={block}
        style={style}
        className={className}
        dataLoading={dataLoading}
      />
    );
  }

  if (block.type === "canvas_table") {
    return (
      <ComunicadoBlockView
        block={block}
        fontScale={fontScale}
        interactive
        embedded
        className={className}
        onCanvasTableCellChange={(row, col, value) => {
          const cells = block.cells.map((currentRow) => [...currentRow]);
          cells[row]![col] = value;
          updateBlock(block.id, { cells });
        }}
      />
    );
  }

  if (block.type === "input") {
    return (
      <EditorInputBlock
        block={block as ComunicadoInputBlock}
        fontScale={fontScale}
        className={className}
        configBlocks={config.blocks ?? []}
        patchInputBlock={patchInputBlock}
        scheduleInputFilterRefreshById={scheduleInputFilterRefreshById}
        refreshingSourceIds={refreshingSourceIds}
      />
    );
  }

  if (block.type === "kpi_view") {
    return (
      <EditorKpiViewBlock
        block={block}
        style={style}
        className={className}
        dataLoading={dataLoading}
      />
    );
  }

  if (block.type === "icon") {
    return (
      <div style={{ position: "relative", width: "100%", height: "100%" }}>
        <ComunicadoBlockView
          block={block}
          fontScale={fontScale}
          interactive
          embedded
          className={className}
          dataLoading={dataLoading}
        />
      </div>
    );
  }

  return (
    <ComunicadoBlockView
      block={block}
      fontScale={fontScale}
      interactive
      embedded
      className={className}
      dataLoading={dataLoading}
      {...dataParamLabelProps}
    />
  );
}
