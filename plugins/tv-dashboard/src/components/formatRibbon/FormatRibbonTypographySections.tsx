import {
  AlignCenter,
  AlignJustify,
  AlignLeft,
  AlignRight,
  AlignVerticalJustifyCenter,
  AlignVerticalJustifyEnd,
  AlignVerticalJustifyStart,
  Bold,
  Italic,
  List,
  ListOrdered,
  Minus,
  Plus,
  RemoveFormatting,
  Strikethrough,
  Underline,
} from "lucide-react";
import {
  COMUNICADO_FONT_FAMILIES,
  COMUNICADO_FONT_SIZE_MAX,
  COMUNICADO_FONT_SIZE_MIN,
  COMUNICADO_FONT_SIZE_PRESETS,
  COMUNICADO_FONT_SIZE_STEP,
  COMUNICADO_LINE_HEIGHT_OPTIONS,
  COMUNICADO_NAMED_TEXT_STYLE_OPTIONS,
  KPI_PART_FONT_SIZE_DEFAULTS,
  buildTextDecoration,
  clampFontSize,
  comunicadoFontFamilyOptions,
  defaultNamedStyleForBlockType,
  ensureComunicadoGoogleFontsLoaded,
  defaultTextBlockStyle,
  parseTextDecorationFlags,
  defaultVerticalAlignForBlock,
  resolveNamedStyleSelectionForBlock,
  resolveTextBlockDisplayRuns,
  selectionListTypeState,
  COMUNICADO_TEXT_SHADOW_PRESETS,
  resolveTextShadowPresetId,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  ComboboxNumberControl,
  HintAction,
  NativeTextControl,
  isAutomaticTextColor,
} from "@delpi/plugin-ui/index";
import { useEffect } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  resolveSelectedTextFormatTarget,
  textFormatTargetSupportsParagraphAlign,
} from "../../utils/selectedTextFormatTarget";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { TvRibbonColorPicker } from "../deck/TvRibbonColorPicker";
import { TdRibbonIconButton, TdRibbonSelect } from "../tdRibbonUi";
import { useComunicadoEditor } from "../comunicadoEditorContext";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const PART_FONT_SIZE_DEFAULT = 16;

const FONT_FAMILY_SELECT_OPTIONS = comunicadoFontFamilyOptions().map((font) => ({
  value: font.value,
  label: font.source === "google" ? `${font.label} · Google` : font.label,
  style: { fontFamily: font.value },
}));

/**
 * Fonte + Parágrafo — só renderiza se o objeto selecionado admite tipografia
 * (texto, forma com texto, parte textual de KPI/gráfico).
 */
export function FormatRibbonTypographySections() {
  const {
    selected,
    selectedKpiPart,
    selectedChartPart,
    background,
    updateSelectedStyle,
    updateSelectedTextFormatStyle,
    updateSelected,
    editingTextId,
    textEditSelection,
    textEditSelectionStyle,
    toggleEditingTextRunStyle,
    textEditListSelection,
    toggleSelectedTextListType,
    textEditNamedStyleSelection,
    applySelectedNamedTextStyle,
  } = useComunicadoEditor();

  useEffect(() => {
    ensureComunicadoGoogleFontsLoaded(FONT_FAMILY_SELECT_OPTIONS.map((option) => option.value));
  }, []);

  const textFormatTarget = resolveSelectedTextFormatTarget({
    selected,
    selectedKpiPart,
    selectedChartPart,
  });
  if (!textFormatTarget) return null;

  const textBlock =
    textFormatTarget.mode === "block" &&
    selected &&
    (selected.type === "heading" || selected.type === "text")
      ? selected
      : null;
  const isTextBlock = textBlock != null;
  const isShapeTextTarget =
    textFormatTarget.mode === "block" && textFormatTarget.blockType === "shape";
  const showParagraphAlign = textFormatTargetSupportsParagraphAlign(textFormatTarget);
  const formatStyle = textFormatTarget.style;
  const kpiPartKind =
    textFormatTarget.mode === "part" && textFormatTarget.source === "kpi"
      ? selectedKpiPart?.kind
      : null;
  const fontSizeDefault =
    isTextBlock
      ? 32
      : isShapeTextTarget
        ? 18
        : kpiPartKind === "value"
          ? KPI_PART_FONT_SIZE_DEFAULTS.value
          : kpiPartKind === "title"
            ? KPI_PART_FONT_SIZE_DEFAULTS.title
            : kpiPartKind === "hint"
              ? KPI_PART_FONT_SIZE_DEFAULTS.hint
              : PART_FONT_SIZE_DEFAULT;
  const currentFontSize = formatStyle?.fontSize ?? fontSizeDefault;
  const currentFontFamily = formatStyle?.fontFamily ?? COMUNICADO_FONT_FAMILIES[0];
  const textAlignActive =
    textFormatTarget.textAlign ??
    formatStyle?.textAlign ??
    textBlock?.style?.textAlign;
  const textVerticalAlign =
    textFormatTarget.verticalAlign ??
    formatStyle?.verticalAlign ??
    (textBlock
      ? (textBlock.style?.verticalAlign ?? defaultVerticalAlignForBlock(textBlock.type))
      : isShapeTextTarget
        ? "middle"
        : "middle");
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
  const fontWeightActive = partialTextSelectionActive
    ? textEditSelectionStyle?.fontWeight === "bold" ||
      textEditSelectionStyle?.fontWeight === "mixed"
    : blockFontWeightActive;
  const fontStyleActive = partialTextSelectionActive
    ? textEditSelectionStyle?.fontStyle === "italic" ||
      textEditSelectionStyle?.fontStyle === "mixed"
    : blockFontStyleActive;
  const underlineActive = partialTextSelectionActive
    ? textEditSelectionStyle?.underline === true || textEditSelectionStyle?.underline === "mixed"
    : blockDecorationFlags.underline;
  const strikethroughActive = partialTextSelectionActive
    ? textEditSelectionStyle?.strikethrough === true ||
      textEditSelectionStyle?.strikethrough === "mixed"
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

  return (
    <>
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
                className="td-deck-ribbon__select--font-family"
                value={currentFontFamily}
                onChange={(value) => {
                  ensureComunicadoGoogleFontsLoaded([value]);
                  updateSelectedTextFormatStyle({ fontFamily: value });
                }}
                options={FONT_FAMILY_SELECT_OPTIONS}
              />
            </HintAction>
            <div className="td-deck-ribbon__font-size" role="group" aria-label="Tamanho da fonte">
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
                <Minus size={16} aria-hidden="true" />
              </TdRibbonIconButton>
              <HintAction hint={H.fontSize} ariaLabel="Ajuda: Tamanho da fonte">
                <ComboboxNumberControl
                  className="td-deck-ribbon__font-size-combobox"
                  compact
                  square
                  aria-label="Tamanho da fonte"
                  value={currentFontSize}
                  options={COMUNICADO_FONT_SIZE_PRESETS}
                  min={COMUNICADO_FONT_SIZE_MIN}
                  max={COMUNICADO_FONT_SIZE_MAX}
                  clamp={clampFontSize}
                  portalScopeClassName="dashboard-tv-dashboard"
                  onChange={(next) =>
                    updateSelectedTextFormatStyle({ fontSize: clampFontSize(next) })
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
                <Plus size={16} aria-hidden="true" />
              </TdRibbonIconButton>
            </div>
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
                (selected?.type === "kpi_view"
                  ? (selected.kpiParts?.card?.style?.fill ??
                    selected.kpiOptions?.backgroundColor)
                  : undefined) ??
                (selected?.style?.fill && selected.style.fill !== "transparent"
                  ? selected.style.fill
                  : undefined) ??
                (selected?.style?.backgroundColor &&
                selected.style.backgroundColor !== "transparent"
                  ? selected.style.backgroundColor
                  : undefined) ??
                (background?.type === "color" ? background.value : "#ffffff")
              }
              value={
                isAutomaticTextColor(formatStyle?.color)
                  ? undefined
                  : (formatStyle?.color ?? "#0f172a")
              }
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

      <DeckRibbonGroup label="Efeitos" hint={H.textEffects}>
        <div className="td-deck-ribbon__toolbar">
          <div className="td-deck-ribbon__toolbar-row td-deck-ribbon__toolbar-row--dense">
            <label className="td-deck-ribbon__field-label" htmlFor="td-ribbon-text-shadow">
              Sombra
            </label>
            <TdRibbonSelect
              id="td-ribbon-text-shadow"
              value={resolveTextShadowPresetId(formatStyle?.textShadow)}
              options={[
                ...COMUNICADO_TEXT_SHADOW_PRESETS.map((preset) => ({
                  value: preset.id,
                  label: preset.label,
                })),
                ...(resolveTextShadowPresetId(formatStyle?.textShadow) === "custom"
                  ? [{ value: "custom", label: "Personalizada" }]
                  : []),
              ]}
              onChange={(value) => {
                const preset = COMUNICADO_TEXT_SHADOW_PRESETS.find((item) => item.id === value);
                updateSelectedTextFormatStyle({
                  textShadow: value === "none" ? "" : (preset?.value ?? formatStyle?.textShadow),
                });
              }}
            />
            <TvRibbonColorPicker
              hint={H.textStroke}
              label="Contorno"
              ariaLabel="Cor do contorno do texto"
              inline
              variant="outline"
              value={formatStyle?.textStrokeColor ?? ""}
              onChange={(color) =>
                updateSelectedTextFormatStyle({
                  textStrokeColor: color,
                  textStrokeWidth: formatStyle?.textStrokeWidth ?? 1,
                })
              }
              onNoFill={() =>
                updateSelectedTextFormatStyle({
                  textStrokeColor: undefined,
                  textStrokeWidth: 0,
                })
              }
            />
            <label className="td-deck-ribbon__field-label" htmlFor="td-ribbon-text-stroke-w">
              px
            </label>
            <NativeTextControl
              id="td-ribbon-text-stroke-w"
              type="number"
              className="td-deck-ribbon__number td-deck-ribbon__number--compact"
              min={0}
              max={8}
              step={0.5}
              value={formatStyle?.textStrokeWidth ?? 0}
              onChange={(value) =>
                updateSelectedTextFormatStyle({
                  textStrokeWidth: Math.max(0, Number(value) || 0),
                  textStrokeColor:
                    formatStyle?.textStrokeColor ||
                    (Number(value) > 0 ? formatStyle?.color ?? "#0f172a" : undefined),
                })
              }
            />
          </div>
        </div>
      </DeckRibbonGroup>

      {showParagraphAlign ? (
        <DeckRibbonGroup label="Parágrafo" hint={H.paragraph} wide>
          <div className="td-deck-ribbon__toolbar">
            <div className="td-deck-ribbon__toolbar-row">
              {(
                [
                  { align: "left" as const, icon: AlignLeft, label: "Alinhar à esquerda", hint: H.alignLeft },
                  { align: "center" as const, icon: AlignCenter, label: "Centralizar", hint: H.alignCenter },
                  { align: "right" as const, icon: AlignRight, label: "Alinhar à direita", hint: H.alignRight },
                  ...(isTextBlock
                    ? ([
                        {
                          align: "justify" as const,
                          icon: AlignJustify,
                          label: "Justificar",
                          hint: H.alignJustify,
                        },
                      ] as const)
                    : []),
                ] as const
              ).map(({ align, icon: Icon, label, hint }) => (
                <TdRibbonIconButton
                  key={align}
                  hint={hint}
                  ariaLabel={label}
                  active={textAlignActive === align}
                  onClick={() => updateSelectedTextFormatStyle({ textAlign: align })}
                >
                  <Icon size={15} aria-hidden="true" />
                </TdRibbonIconButton>
              ))}
              {isTextBlock ? (
                <>
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
                </>
              ) : null}
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
                  onClick={() => updateSelectedTextFormatStyle({ verticalAlign: align })}
                >
                  <Icon size={15} aria-hidden="true" />
                </TdRibbonIconButton>
              ))}
            </div>
            {isTextBlock && textBlock ? (
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
            ) : null}
          </div>
        </DeckRibbonGroup>
      ) : null}
    </>
  );
}
