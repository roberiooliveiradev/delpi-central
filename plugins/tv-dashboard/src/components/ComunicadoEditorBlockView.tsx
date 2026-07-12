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
  kpiPartAllowsEdit,
  partsToKpiOptions,
  upsertKpiPartState,
  type ComunicadoBlock,
  type ComunicadoChartPartFrame,
  type ComunicadoChartPartRef,
  type ComunicadoChartPartResizeHandle,
  type ComunicadoChartViewBlock,
  type ComunicadoKpiPartRef,
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
  } = useComunicadoEditor();

  /**
   * Clique simples no gráfico já selecionado: mantém o grupo `chart_view`
   * (limpa subseleção). Arraste de parte móvel só se a mesma parte já estiver ativa.
   * Com o gráfico não selecionado, `interaction` fica null para o clique subir ao compositor.
   */
  const onPartPointerDown = useCallback(
    (ref: ComunicadoChartPartRef) => {
      if (
        selectedId === block.id &&
        selectedChartPart &&
        isChartPartRefEqual(selectedChartPart, ref) &&
        chartPartAllowsMove(ref)
      ) {
        return;
      }
      selectBlock(block.id);
    },
    [block.id, selectBlock, selectedChartPart, selectedId],
  );

  /** Duplo clique: acessa a parte; texto já selecionado abre edição inline. */
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

  /** Partes só interceptam ponteiro com o grupo já selecionado (1º clique = grupo). */
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
      <ChartViewBlockView block={block} interactive loading={dataLoading} interaction={interaction} />
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
  const { selectedId, selectedTablePart, selectBlock, selectTablePart, requestRibbonTab } =
    useComunicadoEditor();

  const onPartPointerDown = useCallback(
    (_ref: ComunicadoTablePartRef) => {
      selectBlock(block.id);
    },
    [block.id, selectBlock],
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
      <TableViewBlockView block={block} interactive loading={dataLoading} interaction={interaction} />
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
  } = useComunicadoEditor();

  const onPartPointerDown = useCallback(
    (_part: ComunicadoKpiPartRef) => {
      selectBlock(block.id);
    },
    [block.id, selectBlock],
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

  const interaction =
    selectedId === block.id
      ? {
          selectedPart: selectedKpiPart,
          editingPart: editingKpiPart,
          onPartPointerDown,
          onPartDoubleClick,
          onPartContentCommit,
          onPartEditCancel: cancelEditKpiPart,
        }
      : null;

  return (
    <div
      className={["tdp-comunicado__block", "tdp-comunicado__block--kpi-view", className]
        .filter(Boolean)
        .join(" ")}
      style={style}
    >
      <KpiViewBlockView block={block} interactive loading={dataLoading} interaction={interaction} />
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
  const resolvedClassName = [
    className,
    block.style?.boxShadow?.trim() ? "tdp-comunicado__block--with-shadow" : "",
  ]
    .filter(Boolean)
    .join(" ");
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
        className={resolvedClassName}
        isSelected={isSelected}
        isEditingText={isEditingText}
      />
    );
  }

  if (block.type === "image") {
    return <EditorImageBlock block={block} style={style} className={resolvedClassName} isSelected={isSelected} />;
  }

  if (block.type === "video") {
    return (
      <div style={{ position: "relative", width: "100%", height: "100%" }}>
        <ComunicadoEditorVideoPreview block={block} style={style} className={resolvedClassName} />
      </div>
    );
  }

  if (block.type === "chart_view") {
    return (
      <EditorChartViewBlock
        block={block}
        style={style}
        className={resolvedClassName}
        dataLoading={dataLoading}
      />
    );
  }

  if (block.type === "table_view") {
    return (
      <EditorTableViewBlock
        block={block}
        style={style}
        className={resolvedClassName}
        dataLoading={dataLoading}
      />
    );
  }

  if (block.type === "kpi_view") {
    return (
      <EditorKpiViewBlock
        block={block}
        style={style}
        className={resolvedClassName}
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
          className={resolvedClassName}
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
      className={resolvedClassName}
      dataLoading={dataLoading}
    />
  );
}
