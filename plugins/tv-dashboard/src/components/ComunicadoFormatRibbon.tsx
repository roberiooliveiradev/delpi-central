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
  AlignHorizontalJustifyCenter,
  AlignHorizontalJustifyEnd,
  AlignHorizontalJustifyStart,
  Bold,
  Copy,
  Crop,
  FolderOpen,
  Group,
  Highlighter,
  Italic,
  List,
  ListOrdered,
  Minus,
  Plus,
  Redo2,
  RemoveFormatting,
  Strikethrough,
  Trash2,
  Underline,
  Ungroup,
  Undo2,
  Upload,
  ZoomIn,
  ZoomOut,
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
  resolveTextBlockDisplayRuns,
  selectionListTypeState,
} from "@delpi/tv-dashboard-presentation";
import { HintAction } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  COMUNICADO_BOX_SHADOW_PRESETS,
  matchBoxShadowPreset,
} from "../content/comunicadoVisualPresets";
import type { LayoutAlignCommand } from "../utils/comunicadoLayoutAlign";
import { selectedHasGroup } from "../utils/comunicadoGrouping";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { TdRibbonSelect } from "./tdRibbonUi";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

export function ComunicadoFormatRibbon({ labels = {} }: { labels?: Labels }) {
  const {
    selected,
    selectedIds,
    uploading,
    background,
    updateSelectedStyle,
    updateSelected,
    removeSelected,
    duplicateSelected,
    moveLayer,
    triggerUpload,
    openMediaLibrary,
    setBackgroundColor,
    undo,
    redo,
    canUndo,
    canRedo,
    alignSelected,
    stageZoom,
    setStageZoom,
    groupSelected,
    ungroupSelected,
    blocks,
    editingTextId,
    textEditSelection,
    textEditSelectionStyle,
    toggleEditingTextRunStyle,
    textEditListSelection,
    toggleSelectedTextListType,
  } = useComunicadoEditor();

  const multiSelected = selectedIds.length >= 2;
  const canDistribute = selectedIds.length >= 3;
  const canGroup = selectedIds.length >= 2;
  const canUngroup = selectedHasGroup(blocks, selectedIds);

  const isTextBlock = selected?.type === "heading" || selected?.type === "text";
  const partialTextSelectionActive = Boolean(
    isTextBlock &&
      selected &&
      editingTextId === selected.id &&
      textEditSelection &&
      textEditSelection.blockId === selected.id &&
      textEditSelection.end > textEditSelection.start,
  );
  const blockFontWeightActive = selected?.style?.fontWeight === "bold";
  const blockFontStyleActive = selected?.style?.fontStyle === "italic";
  const blockDecorationFlags = parseTextDecorationFlags(selected?.style?.textDecoration);
  const partialFontWeightActive =
    partialTextSelectionActive &&
    (textEditSelectionStyle?.fontWeight === "bold" || textEditSelectionStyle?.fontWeight === "mixed");
  const partialFontStyleActive =
    partialTextSelectionActive &&
    (textEditSelectionStyle?.fontStyle === "italic" || textEditSelectionStyle?.fontStyle === "mixed");
  const partialUnderlineActive =
    partialTextSelectionActive &&
    (textEditSelectionStyle?.underline === true || textEditSelectionStyle?.underline === "mixed");
  const partialStrikethroughActive =
    partialTextSelectionActive &&
    (textEditSelectionStyle?.strikethrough === true ||
      textEditSelectionStyle?.strikethrough === "mixed");
  const fontWeightActive = partialTextSelectionActive ? partialFontWeightActive : blockFontWeightActive;
  const fontStyleActive = partialTextSelectionActive ? partialFontStyleActive : blockFontStyleActive;
  const underlineActive = partialTextSelectionActive
    ? partialUnderlineActive
    : blockDecorationFlags.underline;
  const strikethroughActive = partialTextSelectionActive
    ? partialStrikethroughActive
    : blockDecorationFlags.strikethrough;
  const listSelectionState =
    isTextBlock && selected
      ? editingTextId === selected.id && textEditListSelection
        ? textEditListSelection
        : selectionListTypeState(
            resolveTextBlockDisplayRuns(selected),
            0,
            Math.max(0, selected.content.length),
          )
      : null;
  const bulletListActive =
    listSelectionState?.bullet === true || listSelectionState?.bullet === "mixed";
  const orderedListActive =
    listSelectionState?.ordered === true || listSelectionState?.ordered === "mixed";
  const textVerticalAlign =
    isTextBlock && selected
      ? selected.style?.verticalAlign ?? defaultVerticalAlignForBlock(selected.type)
      : "top";
  const isMediaBlock = selected?.type === "image" || selected?.type === "video";
  const isImageBlock = selected?.type === "image";
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
          <DeckRibbonTile
            icon={FolderOpen}
            label="Biblioteca"
            hint="Escolher imagem já enviada à playlist"
            onClick={() => openMediaLibrary("background")}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Visualização" hint="Zoom do palco (50% a 200%).">
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={ZoomOut}
            label="−"
            disabled={stageZoom <= 0.5}
            onClick={() => setStageZoom(Math.max(0.5, Math.round((stageZoom - 0.1) * 10) / 10))}
          />
          <span className="td-deck-ribbon__zoom-label">{Math.round(stageZoom * 100)}%</span>
          <DeckRibbonTile
            icon={ZoomIn}
            label="+"
            disabled={stageZoom >= 2}
            onClick={() => setStageZoom(Math.min(2, Math.round((stageZoom + 0.1) * 10) / 10))}
          />
        </div>
      </DeckRibbonGroup>

      {multiSelected ? (
        <DeckRibbonGroup label="Alinhar" hint="Alinhar ou distribuir os elementos selecionados.">
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            {(
              [
                ["align-left", AlignHorizontalJustifyStart, "Esquerda"],
                ["align-center-h", AlignHorizontalJustifyCenter, "Centro H"],
                ["align-right", AlignHorizontalJustifyEnd, "Direita"],
                ["align-top", AlignVerticalJustifyStart, "Topo"],
                ["align-center-v", AlignVerticalJustifyCenter, "Centro V"],
                ["align-bottom", AlignVerticalJustifyEnd, "Base"],
              ] as const
            ).map(([command, Icon, label]) => (
              <DeckRibbonTile
                key={command}
                icon={Icon}
                label={label}
                onClick={() => alignSelected(command as LayoutAlignCommand)}
              />
            ))}
            <DeckRibbonTile
              icon={AlignHorizontalJustifyCenter}
              label="Dist. H"
              hint="Distribuir horizontalmente (3+)"
              disabled={!canDistribute}
              onClick={() => alignSelected("distribute-h")}
            />
            <DeckRibbonTile
              icon={AlignVerticalJustifyCenter}
              label="Dist. V"
              hint="Distribuir verticalmente (3+)"
              disabled={!canDistribute}
              onClick={() => alignSelected("distribute-v")}
            />
            <DeckRibbonTile
              icon={Group}
              label="Agrupar"
              hint="Agrupar seleção"
              disabled={!canGroup}
              onClick={groupSelected}
            />
            <DeckRibbonTile
              icon={Ungroup}
              label="Desagrupar"
              hint="Remover grupo da seleção"
              disabled={!canUngroup}
              onClick={ungroupSelected}
            />
          </div>
        </DeckRibbonGroup>
      ) : null}

      {isTextBlock && selected ? (
        <>
          <DeckRibbonGroup label="Fonte" hint={H.font} wide>
            <div className="td-deck-ribbon__toolbar">
              <div className="td-deck-ribbon__toolbar-row">
                <TdRibbonSelect
                  aria-label="Família da fonte"
                  value={selected.style?.fontFamily ?? COMUNICADO_FONT_FAMILIES[0]}
                  onChange={(value) => updateSelectedStyle({ fontFamily: value })}
                  options={COMUNICADO_FONT_FAMILIES.map((font) => ({
                    value: font,
                    label: font.split(",")[0] ?? font,
                  }))}
                />
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
                  className={`td-btn td-btn--sm td-btn--icon${fontWeightActive ? " td-btn--active" : ""}`}
                  aria-label="Negrito"
                  onClick={() => {
                    if (partialTextSelectionActive) {
                      toggleEditingTextRunStyle("fontWeight");
                      return;
                    }
                    updateSelectedStyle({
                      fontWeight: selected.style?.fontWeight === "bold" ? "normal" : "bold",
                    });
                  }}
                >
                  <Bold size={15} aria-hidden="true" />
                </button>
                <button
                  type="button"
                  className={`td-btn td-btn--sm td-btn--icon${fontStyleActive ? " td-btn--active" : ""}`}
                  aria-label="Itálico"
                  onClick={() => {
                    if (partialTextSelectionActive) {
                      toggleEditingTextRunStyle("fontStyle");
                      return;
                    }
                    updateSelectedStyle({
                      fontStyle: selected.style?.fontStyle === "italic" ? "normal" : "italic",
                    });
                  }}
                >
                  <Italic size={15} aria-hidden="true" />
                </button>
                <button
                  type="button"
                  className={`td-btn td-btn--sm td-btn--icon${underlineActive ? " td-btn--active" : ""}`}
                  aria-label="Sublinhado"
                  onClick={() => {
                    if (partialTextSelectionActive) {
                      toggleEditingTextRunStyle("underline");
                      return;
                    }
                    updateSelectedStyle({
                      textDecoration: buildTextDecoration(
                        !blockDecorationFlags.underline,
                        blockDecorationFlags.strikethrough,
                      ),
                    });
                  }}
                >
                  <Underline size={15} aria-hidden="true" />
                </button>
                <button
                  type="button"
                  className={`td-btn td-btn--sm td-btn--icon${strikethroughActive ? " td-btn--active" : ""}`}
                  aria-label="Tachado"
                  onClick={() => {
                    if (partialTextSelectionActive) {
                      toggleEditingTextRunStyle("strikethrough");
                      return;
                    }
                    updateSelectedStyle({
                      textDecoration: buildTextDecoration(
                        blockDecorationFlags.underline,
                        !blockDecorationFlags.strikethrough,
                      ),
                    });
                  }}
                >
                  <Strikethrough size={15} aria-hidden="true" />
                </button>
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
                <button
                  type="button"
                  className={`td-btn td-btn--sm td-btn--icon${bulletListActive ? " td-btn--active" : ""}`}
                  aria-label="Marcadores"
                  onClick={() => toggleSelectedTextListType("bullet")}
                >
                  <List size={15} aria-hidden="true" />
                </button>
                <button
                  type="button"
                  className={`td-btn td-btn--sm td-btn--icon${orderedListActive ? " td-btn--active" : ""}`}
                  aria-label="Lista numerada"
                  onClick={() => toggleSelectedTextListType("ordered")}
                >
                  <ListOrdered size={15} aria-hidden="true" />
                </button>
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
                <TdRibbonSelect
                  id="td-ribbon-line-height"
                  className="td-deck-ribbon__select td-deck-ribbon__select--compact"
                  aria-label="Entrelinhas"
                  value={String(selected.style?.lineHeight ?? 1.15)}
                  onChange={(value) => updateSelectedStyle({ lineHeight: Number(value) })}
                  options={COMUNICADO_LINE_HEIGHT_OPTIONS.map((value) => ({
                    value: String(value),
                    label: value === 1 ? "Simples" : value === 1.15 ? "1,15" : String(value),
                  }))}
                />
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
            {isImageBlock && selected?.url ? (
              <DeckRibbonTile
                icon={Crop}
                label="Recorte"
                hint="Ajustar recorte da imagem no inspetor"
                onClick={() => {
                  document.getElementById("td-comunicado-crop-panel")?.scrollIntoView({
                    behavior: "smooth",
                    block: "nearest",
                  });
                }}
              />
            ) : null}
            {isMediaBlock ? (
              <>
                <DeckRibbonTile
                  icon={FolderOpen}
                  label="Biblioteca"
                  hint="Escolher mídia da playlist"
                  onClick={() => openMediaLibrary("block")}
                />
                <DeckRibbonTile
                  icon={Upload}
                  label={uploading ? "…" : labels.comunicadoUpload ?? "Mídia"}
                  hint={E.uploadMedia}
                  disabled={uploading}
                  onClick={() => triggerUpload("block")}
                />
              </>
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
                <TdRibbonSelect
                  id="td-block-object-fit"
                  className="td-deck-ribbon__select td-deck-ribbon__select--compact"
                  aria-label="Ajuste"
                  value={selected.style?.objectFit ?? "cover"}
                  onChange={(value) =>
                    updateSelectedStyle({
                      objectFit: value as "cover" | "contain",
                    })
                  }
                  options={[
                    { value: "cover", label: "Preencher" },
                    { value: "contain", label: "Conter" },
                  ]}
                />
              </>
            ) : null}
            <label className="td-deck-ribbon__field-label" htmlFor="td-block-border-width">
              Borda
            </label>
            <input
              id="td-block-border-width"
              type="number"
              className="td-deck-ribbon__number td-deck-ribbon__number--compact"
              min={0}
              max={12}
              value={selected.style?.borderWidth ?? 0}
              onChange={(e) =>
                updateSelectedStyle({
                  borderWidth: Number(e.target.value) || 0,
                  borderColor: selected.style?.borderColor ?? "#ffffff",
                })
              }
            />
            <label className="td-ribbon-tile td-ribbon-tile--color" aria-label="Cor da borda">
              <span className="td-ribbon-tile__icon">
                <input
                  type="color"
                  className="td-deck-ribbon__color"
                  value={selected.style?.borderColor ?? "#ffffff"}
                  onChange={(e) => updateSelectedStyle({ borderColor: e.target.value })}
                />
              </span>
            </label>
            <label className="td-deck-ribbon__field-label" htmlFor="td-block-radius">
              Raio
            </label>
            <input
              id="td-block-radius"
              type="number"
              className="td-deck-ribbon__number td-deck-ribbon__number--compact"
              min={0}
              max={64}
              value={selected.style?.borderRadius ?? 0}
              onChange={(e) => updateSelectedStyle({ borderRadius: Number(e.target.value) || 0 })}
            />
            <label className="td-deck-ribbon__field-label" htmlFor="td-block-shadow">
              Sombra
            </label>
            <TdRibbonSelect
              id="td-block-shadow"
              className="td-deck-ribbon__select td-deck-ribbon__select--compact"
              aria-label="Sombra"
              value={matchBoxShadowPreset(selected.style?.boxShadow)}
              onChange={(value) => {
                const preset = COMUNICADO_BOX_SHADOW_PRESETS.find((item) => item.key === value);
                updateSelectedStyle({ boxShadow: preset?.value });
              }}
              options={COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
                value: preset.key,
                label: preset.label,
              }))}
            />
          </div>
        </DeckRibbonGroup>
      ) : (
        <p className="td-subtitle td-deck-ribbon__hint">Selecione um elemento no palco para formatar.</p>
      )}
    </div>
  );
}
