import { frameStyle } from "@delpi/tv-dashboard-presentation";
import { useMemo } from "react";

import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoEditorBlockView } from "./ComunicadoEditorBlockView";

const FONT_SCALE = 0.35;

function useCanvasBackgroundStyle() {
  const { background } = useComunicadoEditor();
  const imageApiUrl = background.type === "image" ? background.url : undefined;
  const { src: imageBlobUrl } = useAuthenticatedBlobUrl(imageApiUrl);

  return useMemo(() => {
    if (background.type === "image" && imageBlobUrl) {
      return {
        backgroundImage: `url(${imageBlobUrl})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      };
    }
    if (background.type === "color") {
      return { backgroundColor: background.value };
    }
    return { backgroundColor: "#0f172a" };
  }, [background, imageBlobUrl]);
}

export function ComunicadoComposerCanvas() {
  const { blocks, selectedId, setSelectedId, editingTextId, canvasRef, startDrag } =
    useComunicadoEditor();
  const canvasStyle = useCanvasBackgroundStyle();

  return (
    <div className="td-composer td-composer--deck">
      <div className="td-composer__canvas-wrap td-composer__canvas-wrap--full">
        <div ref={canvasRef} className="td-composer__canvas" style={canvasStyle}>
          {blocks.map((block) => {
            const isSelected = block.id === selectedId;
            return (
              <div
                key={block.id}
                className={`td-composer__block-wrap${isSelected ? " td-composer__block-wrap--selected" : ""}`}
                style={frameStyle(block.frame)}
                onPointerDown={(event) => {
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
                />
                {isSelected ? (
                  <>
                    <button
                      type="button"
                      className="td-composer__resize td-composer__resize--se"
                      aria-label="Redimensionar"
                      onPointerDown={(event) => startDrag(event, block, "resize-se")}
                    />
                    <button
                      type="button"
                      className="td-composer__resize td-composer__resize--e"
                      aria-label="Redimensionar largura"
                      onPointerDown={(event) => startDrag(event, block, "resize-e")}
                    />
                    <button
                      type="button"
                      className="td-composer__resize td-composer__resize--s"
                      aria-label="Redimensionar altura"
                      onPointerDown={(event) => startDrag(event, block, "resize-s")}
                    />
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
