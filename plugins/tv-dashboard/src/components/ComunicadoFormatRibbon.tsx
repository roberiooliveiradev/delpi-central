import {
  AlignCenter,
  AlignJustify,
  AlignLeft,
  AlignRight,
  AlignVerticalJustifyCenter,
  AlignVerticalJustifyEnd,
  AlignVerticalJustifyStart,
  ArrowDown,
  ArrowUp,
  Bold,
  Copy,
  Highlighter,
  Italic,
  Minus,
  Plus,
  Redo2,
  RemoveFormatting,
  Strikethrough,
  Trash2,
  Underline,
  Undo2,
  Upload,
} from "lucide-react";
import {
  COMUNICADO_FONT_FAMILIES,
  COMUNICADO_FONT_SIZE_MAX,
  COMUNICADO_FONT_SIZE_MIN,
  COMUNICADO_FONT_SIZE_STEP,
  COMUNICADO_LINE_HEIGHT_OPTIONS,
  buildTextDecoration,
  clampFontSize,
  defaultTextBlockStyle,
  parseTextDecorationFlags,
  defaultVerticalAlignForBlock,
} from "@delpi/tv-dashboard-presentation";
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
    updateSelected,
    removeSelected,
    duplicateSelected,
    moveLayer,
    triggerUpload,
    setBackgroundColor,
    undo,
    redo,
    canUndo,
    canRedo,
  } = useComunicadoEditor();

  const isTextBlock = selected?.type === "heading" || selected?.type === "text";
  const textVerticalAlign =
    isTextBlock && selected
      ? selected.style?.verticalAlign ?? defaultVerticalAlignForBlock(selected.type)
      : "top";
  const isMediaBlock = selected?.type === "image" || selected?.type === "video";
  const isShapeBlock = selected?.type === "shape";

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Histórico" hint="Desfazer ou refazer alterações no slide (Ctrl+Z / Ctrl+Y).">
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile icon={Undo2} label="Desfazer" disabled={!canUndo} onClick={undo} />
          <DeckRibbonTile icon={Redo2} label="Refazer" disabled={!canRedo} onClick={redo} />
        </div>
      </DeckRibbonGroup>

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
        <>
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
                <button
                  type="button"
                  className="td-btn td-btn--sm td-btn--icon"
                  aria-label="Diminuir fonte"
                  disabled={(selected.style?.fontSize ?? 32) <= COMUNICADO_FONT_SIZE_MIN}
                  onClick={() =>
                    updateSelectedStyle({
                      fontSize: clampFontSize(
                        (selected.style?.fontSize ?? 32) - COMUNICADO_FONT_SIZE_STEP,
                      ),
                    })
                  }
                >
                  <Minus size={14} aria-hidden="true" />
                </button>
                <input
                  type="number"
                  className="td-deck-ribbon__number"
                  aria-label="Tamanho da fonte"
                  min={COMUNICADO_FONT_SIZE_MIN}
                  max={COMUNICADO_FONT_SIZE_MAX}
                  value={selected.style?.fontSize ?? 32}
                  onChange={(e) =>
                    updateSelectedStyle({ fontSize: clampFontSize(Number(e.target.value)) })
                  }
                />
                <button
                  type="button"
                  className="td-btn td-btn--sm td-btn--icon"
                  aria-label="Aumentar fonte"
                  disabled={(selected.style?.fontSize ?? 32) >= COMUNICADO_FONT_SIZE_MAX}
                  onClick={() =>
                    updateSelectedStyle({
                      fontSize: clampFontSize(
                        (selected.style?.fontSize ?? 32) + COMUNICADO_FONT_SIZE_STEP,
                      ),
                    })
                  }
                >
                  <Plus size={14} aria-hidden="true" />
                </button>
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
                {(() => {
                  const flags = parseTextDecorationFlags(selected.style?.textDecoration);
                  return (
                    <>
                      <button
                        type="button"
                        className={`td-btn td-btn--sm td-btn--icon${flags.underline ? " td-btn--active" : ""}`}
                        aria-label="Sublinhado"
                        onClick={() =>
                          updateSelectedStyle({
                            textDecoration: buildTextDecoration(
                              !flags.underline,
                              flags.strikethrough,
                            ),
                          })
                        }
                      >
                        <Underline size={15} aria-hidden="true" />
                      </button>
                      <button
                        type="button"
                        className={`td-btn td-btn--sm td-btn--icon${flags.strikethrough ? " td-btn--active" : ""}`}
                        aria-label="Tachado"
                        onClick={() =>
                          updateSelectedStyle({
                            textDecoration: buildTextDecoration(
                              flags.underline,
                              !flags.strikethrough,
                            ),
                          })
                        }
                      >
                        <Strikethrough size={15} aria-hidden="true" />
                      </button>
                    </>
                  );
                })()}
                <span className="td-deck-ribbon__toolbar-sep" aria-hidden="true" />
                <label className="td-ribbon-tile td-ribbon-tile--color td-ribbon-tile--inline" aria-label="Realce">
                  <span className="td-ribbon-tile__icon">
                    <Highlighter size={15} aria-hidden="true" />
                    <input
                      type="color"
                      className="td-deck-ribbon__color td-deck-ribbon__color--overlay"
                      value={selected.style?.textHighlight ?? "#fef08a"}
                      onChange={(e) => updateSelectedStyle({ textHighlight: e.target.value })}
                    />
                  </span>
                </label>
                <input
                  type="color"
                  className="td-deck-ribbon__color"
                  aria-label="Cor do texto"
                  value={selected.style?.color ?? "#ffffff"}
                  onChange={(e) => updateSelectedStyle({ color: e.target.value })}
                />
                <button
                  type="button"
                  className="td-btn td-btn--sm td-btn--icon"
                  aria-label="Limpar formatação"
                  onClick={() => {
                    const defaults = defaultTextBlockStyle(selected.type);
                    updateSelected({
                      style: { ...defaults, zIndex: selected.style?.zIndex ?? defaults.zIndex },
                    } as Partial<typeof selected>);
                  }}
                >
                  <RemoveFormatting size={15} aria-hidden="true" />
                </button>
              </div>
            </div>
          </DeckRibbonGroup>

          <DeckRibbonGroup label="Parágrafo" hint={H.paragraph} wide>
            <div className="td-deck-ribbon__toolbar">
              <div className="td-deck-ribbon__toolbar-row">
                {(
                  [
                    { align: "left" as const, icon: AlignLeft, label: "Alinhar à esquerda" },
                    { align: "center" as const, icon: AlignCenter, label: "Centralizar" },
                    { align: "right" as const, icon: AlignRight, label: "Alinhar à direita" },
                    { align: "justify" as const, icon: AlignJustify, label: "Justificar" },
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
                <span className="td-deck-ribbon__toolbar-sep" aria-hidden="true" />
                {(
                  [
                    {
                      align: "top" as const,
                      icon: AlignVerticalJustifyStart,
                      label: "Alinhar ao topo",
                    },
                    {
                      align: "middle" as const,
                      icon: AlignVerticalJustifyCenter,
                      label: "Centralizar verticalmente",
                    },
                    {
                      align: "bottom" as const,
                      icon: AlignVerticalJustifyEnd,
                      label: "Alinhar à base",
                    },
                  ] as const
                ).map(({ align, icon: Icon, label }) => (
                  <button
                    key={align}
                    type="button"
                    className={`td-btn td-btn--sm td-btn--icon${textVerticalAlign === align ? " td-btn--active" : ""}`}
                    aria-label={label}
                    onClick={() => updateSelectedStyle({ verticalAlign: align })}
                  >
                    <Icon size={15} aria-hidden="true" />
                  </button>
                ))}
              </div>
              <div className="td-deck-ribbon__toolbar-row">
                <label className="td-deck-ribbon__field-label" htmlFor="td-ribbon-line-height">
                  Entrelinhas
                </label>
                <select
                  id="td-ribbon-line-height"
                  className="td-deck-ribbon__select td-deck-ribbon__select--compact"
                  aria-label="Entrelinhas"
                  value={String(selected.style?.lineHeight ?? 1.15)}
                  onChange={(e) => updateSelectedStyle({ lineHeight: Number(e.target.value) })}
                >
                  {COMUNICADO_LINE_HEIGHT_OPTIONS.map((value) => (
                    <option key={value} value={value}>
                      {value === 1 ? "Simples" : value === 1.15 ? "1,15" : String(value)}
                    </option>
                  ))}
                </select>
                <label className="td-deck-ribbon__field-label" htmlFor="td-ribbon-letter-spacing">
                  Espaçamento
                </label>
                <input
                  id="td-ribbon-letter-spacing"
                  type="number"
                  className="td-deck-ribbon__number td-deck-ribbon__number--compact"
                  aria-label="Espaçamento entre caracteres (px)"
                  min={-2}
                  max={24}
                  step={0.5}
                  value={selected.style?.letterSpacing ?? 0}
                  onChange={(e) =>
                    updateSelectedStyle({ letterSpacing: Number(e.target.value) || 0 })
                  }
                />
              </div>
            </div>
          </DeckRibbonGroup>
        </>
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
            <DeckRibbonTile icon={Copy} label="Duplicar" hint="Duplicar elemento (Ctrl+D)" onClick={duplicateSelected} />
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
          <div className="td-deck-ribbon__toolbar td-deck-ribbon__toolbar--compact">
            <label className="td-deck-ribbon__field-label" htmlFor="td-block-opacity">
              Opacidade
            </label>
            <input
              id="td-block-opacity"
              type="range"
              min={10}
              max={100}
              step={5}
              value={Math.round((selected.style?.opacity ?? 1) * 100)}
              onChange={(e) =>
                updateSelectedStyle({ opacity: Number(e.target.value) / 100 })
              }
            />
            {isMediaBlock ? (
              <>
                <label className="td-deck-ribbon__field-label" htmlFor="td-block-object-fit">
                  Ajuste
                </label>
                <select
                  id="td-block-object-fit"
                  className="td-deck-ribbon__select td-deck-ribbon__select--compact"
                  value={selected.style?.objectFit ?? "cover"}
                  onChange={(e) =>
                    updateSelectedStyle({
                      objectFit: e.target.value as "cover" | "contain",
                    })
                  }
                >
                  <option value="cover">Preencher</option>
                  <option value="contain">Conter</option>
                </select>
              </>
            ) : null}
          </div>
        </DeckRibbonGroup>
      ) : (
        <p className="td-subtitle td-deck-ribbon__hint">Selecione um elemento no palco para formatar.</p>
      )}
    </div>
  );
}
