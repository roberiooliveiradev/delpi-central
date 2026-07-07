import { ArrowDown, ArrowUp, Image as ImageIcon, Trash2, Upload } from "lucide-react";
import { ComunicadoBlockView, frameStyle } from "@delpi/tv-dashboard-presentation";
import { FieldLabel, HelpTooltip, HintAction } from "@delpi/plugin-ui";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";

const FONT_SCALE = 0.35;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

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
        <h4 className="td-deck-tabs__block-title">
          {labels.comunicadoBlocks ?? "Elemento selecionado"}
          <HelpTooltip content={E.panel} ariaLabel="Ajuda: elemento selecionado" />
        </h4>
        {!selected ? (
          <p className="td-subtitle">Selecione um elemento no slide ou arraste para posicionar.</p>
        ) : (
          <>
            <p className="td-subtitle">Tipo: {selected.type}</p>

            {isTextBlock && (
              <>
                <div className="td-field">
                  <FieldLabel htmlFor="td-block-content" label="Conteúdo" hint={E.content} className="td-field__label" />
                  <textarea
                    id="td-block-content"
                    rows={2}
                    value={selected.content}
                    onChange={(e) => updateSelected({ content: e.target.value } as Partial<typeof selected>)}
                  />
                </div>
                <div className="td-field">
                  <FieldLabel htmlFor="td-block-link" label="Link (URL)" hint={E.link} className="td-field__label" />
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
                  <FieldLabel htmlFor="td-shape-content" label="Texto na forma" hint={E.shapeText} className="td-field__label" />
                  <input
                    id="td-shape-content"
                    type="text"
                    value={selected.content ?? ""}
                    onChange={(e) => updateSelected({ content: e.target.value } as Partial<typeof selected>)}
                  />
                </div>
                <div className="td-field">
                  <FieldLabel
                    htmlFor="td-shape-stroke-width"
                    label="Espessura do contorno"
                    hint={E.strokeWidth}
                    className="td-field__label"
                  />
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
              <HintAction hint={E.uploadMedia} ariaLabel="Ajuda: enviar arquivo">
                <button
                  type="button"
                  className="td-btn td-btn--sm"
                  disabled={uploading}
                  onClick={() => triggerUpload("block")}
                >
                  <Upload size={15} aria-hidden="true" />
                  {uploading ? "Enviando…" : labels.comunicadoUpload ?? "Enviar arquivo"}
                </button>
              </HintAction>
            )}

            <div className="td-composer__grid">
              {(["x", "y", "w", "h"] as const).map((key) => (
                <div className="td-field" key={key}>
                  <FieldLabel
                    htmlFor={`td-frame-${key}`}
                    label={key.toUpperCase()}
                    hint={E.position}
                    className="td-field__label"
                  />
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
              <FieldLabel htmlFor="td-rotation" label="Rotação (°)" hint={E.rotation} className="td-field__label" />
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
              <HintAction hint={E.layerUp} ariaLabel="Ajuda: trazer frente">
                <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("up")}>
                  <ArrowUp size={15} aria-hidden="true" />
                  Trazer frente
                </button>
              </HintAction>
              <HintAction hint={E.layerDown} ariaLabel="Ajuda: enviar fundo">
                <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("down")}>
                  <ArrowDown size={15} aria-hidden="true" />
                  Enviar fundo
                </button>
              </HintAction>
              <HintAction hint={E.remove} ariaLabel="Ajuda: remover">
                <button type="button" className="td-btn td-btn--danger td-btn--sm" onClick={removeSelected}>
                  <Trash2 size={15} aria-hidden="true" />
                  Remover
                </button>
              </HintAction>
            </div>
          </>
        )}
      </div>

      <div className="td-deck-tabs__block">
        <h4 className="td-deck-tabs__block-title">
          <ImageIcon size={14} aria-hidden="true" />
          {labels.comunicadoBackground ?? "Fundo do slide"}
        </h4>
        <div className="td-field">
          <FieldLabel htmlFor="td-bg-color" label="Cor" hint={E.backgroundColor} className="td-field__label" />
          <input
            id="td-bg-color"
            type="color"
            value={background?.type === "color" ? background.value : "#0f172a"}
            onChange={(e) => setBackgroundColor(e.target.value)}
          />
        </div>
        <HintAction hint={E.uploadBackground} ariaLabel="Ajuda: imagem de fundo">
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={uploading}
            onClick={() => triggerUpload("background")}
          >
            <Upload size={15} aria-hidden="true" />
            {labels.comunicadoUpload ?? "Enviar imagem de fundo"}
          </button>
        </HintAction>
      </div>
    </div>
  );
}
