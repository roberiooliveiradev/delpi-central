import {
  AlignCenter,
  AlignJustify,
  AlignLeft,
  AlignRight,
  AlignVerticalJustifyCenter,
  AlignVerticalJustifyEnd,
  AlignVerticalJustifyStart,
  Bold,
  Braces,
  Italic,
  List,
  ListOrdered,
  Minus,
  Plus,
  RemoveFormatting,
  Strikethrough,
  Underline,
  Upload,
} from "lucide-react";
import {
  COMUNICADO_FONT_FAMILIES,
  COMUNICADO_FONT_SIZE_MIN,
  COMUNICADO_FONT_SIZE_PRESETS,
  COMUNICADO_FONT_SIZE_STEP,
  CHART_PART_FONT_SIZE_DEFAULTS,
  KPI_PART_FONT_SIZE_DEFAULTS,
  buildTextDecoration,
  clampFontSize,
  listComunicadoFontFamilyOptions,
  defaultNamedStyleForBlockType,
  ensureComunicadoGoogleFontsLoaded,
  defaultStyle,
  defaultTextBlockStyle,
  parseTextDecorationFlags,
  defaultVerticalAlignForBlock,
  resolveNamedStyleSelectionForBlock,
  resolveTextBlockDisplayRuns,
  selectionListTypeState,
  resolveInputContrastBackground,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  ComboboxNumberControl,
  HintAction,
  isAutomaticTextColor,
} from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useRef } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  resolveSelectedTextFormatTarget,
  textFormatTargetSupportsParagraphAlign,
} from "../../utils/selectedTextFormatTarget";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { TvRibbonColorPicker } from "../deck/TvRibbonColorPicker";
import { TdRibbonIconButton, TdRibbonSelect } from "../tdRibbonUi";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ParagraphSpacingMenu } from "./ParagraphSpacingMenu";
import { TextEffectsMenu } from "./TextEffectsMenu";
import { SelectionPaneSection } from "../selectionSections/SelectionPaneSection";
import type { VisualBoxElementCapabilities } from "../selectionSections/visualBoxElementCapabilities";
import { resolveVisualBoxElementCapabilities } from "../selectionSections/visualBoxElementCapabilities";
import type { ReactNode } from "react";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/** No painel: cada grupo da ribbon vira accordion; na faixa, grupo com legenda. */
function TypographyPaneOrGroup({
  embed,
  title,
  hint,
  groupId,
  defaultOpen = true,
  children,
}: {
  embed: boolean;
  title: string;
  hint?: string;
  groupId?: string;
  defaultOpen?: boolean;
  children: ReactNode;
}) {
  if (embed) {
    return (
      <SelectionPaneSection title={title} hint={hint} defaultOpen={defaultOpen}>
        {children}
      </SelectionPaneSection>
    );
  }
  return (
    <DeckRibbonGroup groupId={groupId} label={title} hint={hint}>
      {children}
    </DeckRibbonGroup>
  );
}

/**
 * Fonte + Parágrafo — só renderiza se o objeto selecionado admite tipografia
 * (texto, forma com texto, parte textual de KPI/gráfico).
 *
 * Capacidades da caixa visual vêm de `resolveVisualBoxElementCapabilities`
 * (ou `capabilities` explícitas) — mesma UI; flags mostram/ocultam por tipo.
 */
export function FormatRibbonTypographySections({
  embed = false,
  capabilities: capabilitiesProp,
}: {
  /** Painel: legendas Fonte/Efeitos/Parágrafo acima, sem estilo ribbon abaixo. */
  embed?: boolean;
  /** Override — ex.: host `visualBox` já resolveu o perfil. */
  capabilities?: VisualBoxElementCapabilities | null;
} = {}) {
  const {
    selected,
    config,
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
    insertDataFieldAtCursor,
    uploadCustomFont,
    uploading,
  } = useComunicadoEditor();
  const fontUploadInputRef = useRef<HTMLInputElement>(null);
  const fontFamilySelectOptions = useMemo(
    () =>
      listComunicadoFontFamilyOptions(config.customFonts).map((font) => ({
        value: font.value,
        label:
          font.source === "google"
            ? `${font.label} · Google`
            : font.source === "custom"
              ? `${font.label} · Personalizada`
              : font.label,
        style: { fontFamily: font.value },
      })),
    [config.customFonts],
  );

  useEffect(() => {
    ensureComunicadoGoogleFontsLoaded(fontFamilySelectOptions.map((option) => option.value));
  }, [fontFamilySelectOptions]);

  const textFormatTarget = resolveSelectedTextFormatTarget({
    selected,
    selectedKpiPart,
    selectedChartPart,
  });
  if (!textFormatTarget) return null;

  const visualCaps =
    capabilitiesProp ??
    (selected ? resolveVisualBoxElementCapabilities(selected) : null);

  const textBlock =
    textFormatTarget.mode === "block" &&
    selected &&
    (selected.type === "heading" || selected.type === "text")
      ? selected
      : null;
  const shapeBlock =
    textFormatTarget.mode === "block" && selected?.type === "shape" ? selected : null;
  const visualBoxBlock = textBlock ?? shapeBlock;
  const isTextBlock = textBlock != null;
  const isShapeTextTarget =
    textFormatTarget.mode === "block" && textFormatTarget.blockType === "shape";
  const showParagraphAlign = textFormatTargetSupportsParagraphAlign(textFormatTarget);
  const showTextHighlight = visualCaps?.textHighlight ?? isTextBlock;
  const showClearFormatting = visualCaps?.clearFormatting ?? isTextBlock;
  const showParagraphJustify = visualCaps?.paragraphJustify ?? isTextBlock;
  const showParagraphLists = visualCaps?.paragraphLists ?? isTextBlock;
  const showParagraphSpacing = visualCaps?.paragraphSpacing ?? isTextBlock;
  const showParagraphNamedStyle = visualCaps?.paragraphNamedStyle ?? isTextBlock;
  const canInsertDataField =
    Boolean(editingTextId) &&
    Boolean(visualBoxBlock && "dataSourceId" in visualBoxBlock && visualBoxBlock.dataSourceId?.trim());
  const formatStyle = textFormatTarget.style;
  const kpiPartKind =
    textFormatTarget.mode === "part" && textFormatTarget.source === "kpi"
      ? selectedKpiPart?.kind
      : null;
  const chartPartKind =
    textFormatTarget.mode === "part" && textFormatTarget.source === "chart"
      ? selectedChartPart?.kind
      : null;
  /* Fallback só se o target não trouxe fontSize (não deveria ocorrer após resolve). */
  const fontSizeDefault =
    isTextBlock
      ? textBlock!.type === "heading"
        ? 56
        : 28
      : isShapeTextTarget
        ? 18
        : kpiPartKind === "value"
          ? KPI_PART_FONT_SIZE_DEFAULTS.value
          : kpiPartKind === "title"
            ? KPI_PART_FONT_SIZE_DEFAULTS.title
            : kpiPartKind === "hint" || kpiPartKind === "comparison"
              ? KPI_PART_FONT_SIZE_DEFAULTS[
                  kpiPartKind === "comparison" ? "comparison" : "hint"
                ]
              : chartPartKind && chartPartKind in CHART_PART_FONT_SIZE_DEFAULTS
                ? CHART_PART_FONT_SIZE_DEFAULTS[
                    chartPartKind as keyof typeof CHART_PART_FONT_SIZE_DEFAULTS
                  ]
                : 9;
  const fontSizeAuto = Boolean(formatStyle?.fontSizeAuto);
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

  const spacingSource = visualBoxBlock;
  const currentLineHeight = spacingSource?.style?.lineHeight ?? 1.15;
  const currentLetterSpacing = spacingSource?.style?.letterSpacing ?? 0;
  const fontTitle =
    textFormatTarget.mode === "part" ? `Fonte · ${textFormatTarget.partLabel}` : "Fonte";

  const paragraphAlignBody = (
    <div className="td-deck-ribbon__toolbar td-deck-ribbon__toolbar--paragraph">
      <div className="td-deck-ribbon__paragraph-cols">
        <div className="td-deck-ribbon__paragraph-col td-deck-ribbon__paragraph-col--align">
          <div className="td-deck-ribbon__toolbar-row" role="group" aria-label="Alinhamento horizontal">
            {(
              [
                { align: "left" as const, icon: AlignLeft, label: "Alinhar à esquerda", hint: H.alignLeft },
                { align: "center" as const, icon: AlignCenter, label: "Centralizar", hint: H.alignCenter },
                { align: "right" as const, icon: AlignRight, label: "Alinhar à direita", hint: H.alignRight },
                ...(showParagraphJustify
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
          </div>
          <div className="td-deck-ribbon__toolbar-row" role="group" aria-label="Alinhamento vertical e listas">
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
            {showParagraphLists ? (
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
          </div>
        </div>
        {!embed && showParagraphSpacing && spacingSource ? (
          <div className="td-deck-ribbon__paragraph-col td-deck-ribbon__paragraph-col--spacing">
            <ParagraphSpacingMenu
              variant="popover"
              namedStyleValue={namedStyleValue}
              showNamedStyle={showParagraphNamedStyle}
              lineHeight={currentLineHeight}
              letterSpacing={currentLetterSpacing}
              onNamedStyle={(value) => applySelectedNamedTextStyle(value)}
              onLineHeight={(value) => updateSelectedStyle({ lineHeight: value })}
              onLetterSpacing={(value) => updateSelectedStyle({ letterSpacing: value })}
            />
          </div>
        ) : null}
      </div>
    </div>
  );

  const spacingMenu =
    showParagraphSpacing && spacingSource ? (
      <ParagraphSpacingMenu
        variant={embed ? "inline" : "popover"}
        namedStyleValue={namedStyleValue}
        showNamedStyle={showParagraphNamedStyle}
        lineHeight={currentLineHeight}
        letterSpacing={currentLetterSpacing}
        onNamedStyle={(value) => applySelectedNamedTextStyle(value)}
        onLineHeight={(value) => updateSelectedStyle({ lineHeight: value })}
        onLetterSpacing={(value) => updateSelectedStyle({ letterSpacing: value })}
      />
    ) : null;

  return (
    <>
      <TypographyPaneOrGroup embed={embed} groupId="typo-font" title={fontTitle} hint={H.font}>
        <div className="td-deck-ribbon__toolbar td-deck-ribbon__toolbar--text-stack td-deck-ribbon__toolbar--font">
          <div className="td-deck-ribbon__toolbar-row td-deck-ribbon__toolbar-row--inputs">
            <HintAction hint={H.fontFamily} ariaLabel="Ajuda: Família da fonte">
              <TdRibbonSelect
                aria-label="Família da fonte"
                className="td-deck-ribbon__select--font-family"
                value={currentFontFamily}
                onChange={(value) => {
                  ensureComunicadoGoogleFontsLoaded([value]);
                  updateSelectedTextFormatStyle({ fontFamily: value });
                }}
                options={fontFamilySelectOptions}
              />
            </HintAction>
            <TdRibbonIconButton
              hint={H.uploadFont}
              ariaLabel="Enviar fonte personalizada"
              disabled={uploading}
              onClick={() => fontUploadInputRef.current?.click()}
            >
              <Upload size={15} aria-hidden="true" />
            </TdRibbonIconButton>
            <input
              ref={fontUploadInputRef}
              type="file"
              hidden
              accept=".woff2,.ttf,.otf,font/woff2,font/ttf,font/otf"
              onChange={(event) => {
                const file = event.target.files?.[0];
                event.target.value = "";
                if (file) void uploadCustomFont(file);
              }}
            />
            <div className="td-deck-ribbon__font-size" role="group" aria-label="Tamanho da fonte">
              <TdRibbonIconButton
                hint={H.fontSizeDown}
                ariaLabel="Diminuir fonte"
                disabled={currentFontSize <= COMUNICADO_FONT_SIZE_MIN}
                onClick={() =>
                  updateSelectedTextFormatStyle({
                    fontSize: clampFontSize(currentFontSize - COMUNICADO_FONT_SIZE_STEP),
                    fontSizeAuto: false,
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
                  aria-label={fontSizeAuto ? "Tamanho da fonte (Automático)" : "Tamanho da fonte"}
                  value={currentFontSize}
                  options={COMUNICADO_FONT_SIZE_PRESETS}
                  min={COMUNICADO_FONT_SIZE_MIN}
                  clamp={clampFontSize}
                  portalScopeClassName="dashboard-tv-dashboard"
                  onChange={(next) =>
                    updateSelectedTextFormatStyle({
                      fontSize: clampFontSize(next),
                      fontSizeAuto: false,
                    })
                  }
                />
              </HintAction>
              <TdRibbonIconButton
                hint={H.fontSizeUp}
                ariaLabel="Aumentar fonte"
                onClick={() =>
                  updateSelectedTextFormatStyle({
                    fontSize: clampFontSize(currentFontSize + COMUNICADO_FONT_SIZE_STEP),
                    fontSizeAuto: false,
                  })
                }
              >
                <Plus size={16} aria-hidden="true" />
              </TdRibbonIconButton>
              {textFormatTarget.mode === "part" && textFormatTarget.source === "kpi" ? (
                <TdRibbonIconButton
                  hint="Ajusta o texto ao quadro da parte (automático)."
                  ariaLabel={fontSizeAuto ? "Fonte automática ativa" : "Usar fonte automática"}
                  active={fontSizeAuto}
                  onClick={() =>
                    updateSelectedTextFormatStyle({
                      fontSizeAuto: !fontSizeAuto,
                      ...(fontSizeAuto
                        ? { fontSize: clampFontSize(currentFontSize) }
                        : {}),
                    })
                  }
                >
                  Auto
                </TdRibbonIconButton>
              ) : null}
            </div>
          </div>
          <div className="td-deck-ribbon__toolbar-row">
            {canInsertDataField ? (
              <TdRibbonIconButton
                hint={TV_DASHBOARD_HELP_TOOLTIPS.data.insertFieldAtCursor}
                ariaLabel="Inserir campo dinâmico no cursor"
                onClick={() => insertDataFieldAtCursor()}
              >
                <Braces size={15} aria-hidden="true" />
              </TdRibbonIconButton>
            ) : null}
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
            {showTextHighlight ? (
              <TvRibbonColorPicker
                hint={H.textHighlight}
                label="Realce"
                ariaLabel="Realce do texto"
                inline
                variant="fill"
                value={formatStyle?.textHighlight ?? "#fef08a"}
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
                (selected?.type === "input"
                  ? resolveInputContrastBackground(
                      selected.inputParts,
                      selected.style,
                    )
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
            {showClearFormatting && visualBoxBlock ? (
              <TdRibbonIconButton
                hint={H.clearFormatting}
                ariaLabel="Limpar formatação"
                onClick={() => {
                  if (visualBoxBlock.type === "heading" || visualBoxBlock.type === "text") {
                    const defaults = defaultTextBlockStyle(visualBoxBlock.type);
                    updateSelected({
                      style: {
                        ...defaults,
                        zIndex: visualBoxBlock.style?.zIndex ?? defaults.zIndex,
                        fill: visualBoxBlock.style?.fill ?? defaults.fill,
                        backgroundColor:
                          visualBoxBlock.style?.backgroundColor ?? defaults.backgroundColor,
                        stroke: visualBoxBlock.style?.stroke ?? defaults.stroke,
                        strokeWidth: visualBoxBlock.style?.strokeWidth ?? defaults.strokeWidth,
                        borderWidth: visualBoxBlock.style?.borderWidth ?? defaults.borderWidth,
                        borderColor: visualBoxBlock.style?.borderColor ?? defaults.borderColor,
                        borderRadius: visualBoxBlock.style?.borderRadius,
                        boxShadow: visualBoxBlock.style?.boxShadow,
                        opacity: visualBoxBlock.style?.opacity,
                      },
                    } as Partial<ComunicadoBlock>);
                    return;
                  }
                  const defaults = defaultStyle("shape", visualBoxBlock.shape);
                  updateSelected({
                    style: {
                      ...visualBoxBlock.style,
                      fontFamily: defaults.fontFamily,
                      fontSize: defaults.fontSize,
                      fontWeight: defaults.fontWeight,
                      fontStyle: undefined,
                      color: defaults.color,
                      textDecoration: undefined,
                      textHighlight: undefined,
                      textAlign: defaults.textAlign,
                      verticalAlign: defaults.verticalAlign,
                      lineHeight: defaults.lineHeight,
                      letterSpacing: undefined,
                      textShadow: undefined,
                      textStrokeColor: undefined,
                      textStrokeWidth: undefined,
                      textReflection: undefined,
                    },
                  } as Partial<ComunicadoBlock>);
                }}
              >
                <RemoveFormatting size={15} aria-hidden="true" />
              </TdRibbonIconButton>
            ) : null}
          </div>
        </div>
      </TypographyPaneOrGroup>

      <TypographyPaneOrGroup
        embed={embed}
        groupId="typo-effects"
        title="Efeitos de texto"
        hint={H.textEffects}
        defaultOpen={false}
      >
        <TextEffectsMenu
          formatStyle={formatStyle}
          onUpdate={updateSelectedTextFormatStyle}
          variant={embed ? "inline" : "popover"}
        />
      </TypographyPaneOrGroup>

      {showParagraphAlign ? (
        <TypographyPaneOrGroup
          embed={embed}
          groupId="typo-paragraph"
          title="Parágrafo"
          hint={H.paragraph}
          defaultOpen={false}
        >
          {paragraphAlignBody}
        </TypographyPaneOrGroup>
      ) : null}

      {embed && spacingMenu ? (
        <TypographyPaneOrGroup
          embed
          groupId="typo-style"
          title="Estilo"
          hint={H.paragraphSpacing}
          defaultOpen={false}
        >
          {spacingMenu}
        </TypographyPaneOrGroup>
      ) : null}
    </>
  );
}
