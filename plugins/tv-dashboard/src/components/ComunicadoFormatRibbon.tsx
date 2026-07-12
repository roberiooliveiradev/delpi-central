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
  Crop,
  FolderOpen,
  Italic,
  List,
  ListOrdered,
  Minus,
  Plus,
  RemoveFormatting,
  Strikethrough,
  Trash2,
  Underline,
  Upload,
} from "lucide-react";
import {
  COMUNICADO_FONT_FAMILIES,
  COMUNICADO_FONT_SIZE_MAX,
  COMUNICADO_FONT_SIZE_MIN,
  COMUNICADO_FONT_SIZE_STEP,
  COMUNICADO_LINE_HEIGHT_OPTIONS,
  COMUNICADO_NAMED_TEXT_STYLE_OPTIONS,
  buildTextDecoration,
  clampFontSize,
  comunicadoFontFamilyOptions,
  defaultNamedStyleForBlockType,
  ensureComunicadoGoogleFontsLoaded,
  defaultTextBlockStyle,
  isComunicadoVisualBoxBlock,
  parseTextDecorationFlags,
  defaultVerticalAlignForBlock,
  resolveNamedStyleSelectionForBlock,
  resolveShapePrimitive,
  resolveTextBlockDisplayRuns,
  resolveVisualBoxChrome,
  selectionListTypeState,
  shapeSupportsFill,
  shapeSupportsStroke,
  visualBoxSupportsShapeFormatting,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import { DECK_SHAPE_DEFAULTS, HintAction, NativeTextControl, ShapeEffectsMenu, ShapeFillMenu, ShapeOutlineMenu, ShapeStyleMenu } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  COMUNICADO_BOX_SHADOW_PRESETS,
  matchBoxShadowPreset,
} from "../content/comunicadoVisualPresets";
import { selectedHasGroup } from "../utils/comunicadoGrouping";
import { resolveSelectedTextFormatTarget } from "../utils/selectedTextFormatTarget";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { TdRibbonIconButton, TdRibbonSelect } from "./tdRibbonUi";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { FormatRibbonAlignSection } from "./FormatRibbonAlignSection";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;
const PART_FONT_SIZE_DEFAULT = 16;

export function ComunicadoFormatRibbon({ labels = {} }: { labels?: Labels }) {
  const {
    selected,
    selectedIds,
    selectedKpiPart,
    selectedChartPart,
    uploading,
    background,
    updateSelectedStyle,
    updateSelectedTextFormatStyle,
    updateSelected,
    removeSelected,
    duplicateSelected,
    moveLayer,
    triggerUpload,
    openMediaLibrary,
    setBackgroundColor,
    alignSelected,
    groupSelected,
    ungroupSelected,
    blocks,
    editingTextId,
    textEditSelection,
    textEditSelectionStyle,
    toggleEditingTextRunStyle,
    textEditListSelection,
    toggleSelectedTextListType,
    textEditNamedStyleSelection,
    applySelectedNamedTextStyle,
  } = useComunicadoEditor();

  const multiSelected = selectedIds.length >= 2;
  const canDistribute = selectedIds.length >= 3;
  const canGroup = selectedIds.length >= 2;
  const canUngroup = selectedHasGroup(blocks, selectedIds);

  const textFormatTarget = resolveSelectedTextFormatTarget({
    selected,
    selectedKpiPart,
    selectedChartPart,
  });
  const textBlock =
    textFormatTarget?.mode === "block" && selected && (selected.type === "heading" || selected.type === "text")
      ? selected
      : null;
  const isTextBlock = textBlock != null;
  const showFontControls = textFormatTarget != null;
  const formatStyle = textFormatTarget?.style;
  const fontSizeDefault = isTextBlock ? 32 : PART_FONT_SIZE_DEFAULT;
  const currentFontSize = formatStyle?.fontSize ?? fontSizeDefault;
  const currentFontFamily = formatStyle?.fontFamily ?? COMUNICADO_FONT_FAMILIES[0];
  const partialTextSelectionActive = Boolean(
    textBlock &&
      editingTextId === textBlock.id &&
      textEditSelection &&
      textEditSelection.blockId === textBlock.id &&
      textEditSelection.end > textEditSelection.start,
  );
  const blockFontWeightActive = formatStyle?.fontWeight === "bold";
  const blockFontStyleActive = formatStyle?.fontStyle === "italic";
  const blockDecorationFlags = parseTextDecorationFlags(
    formatStyle?.textDecoration as Parameters<typeof parseTextDecorationFlags>[0],
  );
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
  const listSelectionState = textBlock
    ? editingTextId === textBlock.id && textEditListSelection
      ? textEditListSelection
      : selectionListTypeState(
          resolveTextBlockDisplayRuns(textBlock),
          0,
          Math.max(0, textBlock.content.length),
        )
    : null;
  const bulletListActive =
    listSelectionState?.bullet === true || listSelectionState?.bullet === "mixed";
  const orderedListActive =
    listSelectionState?.ordered === true || listSelectionState?.ordered === "mixed";
  const namedStyleSelection = textBlock
    ? editingTextId === textBlock.id && textEditNamedStyleSelection
      ? textEditNamedStyleSelection
      : resolveNamedStyleSelectionForBlock(textBlock, 0, Math.max(0, textBlock.content.length))
    : null;
  const namedStyleValue =
    namedStyleSelection && namedStyleSelection !== "mixed"
      ? namedStyleSelection
      : defaultNamedStyleForBlockType(textBlock?.type === "heading" ? "heading" : "text");
  const textVerticalAlign = textBlock
    ? textBlock.style?.verticalAlign ?? defaultVerticalAlignForBlock(textBlock.type)
    : "top";
  const isMediaBlock = selected?.type === "image" || selected?.type === "video";
  const isImageBlock = selected?.type === "image";
  const isShapeBlock =
    selected && isComunicadoVisualBoxBlock(selected) && visualBoxSupportsShapeFormatting(selected);
  const shapePrimitive =
    isShapeBlock && selected.type === "shape"
      ? resolveShapePrimitive(selected.shape)
      : null;
  const shapeChrome = isShapeBlock ? resolveVisualBoxChrome(selected) : null;
  const showShapeFill = shapePrimitive ? shapeSupportsFill(shapePrimitive) : false;
  const showShapeStroke = shapePrimitive ? shapeSupportsStroke(shapePrimitive) : false;
  const defaultShapeStrokeWidth = shapeChrome?.strokeWidth ?? 2;

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Fundo do slide" hint={H.background}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--color-pickers">
          <TvRibbonColorPicker
            hint={E.backgroundColor}
            label="Cor"
            ariaLabel="Cor sólida de fundo do slide"
            value={background?.type === "color" ? background.value : "#ffffff"}
            onChange={setBackgroundColor}
          />
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
            hint={H.mediaLibrary}
            onClick={() => openMediaLibrary("background")}
          />
        </div>
      </DeckRibbonGroup>

      {multiSelected ? (
        <FormatRibbonAlignSection
          canDistribute={canDistribute}
          canGroup={canGroup}
          canUngroup={canUngroup}
          alignSelected={alignSelected}
          groupSelected={groupSelected}
          ungroupSelected={ungroupSelected}
        />
      ) : null}

      {showFontControls && textFormatTarget ? (
        <DeckRibbonGroup
          label={textFormatTarget.mode === "part" ? `Fonte · ${textFormatTarget.partLabel}` : "Fonte"}
          hint={H.font}
          wide
        >
            <div className="td-deck-ribbon__toolbar">
              <div className="td-deck-ribbon__toolbar-row">
                <HintAction hint={H.fontFamily} ariaLabel="Ajuda: Família da fonte">
                  <TdRibbonSelect
                    aria-label="Família da fonte"
                    value={currentFontFamily}
                    onChange={(value) => {
                      ensureComunicadoGoogleFontsLoaded([value]);
                      updateSelectedTextFormatStyle({ fontFamily: value });
                    }}
                    options={comunicadoFontFamilyOptions().map((font) => ({
                      value: font.value,
                      label: font.source === "google" ? `${font.label} · Google` : font.label,
                    }))}
                  />
                </HintAction>
                <TdRibbonIconButton
                  hint={H.fontSizeDown}
                  ariaLabel="Diminuir fonte"
                  disabled={currentFontSize <= COMUNICADO_FONT_SIZE_MIN}
                  onClick={() =>
                    updateSelectedTextFormatStyle({
                      fontSize: clampFontSize(currentFontSize - COMUNICADO_FONT_SIZE_STEP),
                    })
                  }
                >
                  <Minus size={14} aria-hidden="true" />
                </TdRibbonIconButton>
                <HintAction hint={H.fontSize} ariaLabel="Ajuda: Tamanho da fonte">
                  <NativeTextControl
                    type="number"
                    className="td-deck-ribbon__number"
                    aria-label="Tamanho da fonte"
                    min={COMUNICADO_FONT_SIZE_MIN}
                    max={COMUNICADO_FONT_SIZE_MAX}
                    value={currentFontSize}
                    onChange={(value) =>
                      updateSelectedTextFormatStyle({ fontSize: clampFontSize(Number(value)) })
                    }
                  />
                </HintAction>
                <TdRibbonIconButton
                  hint={H.fontSizeUp}
                  ariaLabel="Aumentar fonte"
                  disabled={currentFontSize >= COMUNICADO_FONT_SIZE_MAX}
                  onClick={() =>
                    updateSelectedTextFormatStyle({
                      fontSize: clampFontSize(currentFontSize + COMUNICADO_FONT_SIZE_STEP),
                    })
                  }
                >
                  <Plus size={14} aria-hidden="true" />
                </TdRibbonIconButton>
              </div>
              <div className="td-deck-ribbon__toolbar-row">
                <TdRibbonIconButton
                  hint={H.bold}
                  ariaLabel="Negrito"
                  active={Boolean(fontWeightActive)}
                  onClick={() => {
                    if (partialTextSelectionActive) {
                      toggleEditingTextRunStyle("fontWeight");
                      return;
                    }
                    updateSelectedTextFormatStyle({
                      fontWeight: formatStyle?.fontWeight === "bold" ? "normal" : "bold",
                    });
                  }}
                >
                  <Bold size={15} aria-hidden="true" />
                </TdRibbonIconButton>
                <TdRibbonIconButton
                  hint={H.italic}
                  ariaLabel="Itálico"
                  active={Boolean(fontStyleActive)}
                  onClick={() => {
                    if (partialTextSelectionActive) {
                      toggleEditingTextRunStyle("fontStyle");
                      return;
                    }
                    updateSelectedTextFormatStyle({
                      fontStyle: formatStyle?.fontStyle === "italic" ? "normal" : "italic",
                    });
                  }}
                >
                  <Italic size={15} aria-hidden="true" />
                </TdRibbonIconButton>
                <TdRibbonIconButton
                  hint={H.underline}
                  ariaLabel="Sublinhado"
                  active={Boolean(underlineActive)}
                  onClick={() => {
                    if (partialTextSelectionActive) {
                      toggleEditingTextRunStyle("underline");
                      return;
                    }
                    updateSelectedTextFormatStyle({
                      textDecoration: buildTextDecoration(
                        !blockDecorationFlags.underline,
                        blockDecorationFlags.strikethrough,
                      ),
                    });
                  }}
                >
                  <Underline size={15} aria-hidden="true" />
                </TdRibbonIconButton>
                <TdRibbonIconButton
                  hint={H.strikethrough}
                  ariaLabel="Tachado"
                  active={Boolean(strikethroughActive)}
                  onClick={() => {
                    if (partialTextSelectionActive) {
                      toggleEditingTextRunStyle("strikethrough");
                      return;
                    }
                    updateSelectedTextFormatStyle({
                      textDecoration: buildTextDecoration(
                        blockDecorationFlags.underline,
                        !blockDecorationFlags.strikethrough,
                      ),
                    });
                  }}
                >
                  <Strikethrough size={15} aria-hidden="true" />
                </TdRibbonIconButton>
                <span className="td-deck-ribbon__toolbar-sep" aria-hidden="true" />
                {isTextBlock && textBlock ? (
                  <TvRibbonColorPicker
                    hint={H.textHighlight}
                    label="Realce"
                    ariaLabel="Realce do texto"
                    inline
                    variant="fill"
                    value={textBlock.style?.textHighlight ?? "#fef08a"}
                    onChange={(color) => updateSelectedTextFormatStyle({ textHighlight: color })}
                    onNoFill={() => updateSelectedTextFormatStyle({ textHighlight: "transparent" })}
                  />
                ) : null}
                <TvRibbonColorPicker
                  hint={H.textColor}
                  label="Cor texto"
                  ariaLabel="Cor do texto"
                  inline
                  variant="text"
                  contrastBackground={
                    (selected?.style?.fill && selected.style.fill !== "transparent"
                      ? selected.style.fill
                      : undefined) ??
                    (selected?.style?.backgroundColor &&
                    selected.style.backgroundColor !== "transparent"
                      ? selected.style.backgroundColor
                      : undefined) ??
                    (background?.type === "color" ? background.value : "#ffffff")
                  }
                  value={formatStyle?.color ?? "#0f172a"}
                  onChange={(color) => updateSelectedTextFormatStyle({ color })}
                />
                {isTextBlock && textBlock ? (
                  <TdRibbonIconButton
                    hint={H.clearFormatting}
                    ariaLabel="Limpar formatação"
                    onClick={() => {
                      const defaults = defaultTextBlockStyle(textBlock.type);
                      updateSelected({
                        style: { ...defaults, zIndex: textBlock.style?.zIndex ?? defaults.zIndex },
                      } as Partial<ComunicadoBlock>);
                    }}
                  >
                    <RemoveFormatting size={15} aria-hidden="true" />
                  </TdRibbonIconButton>
                ) : null}
              </div>
            </div>
          </DeckRibbonGroup>
      ) : null}

      {isTextBlock && textBlock ? (
          <DeckRibbonGroup label="Parágrafo" hint={H.paragraph} wide>
            <div className="td-deck-ribbon__toolbar">
              <div className="td-deck-ribbon__toolbar-row">
                {(
                  [
                    { align: "left" as const, icon: AlignLeft, label: "Alinhar à esquerda", hint: H.alignLeft },
                    { align: "center" as const, icon: AlignCenter, label: "Centralizar", hint: H.alignCenter },
                    { align: "right" as const, icon: AlignRight, label: "Alinhar à direita", hint: H.alignRight },
                    { align: "justify" as const, icon: AlignJustify, label: "Justificar", hint: H.alignJustify },
                  ] as const
                ).map(({ align, icon: Icon, label, hint }) => (
                  <TdRibbonIconButton
                    key={align}
                    hint={hint}
                    ariaLabel={label}
                    active={textBlock.style?.textAlign === align}
                    onClick={() => updateSelectedStyle({ textAlign: align })}
                  >
                    <Icon size={15} aria-hidden="true" />
                  </TdRibbonIconButton>
                ))}
                <span className="td-deck-ribbon__toolbar-sep" aria-hidden="true" />
                <TdRibbonIconButton
                  hint={H.bulletList}
                  ariaLabel="Marcadores"
                  active={Boolean(bulletListActive)}
                  onClick={() => toggleSelectedTextListType("bullet")}
                >
                  <List size={15} aria-hidden="true" />
                </TdRibbonIconButton>
                <TdRibbonIconButton
                  hint={H.orderedList}
                  ariaLabel="Lista numerada"
                  active={Boolean(orderedListActive)}
                  onClick={() => toggleSelectedTextListType("ordered")}
                >
                  <ListOrdered size={15} aria-hidden="true" />
                </TdRibbonIconButton>
                <span className="td-deck-ribbon__toolbar-sep" aria-hidden="true" />
                {(
                  [
                    {
                      align: "top" as const,
                      icon: AlignVerticalJustifyStart,
                      label: "Alinhar ao topo",
                      hint: H.alignTop,
                    },
                    {
                      align: "middle" as const,
                      icon: AlignVerticalJustifyCenter,
                      label: "Centralizar verticalmente",
                      hint: H.alignMiddle,
                    },
                    {
                      align: "bottom" as const,
                      icon: AlignVerticalJustifyEnd,
                      label: "Alinhar à base",
                      hint: H.alignBottom,
                    },
                  ] as const
                ).map(({ align, icon: Icon, label, hint }) => (
                  <TdRibbonIconButton
                    key={align}
                    hint={hint}
                    ariaLabel={label}
                    active={textVerticalAlign === align}
                    onClick={() => updateSelectedStyle({ verticalAlign: align })}
                  >
                    <Icon size={15} aria-hidden="true" />
                  </TdRibbonIconButton>
                ))}
              </div>
              <div className="td-deck-ribbon__toolbar-row td-deck-ribbon__toolbar-row--dense">
                <label className="td-deck-ribbon__field-label" htmlFor="td-ribbon-named-style">
                  Estilo
                </label>
                <TdRibbonSelect
                  id="td-ribbon-named-style"
                  className="td-deck-ribbon__select td-deck-ribbon__select--style"
                  aria-label="Estilo de parágrafo"
                  value={namedStyleValue}
                  onChange={(value) =>
                    applySelectedNamedTextStyle(value as typeof namedStyleValue)
                  }
                  options={COMUNICADO_NAMED_TEXT_STYLE_OPTIONS.map((option) => ({
                    value: option.key,
                    label: option.label,
                  }))}
                />
                <label className="td-deck-ribbon__field-label" htmlFor="td-ribbon-line-height">
                  Entrelinhas
                </label>
                <TdRibbonSelect
                  id="td-ribbon-line-height"
                  className="td-deck-ribbon__select td-deck-ribbon__select--compact"
                  aria-label="Entrelinhas"
                  value={String(textBlock.style?.lineHeight ?? 1.15)}
                  onChange={(value) => updateSelectedStyle({ lineHeight: Number(value) })}
                  options={COMUNICADO_LINE_HEIGHT_OPTIONS.map((value) => ({
                    value: String(value),
                    label: value === 1 ? "Simples" : value === 1.15 ? "1,15" : String(value),
                  }))}
                />
                <label className="td-deck-ribbon__field-label" htmlFor="td-ribbon-letter-spacing">
                  Espaçamento
                </label>
                <NativeTextControl
                  id="td-ribbon-letter-spacing"
                  type="number"
                  className="td-deck-ribbon__number td-deck-ribbon__number--compact"
                  aria-label="Espaçamento entre caracteres (px)"
                  min={-2}
                  max={24}
                  step={0.5}
                  value={textBlock.style?.letterSpacing ?? 0}
                  onChange={(value) =>
                    updateSelectedStyle({ letterSpacing: Number(value) || 0 })
                  }
                />
              </div>
            </div>
          </DeckRibbonGroup>
      ) : null}

      {isShapeBlock && selected ? (
        <DeckRibbonGroup label="Forma" hint={H.shape}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
            {showShapeFill ? (
              <ShapeFillMenu
                value={selected.style?.fill ?? DECK_SHAPE_DEFAULTS.fill}
                fillLabel={shapePrimitive === "point" ? "Cor" : "Preench."}
                onChange={(color) => updateSelectedStyle({ fill: color })}
                onNoFill={() => updateSelectedStyle({ fill: "transparent" })}
              />
            ) : null}
            {showShapeStroke ? (
              <ShapeOutlineMenu
                color={
                  selected.style?.stroke ??
                  (shapePrimitive === "line"
                    ? DECK_SHAPE_DEFAULTS.lineStroke
                    : DECK_SHAPE_DEFAULTS.stroke)
                }
                strokeWidth={selected.style?.strokeWidth ?? defaultShapeStrokeWidth}
                minWidth={shapePrimitive === "point" ? 0 : 0}
                maxWidth={shapePrimitive === "point" ? 8 : 20}
                outlineLabel="Contorno"
                onColorChange={(color) => updateSelectedStyle({ stroke: color })}
                onNoOutline={() => updateSelectedStyle({ stroke: "transparent" })}
                onStrokeWidthChange={(width) => updateSelectedStyle({ strokeWidth: width })}
              />
            ) : null}
            <ShapeStyleMenu
              onSelect={(preset) =>
                updateSelectedStyle({
                  fill: preset.fill,
                  stroke: preset.stroke,
                  strokeWidth: preset.strokeWidth,
                  boxShadow: preset.boxShadow,
                })
              }
            />
            <ShapeEffectsMenu
              onSelect={(effectId, optionId) => {
                if (effectId === "shadow" && !optionId) {
                  updateSelectedStyle({ boxShadow: "0 4px 14px rgba(0, 0, 0, 0.28)" });
                }
              }}
            />
          </div>
        </DeckRibbonGroup>
      ) : null}

      {selected ? (
        <DeckRibbonGroup label="Organizar" hint={H.organize} wide>
          <div className="td-deck-ribbon__organize">
            <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            <DeckRibbonTile icon={Copy} label="Duplicar" hint={H.duplicateBlock} onClick={duplicateSelected} />
            {isImageBlock && selected?.url ? (
              <DeckRibbonTile
                icon={Crop}
                label="Recorte"
                hint={H.cropImage}
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
                  hint={H.mediaLibrary}
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
            <div className="td-deck-ribbon__toolbar td-deck-ribbon__toolbar--inline">
            <label className="td-deck-ribbon__field-label" htmlFor="td-block-opacity">
              Opacidade
            </label>
            <HintAction hint={H.opacity} ariaLabel="Ajuda: Opacidade">
              <input
                id="td-block-opacity"
                type="range"
                min={10}
                max={100}
                step={5}
                aria-label="Opacidade"
                value={Math.round((selected.style?.opacity ?? 1) * 100)}
                onChange={(e) =>
                  updateSelectedStyle({ opacity: Number(e.target.value) / 100 })
                }
              />
            </HintAction>
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
            <NativeTextControl
              id="td-block-border-width"
              type="number"
              className="td-deck-ribbon__number td-deck-ribbon__number--compact"
              min={0}
              max={12}
              value={selected.style?.borderWidth ?? 0}
              onChange={(value) =>
                updateSelectedStyle({
                  borderWidth: Number(value) || 0,
                  borderColor: selected.style?.borderColor ?? "#ffffff",
                })
              }
            />
            <TvRibbonColorPicker
              label="Borda"
              ariaLabel="Cor da borda"
              inline
              variant="outline"
              value={selected.style?.borderColor ?? "#ffffff"}
              onChange={(color) => updateSelectedStyle({ borderColor: color })}
            />
            <label className="td-deck-ribbon__field-label" htmlFor="td-block-radius">
              Raio
            </label>
            <NativeTextControl
              id="td-block-radius"
              type="number"
              className="td-deck-ribbon__number td-deck-ribbon__number--compact"
              min={0}
              max={64}
              value={selected.style?.borderRadius ?? 0}
              onChange={(value) => updateSelectedStyle({ borderRadius: Number(value) || 0 })}
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
          </div>
        </DeckRibbonGroup>
      ) : (
        <p className="td-subtitle td-deck-ribbon__hint">Selecione um elemento no palco para formatar.</p>
      )}
    </div>
  );
}
