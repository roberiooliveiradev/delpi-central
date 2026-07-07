import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  ArrowDown,
  ArrowUp,
  Bold,
  Italic,
  Trash2,
  Underline,
  Upload,
} from "lucide-react";
import { COMUNICADO_FONT_FAMILIES } from "@delpi/tv-dashboard-presentation";
import { HintAction } from "@delpi/plugin-ui";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

export function ComunicadoFormatRibbon({ labels = {} }: { labels?: Labels }) {
  const {
    selected,
    uploading,
    background,
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
      <DeckRibbonGroup label="Fundo do slide" hint={H.background}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <HintAction hint={E.backgroundColor} ariaLabel="Ajuda: Cor de fundo">
            <label className="td-ribbon-tile td-ribbon-tile--color" aria-label="Cor de fundo">
              <span className="td-ribbon-tile__icon">
                <input
                  type="color"
                  className="td-deck-ribbon__color"
                  value={background?.type === "color" ? background.value : "#0f172a"}
                  onChange={(e) => setBackgroundColor(e.target.value)}
                />
              </span>
              <span className="td-ribbon-tile__label">Cor</span>
            </label>
          </HintAction>
          <DeckRibbonTile
            icon={Upload}
            label={labels.comunicadoUpload ?? "Imagem"}
            hint={E.uploadBackground}
            disabled={uploading}
            onClick={() => triggerUpload("background")}
          />
        </div>
      </DeckRibbonGroup>

      {isTextBlock && selected ? (
        <DeckRibbonGroup label="Fonte" hint={H.font} wide>
          <div className="td-deck-ribbon__toolbar">
            <div className="td-deck-ribbon__toolbar-row">
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
            </div>
            <div className="td-deck-ribbon__toolbar-row">
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
              <span className="td-deck-ribbon__toolbar-sep" aria-hidden="true" />
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
        </DeckRibbonGroup>
      ) : null}

      {isShapeBlock && selected ? (
        <DeckRibbonGroup label="Forma" hint={H.shape}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            <label className="td-ribbon-tile td-ribbon-tile--color" aria-label="Preenchimento">
              <span className="td-ribbon-tile__icon">
                <input
                  type="color"
                  className="td-deck-ribbon__color"
                  value={selected.style?.fill ?? "#089bdb"}
                  onChange={(e) => updateSelectedStyle({ fill: e.target.value })}
                />
              </span>
              <span className="td-ribbon-tile__label">Preench.</span>
            </label>
            <label className="td-ribbon-tile td-ribbon-tile--color" aria-label="Contorno">
              <span className="td-ribbon-tile__icon">
                <input
                  type="color"
                  className="td-deck-ribbon__color"
                  value={selected.style?.stroke ?? "#ffffff"}
                  onChange={(e) => updateSelectedStyle({ stroke: e.target.value })}
                />
              </span>
              <span className="td-ribbon-tile__label">Contorno</span>
            </label>
          </div>
        </DeckRibbonGroup>
      ) : null}

      {selected ? (
        <DeckRibbonGroup label="Organizar" hint={H.organize}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            {isMediaBlock ? (
              <DeckRibbonTile
                icon={Upload}
                label={uploading ? "…" : labels.comunicadoUpload ?? "Mídia"}
                hint={E.uploadMedia}
                disabled={uploading}
                onClick={() => triggerUpload("block")}
              />
            ) : null}
            <DeckRibbonTile
              icon={ArrowUp}
              label="Frente"
              hint={E.layerUp}
              onClick={() => moveLayer("up")}
            />
            <DeckRibbonTile
              icon={ArrowDown}
              label="Fundo"
              hint={E.layerDown}
              onClick={() => moveLayer("down")}
            />
            <DeckRibbonTile
              icon={Trash2}
              label="Remover"
              hint={E.remove}
              onClick={removeSelected}
            />
          </div>
        </DeckRibbonGroup>
      ) : (
        <p className="td-subtitle td-deck-ribbon__hint">Selecione um elemento no palco para formatar.</p>
      )}
    </div>
  );
}
