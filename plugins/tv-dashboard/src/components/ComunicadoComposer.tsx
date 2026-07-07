import { ComunicadoBlockView, frameStyle } from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "./comunicadoEditorContext";

const FONT_SCALE = 0.35;

type Labels = Record<string, string>;

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

export function ComunicadoElementPanel({ labels = {} }: { labels?: Labels }) {
  const {
    selected,
    uploading,
    background,
    updateSelected,
    updateSelectedStyle,
    removeSelected,
    moveLayer,
    triggerUpload,
    setBackgroundColor,
  } = useComunicadoEditor();

  const isTextBlock = selected?.type === "heading" || selected?.type === "text";
  const isMediaBlock = selected?.type === "image" || selected?.type === "video";
  const isShapeBlock = selected?.type === "shape";

  return (
    <div className="td-deck-tabs__grid">
      <div className="td-deck-tabs__block">
        <h4 className="td-deck-tabs__block-title">{labels.comunicadoBlocks ?? "Elemento selecionado"}</h4>
        {!selected ? (
          <p className="td-subtitle">Selecione um elemento no slide ou arraste para posicionar.</p>
        ) : (
          <>
            <p className="td-subtitle">Tipo: {selected.type}</p>

            {isTextBlock && (
              <>
                <div className="td-field">
                  <label htmlFor="td-block-content">Conteúdo</label>
                  <textarea
                    id="td-block-content"
                    rows={2}
                    value={selected.content}
                    onChange={(e) => updateSelected({ content: e.target.value } as Partial<typeof selected>)}
                  />
                </div>
                <div className="td-field">
                  <label htmlFor="td-block-link">Link (URL)</label>
                  <input
                    id="td-block-link"
                    type="url"
                    placeholder="https://..."
                    value={selected.href ?? ""}
                    onChange={(e) =>
                      updateSelected({
                        href: e.target.value.trim() || undefined,
                        linkTarget: "_blank",
                      } as Partial<typeof selected>)
                    }
                  />
                </div>
              </>
            )}

            {isShapeBlock && (
              <>
                <div className="td-field">
                  <label htmlFor="td-shape-content">Texto na forma</label>
                  <input
                    id="td-shape-content"
                    type="text"
                    value={selected.content ?? ""}
                    onChange={(e) => updateSelected({ content: e.target.value } as Partial<typeof selected>)}
                  />
                </div>
                <div className="td-field">
                  <label htmlFor="td-shape-stroke-width">Espessura do contorno</label>
                  <input
                    id="td-shape-stroke-width"
                    type="number"
                    min={0}
                    max={20}
                    value={selected.style?.strokeWidth ?? 2}
                    onChange={(e) => updateSelectedStyle({ strokeWidth: Number(e.target.value) })}
                  />
                </div>
              </>
            )}

            {isMediaBlock && (
              <button
                type="button"
                className="td-btn td-btn--sm"
                disabled={uploading}
                onClick={() => triggerUpload("block")}
              >
                {uploading ? "Enviando…" : labels.comunicadoUpload ?? "Enviar arquivo"}
              </button>
            )}

            <div className="td-composer__grid">
              {(["x", "y", "w", "h"] as const).map((key) => (
                <div className="td-field" key={key}>
                  <label htmlFor={`td-frame-${key}`}>{key.toUpperCase()} %</label>
                  <input
                    id={`td-frame-${key}`}
                    type="number"
                    min={0}
                    max={100}
                    value={selected.frame[key]}
                    onChange={(e) =>
                      updateSelected({
                        frame: { ...selected.frame, [key]: Number(e.target.value) },
                      } as Partial<typeof selected>)
                    }
                  />
                </div>
              ))}
            </div>

            <div className="td-field">
              <label htmlFor="td-rotation">Rotação (°)</label>
              <input
                id="td-rotation"
                type="number"
                min={-180}
                max={180}
                value={selected.style?.rotation ?? 0}
                onChange={(e) => updateSelectedStyle({ rotation: Number(e.target.value) })}
              />
            </div>

            <div className="td-composer__format-row">
              <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("up")}>
                Trazer frente
              </button>
              <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("down")}>
                Enviar fundo
              </button>
              <button type="button" className="td-btn td-btn--danger td-btn--sm" onClick={removeSelected}>
                Remover
              </button>
            </div>
          </>
        )}
      </div>

      <div className="td-deck-tabs__block">
        <h4 className="td-deck-tabs__block-title">{labels.comunicadoBackground ?? "Fundo do slide"}</h4>
        <div className="td-field">
          <label htmlFor="td-bg-color">Cor</label>
          <input
            id="td-bg-color"
            type="color"
            value={background?.type === "color" ? background.value : "#0f172a"}
            onChange={(e) => setBackgroundColor(e.target.value)}
          />
        </div>
        <button
          type="button"
          className="td-btn td-btn--sm"
          disabled={uploading}
          onClick={() => triggerUpload("background")}
        >
          {labels.comunicadoUpload ?? "Enviar imagem de fundo"}
        </button>
      </div>
    </div>
  );
}
