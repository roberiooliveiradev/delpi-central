import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  ArrowDown,
  ArrowUp,
  Bold,
  Heading,
  Image as ImageIcon,
  Italic,
  Shapes,
  Text,
  Trash2,
  Underline,
  Upload,
  Video,
} from "lucide-react";
import {
  COMUNICADO_FONT_FAMILIES,
  COMUNICADO_SHAPE_KINDS,
} from "@delpi/tv-dashboard-presentation";
import { HintAction, SectionHintLabel } from "@delpi/plugin-ui";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

export function ComunicadoEditorRibbon({ labels = {} }: { labels?: Labels }) {
  const {
    selected,
    uploading,
    shapeMenuOpen,
    setShapeMenuOpen,
    background,
    addBlock,
    addShape,
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
        <SectionHintLabel label="Inserir" hint={H.insert} className="td-deck-ribbon__label" />
        <div className="td-deck-ribbon__controls">
          <button type="button" className="td-btn td-btn--sm" onClick={() => addBlock("heading")}>
            <Heading size={15} aria-hidden="true" />
            {labels.comunicadoAddHeading ?? "Título"}
          </button>
          <button type="button" className="td-btn td-btn--sm" onClick={() => addBlock("text")}>
            <Text size={15} aria-hidden="true" />
            {labels.comunicadoAddText ?? "Texto"}
          </button>
          <button type="button" className="td-btn td-btn--sm" onClick={() => addBlock("image")}>
            <ImageIcon size={15} aria-hidden="true" />
            {labels.comunicadoAddImage ?? "Imagem"}
          </button>
          <button type="button" className="td-btn td-btn--sm" onClick={() => addBlock("video")}>
            <Video size={15} aria-hidden="true" />
            {labels.comunicadoAddVideo ?? "Vídeo"}
          </button>
          <div className="td-composer__dropdown">
            <button
              type="button"
              className="td-btn td-btn--sm"
              onClick={() => setShapeMenuOpen(!shapeMenuOpen)}
            >
              <Shapes size={15} aria-hidden="true" />
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
        <SectionHintLabel label="Fundo" hint={H.background} className="td-deck-ribbon__label" />
        <div className="td-deck-ribbon__controls">
          <HintAction hint={E.backgroundColor} ariaLabel="Ajuda: Cor de fundo">
            <input
              type="color"
              className="td-deck-ribbon__color"
              aria-label="Cor de fundo"
              value={background?.type === "color" ? background.value : "#0f172a"}
              onChange={(e) => setBackgroundColor(e.target.value)}
            />
          </HintAction>
          <HintAction hint={E.uploadBackground} ariaLabel="Ajuda: Imagem de fundo">
            <button
              type="button"
              className="td-btn td-btn--sm"
              disabled={uploading}
              onClick={() => triggerUpload("background")}
            >
              <Upload size={15} aria-hidden="true" />
              {labels.comunicadoUpload ?? "Imagem"}
            </button>
          </HintAction>
        </div>
      </div>

      {isTextBlock && selected ? (
        <div className="td-deck-ribbon__group td-deck-ribbon__group--wide">
          <SectionHintLabel label="Fonte" hint={H.font} className="td-deck-ribbon__label" />
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
              className={`td-btn td-btn--sm td-btn--icon${selected.style?.fontWeight === "bold" ? " td-btn--active" : ""}`}
              aria-label="Negrito"
              onClick={() =>
                updateSelectedStyle({
                  fontWeight: selected.style?.fontWeight === "bold" ? "normal" : "bold",
                })
              }
            >
              <Bold size={15} aria-hidden="true" />
            </button>
            <button
              type="button"
              className={`td-btn td-btn--sm td-btn--icon${selected.style?.fontStyle === "italic" ? " td-btn--active" : ""}`}
              aria-label="Itálico"
              onClick={() =>
                updateSelectedStyle({
                  fontStyle: selected.style?.fontStyle === "italic" ? "normal" : "italic",
                })
              }
            >
              <Italic size={15} aria-hidden="true" />
            </button>
            <button
              type="button"
              className={`td-btn td-btn--sm td-btn--icon${selected.style?.textDecoration === "underline" ? " td-btn--active" : ""}`}
              aria-label="Sublinhado"
              onClick={() =>
                updateSelectedStyle({
                  textDecoration: selected.style?.textDecoration === "underline" ? "none" : "underline",
                })
              }
            >
              <Underline size={15} aria-hidden="true" />
            </button>
            {(
              [
                { align: "left" as const, icon: AlignLeft, label: "Alinhar à esquerda" },
                { align: "center" as const, icon: AlignCenter, label: "Centralizar" },
                { align: "right" as const, icon: AlignRight, label: "Alinhar à direita" },
              ] as const
            ).map(({ align, icon: Icon, label }) => (
              <button
                key={align}
                type="button"
                className={`td-btn td-btn--sm td-btn--icon${selected.style?.textAlign === align ? " td-btn--active" : ""}`}
                aria-label={label}
                onClick={() => updateSelectedStyle({ textAlign: align })}
              >
                <Icon size={15} aria-hidden="true" />
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
          <SectionHintLabel label="Forma" hint={H.shape} className="td-deck-ribbon__label" />
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
          <SectionHintLabel label="Organizar" hint={H.organize} className="td-deck-ribbon__label" />
          <div className="td-deck-ribbon__controls">
            {isMediaBlock ? (
              <HintAction hint={E.uploadMedia} ariaLabel="Ajuda: Trocar mídia">
                <button
                  type="button"
                  className="td-btn td-btn--sm"
                  disabled={uploading}
                  onClick={() => triggerUpload("block")}
                >
                  <Upload size={15} aria-hidden="true" />
                  {uploading ? "…" : labels.comunicadoUpload ?? "Mídia"}
                </button>
              </HintAction>
            ) : null}
            <HintAction hint={E.layerUp} ariaLabel="Ajuda: Trazer frente">
              <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("up")}>
                <ArrowUp size={15} aria-hidden="true" />
                Frente
              </button>
            </HintAction>
            <HintAction hint={E.layerDown} ariaLabel="Ajuda: Enviar fundo">
              <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("down")}>
                <ArrowDown size={15} aria-hidden="true" />
                Fundo
              </button>
            </HintAction>
            <HintAction hint={E.remove} ariaLabel="Ajuda: Remover">
              <button type="button" className="td-btn td-btn--danger td-btn--sm" onClick={removeSelected}>
                <Trash2 size={15} aria-hidden="true" />
                Remover
              </button>
            </HintAction>
          </div>
        </div>
      ) : null}
    </div>
  );
}
