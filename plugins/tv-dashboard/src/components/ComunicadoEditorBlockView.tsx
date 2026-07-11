import {
  ChartViewBlockView,
  ComunicadoBlockView,
  ComunicadoMediaPlaceholder,
  blockCssStyle,
  chartOptionsToParts,
  chartPartAllowsMove,
  clampChartPartFrame,
  comunicadoImageCropCssProperties,
  getChartPartState,
  isComunicadoVisualBoxBlock,
  mergeComunicadoChartOptions,
  partsToChartOptions,
  upsertChartPartState,
  type ComunicadoBlock,
  type ComunicadoChartPartRef,
  type ComunicadoChartViewBlock,
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
  block: Extract<ComunicadoBlock, { type: "image" }>;
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
    selectChartPart,
    beginEditChartPart,
    commitChartPartContent,
    cancelEditChartPart,
    requestRibbonTab,
    updateBlock,
  } = useComunicadoEditor();

  const onPartPointerDown = useCallback(
    (ref: ComunicadoChartPartRef) => {
      selectChartPart(block.id, ref);
      requestRibbonTab("format");
    },
    [block.id, requestRibbonTab, selectChartPart],
  );

  const onPartDoubleClick = useCallback(
    (ref: ComunicadoChartPartRef) => {
      if (ref.kind === "title" || ref.kind === "legend" || ref.kind === "axisTitle") {
        beginEditChartPart(block.id, ref);
        requestRibbonTab("format");
      } else {
        selectChartPart(block.id, ref);
        requestRibbonTab("format");
      }
    },
    [beginEditChartPart, block.id, requestRibbonTab, selectChartPart],
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
      const chartRoot = (event.currentTarget as HTMLElement).closest(".delpi-ui-series-chart");
      if (!chartRoot) return;
      event.preventDefault();
      const rect = chartRoot.getBoundingClientRect();
      const elRect = (event.currentTarget as HTMLElement).getBoundingClientRect();
      const existing = getChartPartState(block.chartParts, ref)?.frame;
      const origin = existing ?? {
        x: ((elRect.left - rect.left) / Math.max(rect.width, 1)) * 100,
        y: ((elRect.top - rect.top) / Math.max(rect.height, 1)) * 100,
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
        }
      : {
          selectedPart: null,
          editingPart: null,
          onPartPointerDown,
          onPartDoubleClick,
          onPartContentCommit,
          onPartEditCancel: cancelEditChartPart,
          onPartMovePointerDown,
        };

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
