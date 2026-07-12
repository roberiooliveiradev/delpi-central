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
  resizeChartPartFrame,
  resolveChartPartFrameRoot,
  upsertChartPartState,
  KpiViewBlockView,
  KPI_ICON_DEFAULT_RADIUS_PX,
  clampKpiPartFrame,
  getKpiPartState,
  kpiPartAllowsEdit,
  kpiPartAllowsFrame,
  kpiPartAllowsMove,
  kpiPartAllowsResize,
  partsToKpiOptions,
  resizeKpiPartFrame,
  resolveKpiPartFrameRoot,
  upsertKpiPartState,
  type ComunicadoBlock,
  type ComunicadoChartPartFrame,
  type ComunicadoChartPartRef,
  type ComunicadoChartPartResizeHandle,
  type ComunicadoChartViewBlock,
  type ComunicadoKpiPartFrame,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiPartResizeHandle,
  type ComunicadoKpiViewBlock,
  type ComunicadoMediaBlock,
  type ComunicadoTablePartRef,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";
import { useCallback, type CSSProperties, type PointerEvent as ReactPointerEvent } from "react";

import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
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
    selectedChartPart,
    editingChartPart,
    selectBlock,
    selectChartPart,
    beginEditChartPart,
    commitChartPartContent,
    cancelEditChartPart,
    requestRibbonTab,
    updateBlock,
    startDrag,
  } = useComunicadoEditor();

  /**
   * Clique: seleciona a parte (paridade com KPI). chartArea move o bloco.
   * Parte já selecionada + movable: move trata o drag (não re-seleciona).
   * Com o gráfico não selecionado, `interaction` fica null para o clique subir ao compositor.
   */
  const onPartPointerDown = useCallback(
    (ref: ComunicadoChartPartRef, event?: ReactPointerEvent) => {
      if (ref.kind === "chartArea" && event) {
        selectBlock(block.id);
        startDrag(event, block, "move");
        return;
      }
      if (
        selectedId === block.id &&
        selectedChartPart &&
        isChartPartRefEqual(selectedChartPart, ref) &&
        chartPartAllowsMove(ref)
      ) {
        return;
      }
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
    },
    [
      block,
      requestRibbonTab,
      selectBlock,
      selectChartPart,
      selectedChartPart,
      selectedId,
      startDrag,
    ],
  );

  /** Duplo clique na parte já selecionada: abre edição inline quando editável. */
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
      if (editingChartPart && ref.kind === editingChartPart.kind) {
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
      let lastParts = upsertChartPartState(block.chartParts, ref, { frame: origin });

      const onMove = (ev: PointerEvent) => {
        const dx = ((ev.clientX - startClientX) / Math.max(rect.width, 1)) * 100;
        const dy = ((ev.clientY - startClientY) / Math.max(rect.height, 1)) * 100;
        const nextFrame = resizeChartPartFrame(origin, handle, dx, dy);
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
  const { selectedId, selectedTablePart, selectBlock, selectTablePart, requestRibbonTab, startDrag } =
    useComunicadoEditor();

  const onPartPointerDown = useCallback(
    (ref: ComunicadoTablePartRef, event?: ReactPointerEvent) => {
      selectBlock(block.id);
      if (ref.kind === "frame" && event) {
        startDrag(event, block, "move");
      }
    },
    [block, selectBlock, startDrag],
  );

  const onPartDoubleClick = useCallback(
    (ref: ComunicadoTablePartRef) => {
      selectTablePart(block.id, ref);
      requestRibbonTab("table");
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
    selectBlock,
    selectKpiPart,
    beginEditKpiPart,
    commitKpiPartContent,
    cancelEditKpiPart,
    requestRibbonTab,
    updateBlock,
    startDrag,
  } = useComunicadoEditor();

  const onPartPointerDown = useCallback(
    (part: ComunicadoKpiPartRef, event?: ReactPointerEvent) => {
      /* Card = moldura do bloco: arrastar move o KPI. */
      if (part.kind === "card" && event) {
        selectBlock(block.id);
        startDrag(event, block, "move");
        return;
      }
      /* Parte já selecionada: move trata o drag (não re-seleciona). */
      if (
        selectedId === block.id &&
        selectedKpiPart &&
        selectedKpiPart.kind === part.kind &&
        kpiPartAllowsMove(part)
      ) {
        return;
      }
      selectBlock(block.id);
      if (kpiPartAllowsFrame(part)) {
        selectKpiPart(block.id, part);
        requestRibbonTab("shape");
      }
    },
    [block, requestRibbonTab, selectBlock, selectKpiPart, selectedId, selectedKpiPart, startDrag],
  );

  const onPartDoubleClick = useCallback(
    (part: ComunicadoKpiPartRef) => {
      const same =
        selectedId === block.id &&
        selectedKpiPart &&
        selectedKpiPart.kind === part.kind;
      selectKpiPart(block.id, part);
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
      const cardRoot = resolveKpiPartFrameRoot(event.currentTarget as HTMLElement);
      if (!cardRoot) return;
      event.preventDefault();
      const rect = cardRoot.getBoundingClientRect();
      const elRect = (event.currentTarget as HTMLElement).getBoundingClientRect();
      const existing = getKpiPartState(block.kpiParts, ref)?.frame;
      const origin = clampKpiPartFrame({
        x: existing?.x ?? ((elRect.left - rect.left) / Math.max(rect.width, 1)) * 100,
        y: existing?.y ?? ((elRect.top - rect.top) / Math.max(rect.height, 1)) * 100,
        w: existing?.w ?? (elRect.width / Math.max(rect.width, 1)) * 100,
        h: existing?.h ?? (elRect.height / Math.max(rect.height, 1)) * 100,
      });
      const startClientX = event.clientX;
      const startClientY = event.clientY;
      let lastParts = upsertKpiPartState(block.kpiParts, ref, { frame: origin });
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
      const cardRoot = resolveKpiPartFrameRoot(event.currentTarget as HTMLElement);
      const host = (event.currentTarget as HTMLElement).closest("[data-kpi-part]");
      if (!cardRoot || !host) return;
      event.preventDefault();
      const rect = cardRoot.getBoundingClientRect();
      const elRect = host.getBoundingClientRect();
      const existing = getKpiPartState(block.kpiParts, ref)?.frame;
      const origin = clampKpiPartFrame({
        x: existing?.x ?? ((elRect.left - rect.left) / Math.max(rect.width, 1)) * 100,
        y: existing?.y ?? ((elRect.top - rect.top) / Math.max(rect.height, 1)) * 100,
        w: existing?.w ?? (elRect.width / Math.max(rect.width, 1)) * 100,
        h: existing?.h ?? (elRect.height / Math.max(rect.height, 1)) * 100,
      });
      const startClientX = event.clientX;
      const startClientY = event.clientY;
      let lastParts = upsertKpiPartState(block.kpiParts, ref, { frame: origin });

      const onMove = (ev: PointerEvent) => {
        const dx = ((ev.clientX - startClientX) / Math.max(rect.width, 1)) * 100;
        const dy = ((ev.clientY - startClientY) / Math.max(rect.height, 1)) * 100;
        const nextFrame = resizeKpiPartFrame(origin, handle, dx, dy);
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
      if (!kpiPartAllowsFrame(ref)) return;
      event.preventDefault();
      const startClientX = event.clientX;
      const startClientY = event.clientY;
      const origin =
        getKpiPartState(block.kpiParts, ref)?.style?.borderRadius ??
        (ref.kind === "icon" ? KPI_ICON_DEFAULT_RADIUS_PX : 0);
      let lastParts = block.kpiParts;

      const onMove = (ev: PointerEvent) => {
        const delta = ((ev.clientX - startClientX) + (ev.clientY - startClientY)) / 2;
        const nextRadius = Math.max(0, Math.min(64, Math.round(origin + delta * 0.35)));
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

/** Renderização de blocos no editor — mídia autenticada e controles de vídeo. */
export function ComunicadoEditorBlockView({
  block,
  fontScale = 1,
  className = "",
  isSelected = false,
  isEditingText = false,
  dataLoading = false,
}: Props) {
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
    />
  );
}
