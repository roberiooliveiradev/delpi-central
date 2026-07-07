import { ComunicadoBlockView, frameStyle } from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "./comunicadoEditorContext";

const FONT_SCALE = 0.35;

export function ComunicadoComposerCanvas() {
  const { blocks, selectedId, setSelectedId, bgPreviewStyle, canvasRef, startDrag } = useComunicadoEditor();

  return (
    <div className="td-composer td-composer--deck">
      <div className="td-composer__canvas-wrap td-composer__canvas-wrap--full">
        <div ref={canvasRef} className="td-composer__canvas" style={bgPreviewStyle}>
          {blocks.map((block) => {
            const isSelected = block.id === selectedId;
            return (
              <div
                key={block.id}
                className={`td-composer__block-wrap${isSelected ? " td-composer__block-wrap--selected" : ""}`}
                style={frameStyle(block.frame)}
                onPointerDown={(event) => {
                  setSelectedId(block.id);
                  startDrag(event, block, "move");
                }}
              >
                <ComunicadoBlockView
                  block={block}
                  fontScale={FONT_SCALE}
                  interactive
                  embedded
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
