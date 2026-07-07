import { comunicadoBackgroundCssProperties, frameStyle } from "@delpi/tv-dashboard-presentation";
import { useMemo } from "react";

import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoEditorBlockView } from "./ComunicadoEditorBlockView";
import type { BlockDragMode } from "./useCanvasBlockInteraction";

const FONT_SCALE = 0.35;

const BLOCK_RESIZE_HANDLES: Array<{
  mode: Exclude<BlockDragMode, "move">;
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

export function ComunicadoComposerCanvas() {
  const { blocks, selectedId, setSelectedId, editingTextId, canvasRef, startDrag, dataPreviewLoading } =
    useComunicadoEditor();
  const canvasStyle = useCanvasBackgroundStyle();

  return (
    <div className="td-composer td-composer--deck">
      <div className="td-composer__canvas-wrap td-composer__canvas-wrap--full">
        <div
          ref={canvasRef}
          className="td-composer__canvas"
          style={canvasStyle}
          onPointerDown={(event) => {
            if (event.target !== event.currentTarget) return;
            setSelectedId(null);
          }}
        >
          {blocks.map((block) => {
            const isSelected = block.id === selectedId;
            return (
              <div
                key={block.id}
                className={`td-composer__block-wrap${isSelected ? " td-composer__block-wrap--selected" : ""}`}
                style={frameStyle(block.frame)}
                onPointerDown={(event) => {
                  event.stopPropagation();
                  setSelectedId(block.id);
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
                  fontScale={FONT_SCALE}
                  isSelected={isSelected}
                  isEditingText={editingTextId === block.id}
                  className={isSelected ? "td-composer__block--selected" : ""}
                  dataLoading={dataPreviewLoading}
                />
                {isSelected && editingTextId !== block.id ? (
                  <>
                    {BLOCK_RESIZE_HANDLES.map(({ mode, position, label }) => (
                      <button
                        key={mode}
                        type="button"
                        className={`td-composer__resize td-composer__resize--${position}`}
                        aria-label={label}
                        onPointerDown={(event) => startDrag(event, block, mode)}
                      />
                    ))}
                  </>
                ) : null}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
