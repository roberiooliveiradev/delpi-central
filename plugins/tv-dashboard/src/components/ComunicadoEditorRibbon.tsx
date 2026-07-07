import {
  COMUNICADO_FONT_FAMILIES,
  COMUNICADO_SHAPE_KINDS,
} from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "./comunicadoEditorContext";

type Labels = Record<string, string>;

export function ComunicadoEditorRibbon({ labels = {} }: { labels?: Labels }) {
  const {
    selected,
    uploading,
    shapeMenuOpen,
    setShapeMenuOpen,
    background,
    addBlock,
    addShape,
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
    <div className="td-deck-ribbon__groups">
      <div className="td-deck-ribbon__group">
        <span className="td-deck-ribbon__label">Inserir</span>
        <div className="td-deck-ribbon__controls">
          <button type="button" className="td-btn td-btn--sm" onClick={() => addBlock("heading")}>
            {labels.comunicadoAddHeading ?? "Título"}
          </button>
          <button type="button" className="td-btn td-btn--sm" onClick={() => addBlock("text")}>
            {labels.comunicadoAddText ?? "Texto"}
          </button>
          <button type="button" className="td-btn td-btn--sm" onClick={() => addBlock("image")}>
            {labels.comunicadoAddImage ?? "Imagem"}
          </button>
          <button type="button" className="td-btn td-btn--sm" onClick={() => addBlock("video")}>
            {labels.comunicadoAddVideo ?? "Vídeo"}
          </button>
          <div className="td-composer__dropdown">
            <button
              type="button"
              className="td-btn td-btn--sm"
              onClick={() => setShapeMenuOpen(!shapeMenuOpen)}
            >
              {labels.comunicadoAddShape ?? "Forma"}
            </button>
            {shapeMenuOpen ? (
              <div className="td-composer__dropdown-menu" role="menu">
                {COMUNICADO_SHAPE_KINDS.map((item) => (
                  <button
                    key={item.kind}
                    type="button"
                    role="menuitem"
                    className="td-composer__dropdown-item"
                    onClick={() => addShape(item.kind)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="td-deck-ribbon__group">
        <span className="td-deck-ribbon__label">Fundo</span>
        <div className="td-deck-ribbon__controls">
          <input
            type="color"
            className="td-deck-ribbon__color"
            aria-label="Cor de fundo"
            value={background?.type === "color" ? background.value : "#0f172a"}
            onChange={(e) => setBackgroundColor(e.target.value)}
          />
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={uploading}
            onClick={() => triggerUpload("background")}
          >
            {labels.comunicadoUpload ?? "Imagem"}
          </button>
        </div>
      </div>

      {isTextBlock && selected ? (
        <div className="td-deck-ribbon__group td-deck-ribbon__group--wide">
          <span className="td-deck-ribbon__label">Fonte</span>
          <div className="td-deck-ribbon__controls">
            <select
              className="td-deck-ribbon__select"
              aria-label="Família da fonte"
              value={selected.style?.fontFamily ?? COMUNICADO_FONT_FAMILIES[0]}
              onChange={(e) => updateSelectedStyle({ fontFamily: e.target.value })}
            >
              {COMUNICADO_FONT_FAMILIES.map((font) => (
                <option key={font} value={font}>
                  {font.split(",")[0]}
                </option>
              ))}
            </select>
            <input
              type="number"
              className="td-deck-ribbon__number"
              aria-label="Tamanho da fonte"
              min={12}
              max={120}
              value={selected.style?.fontSize ?? 32}
              onChange={(e) => updateSelectedStyle({ fontSize: Number(e.target.value) })}
            />
            <button
              type="button"
              className={`td-btn td-btn--sm${selected.style?.fontWeight === "bold" ? " td-btn--active" : ""}`}
              onClick={() =>
                updateSelectedStyle({
                  fontWeight: selected.style?.fontWeight === "bold" ? "normal" : "bold",
                })
              }
            >
              N
            </button>
            <button
              type="button"
              className={`td-btn td-btn--sm${selected.style?.fontStyle === "italic" ? " td-btn--active" : ""}`}
              onClick={() =>
                updateSelectedStyle({
                  fontStyle: selected.style?.fontStyle === "italic" ? "normal" : "italic",
                })
              }
            >
              I
            </button>
            <button
              type="button"
              className={`td-btn td-btn--sm${selected.style?.textDecoration === "underline" ? " td-btn--active" : ""}`}
              onClick={() =>
                updateSelectedStyle({
                  textDecoration: selected.style?.textDecoration === "underline" ? "none" : "underline",
                })
              }
            >
              S
            </button>
            {(["left", "center", "right"] as const).map((align) => (
              <button
                key={align}
                type="button"
                className={`td-btn td-btn--sm${selected.style?.textAlign === align ? " td-btn--active" : ""}`}
                onClick={() => updateSelectedStyle({ textAlign: align })}
              >
                {align === "left" ? "Esq" : align === "center" ? "C" : "Dir"}
              </button>
            ))}
            <input
              type="color"
              className="td-deck-ribbon__color"
              aria-label="Cor do texto"
              value={selected.style?.color ?? "#ffffff"}
              onChange={(e) => updateSelectedStyle({ color: e.target.value })}
            />
          </div>
        </div>
      ) : null}

      {isShapeBlock && selected ? (
        <div className="td-deck-ribbon__group">
          <span className="td-deck-ribbon__label">Forma</span>
          <div className="td-deck-ribbon__controls">
            <input
              type="color"
              className="td-deck-ribbon__color"
              aria-label="Preenchimento"
              value={selected.style?.fill ?? "#089bdb"}
              onChange={(e) => updateSelectedStyle({ fill: e.target.value })}
            />
            <input
              type="color"
              className="td-deck-ribbon__color"
              aria-label="Contorno"
              value={selected.style?.stroke ?? "#ffffff"}
              onChange={(e) => updateSelectedStyle({ stroke: e.target.value })}
            />
          </div>
        </div>
      ) : null}

      {selected ? (
        <div className="td-deck-ribbon__group">
          <span className="td-deck-ribbon__label">Organizar</span>
          <div className="td-deck-ribbon__controls">
            {isMediaBlock ? (
              <button
                type="button"
                className="td-btn td-btn--sm"
                disabled={uploading}
                onClick={() => triggerUpload("block")}
              >
                {uploading ? "…" : labels.comunicadoUpload ?? "Mídia"}
              </button>
            ) : null}
            <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("up")}>
              Frente
            </button>
            <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("down")}>
              Fundo
            </button>
            <button type="button" className="td-btn td-btn--danger td-btn--sm" onClick={removeSelected}>
              Remover
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
