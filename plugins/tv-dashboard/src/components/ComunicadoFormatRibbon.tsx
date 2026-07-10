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
  parseTextDecorationFlags,
  defaultVerticalAlignForBlock,
  resolveNamedStyleSelectionForBlock,
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
import { TdRibbonIconButton, TdRibbonSelect } from "./tdRibbonUi";
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
  const namedStyleSelection =
    isTextBlock && selected
      ? editingTextId === selected.id && textEditNamedStyleSelection
        ? textEditNamedStyleSelection
        : resolveNamedStyleSelectionForBlock(
            selected,
            0,
            Math.max(0, selected.content.length),
          )
      : null;
  const namedStyleValue =
    namedStyleSelection && namedStyleSelection !== "mixed"
      ? namedStyleSelection
      : defaultNamedStyleForBlockType(selected?.type === "heading" ? "heading" : "text");
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
          <DeckRibbonTile icon={Undo2} label="Desfazer" hint={H.undo} disabled={!canUndo} onClick={undo} />
          <DeckRibbonTile icon={Redo2} label="Refazer" hint={H.redo} disabled={!canRedo} onClick={redo} />
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
            hint={H.mediaLibrary}
            onClick={() => openMediaLibrary("background")}
          />
        </div>
      </DeckRibbonGroup>

      {multiSelected ? (
        <DeckRibbonGroup label="Alinhar" hint={H.alignSelection}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            {(
              [
                ["align-left", AlignHorizontalJustifyStart, "Esquerda", H.alignSelectionLeft],
                ["align-center-h", AlignHorizontalJustifyCenter, "Centro H", H.alignSelectionCenterH],
                ["align-right", AlignHorizontalJustifyEnd, "Direita", H.alignSelectionRight],
                ["align-top", AlignVerticalJustifyStart, "Topo", H.alignSelectionTop],
                ["align-center-v", AlignVerticalJustifyCenter, "Centro V", H.alignSelectionCenterV],
                ["align-bottom", AlignVerticalJustifyEnd, "Base", H.alignSelectionBottom],
              ] as const
            ).map(([command, Icon, label, hint]) => (
              <DeckRibbonTile
                key={command}
                icon={Icon}
                label={label}
                hint={hint}
                onClick={() => alignSelected(command as LayoutAlignCommand)}
              />
            ))}
            <DeckRibbonTile
              icon={AlignHorizontalJustifyCenter}
              label="Dist. H"
              hint={H.distributeH}
              disabled={!canDistribute}
              onClick={() => alignSelected("distribute-h")}
            />
            <DeckRibbonTile
              icon={AlignVerticalJustifyCenter}
              label="Dist. V"
              hint={H.distributeV}
              disabled={!canDistribute}
              onClick={() => alignSelected("distribute-v")}
            />
            <DeckRibbonTile
              icon={Group}
              label="Agrupar"
              hint={H.groupSelection}
              disabled={!canGroup}
              onClick={groupSelected}
            />
            <DeckRibbonTile
              icon={Ungroup}
              label="Desagrupar"
              hint={H.ungroupSelection}
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
                <HintAction hint={H.fontFamily} ariaLabel="Ajuda: Família da fonte">
                  <TdRibbonSelect
                    aria-label="Família da fonte"
                    value={selected.style?.fontFamily ?? COMUNICADO_FONT_FAMILIES[0]}
                    onChange={(value) => {
                      ensureComunicadoGoogleFontsLoaded([value]);
                      updateSelectedStyle({ fontFamily: value });
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
                </TdRibbonIconButton>
                <HintAction hint={H.fontSize} ariaLabel="Ajuda: Tamanho da fonte">
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
                </HintAction>
                <TdRibbonIconButton
                  hint={H.fontSizeUp}
                  ariaLabel="Aumentar fonte"
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
                    updateSelectedStyle({
                      fontWeight: selected.style?.fontWeight === "bold" ? "normal" : "bold",
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
                    updateSelectedStyle({
                      fontStyle: selected.style?.fontStyle === "italic" ? "normal" : "italic",
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
                    updateSelectedStyle({
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
                    updateSelectedStyle({
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
                <HintAction hint={H.textHighlight} ariaLabel="Ajuda: Realce do texto">
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
                </HintAction>
                <HintAction hint={H.textColor} ariaLabel="Ajuda: Cor do texto">
                  <input
                    type="color"
                    className="td-deck-ribbon__color"
                    aria-label="Cor do texto"
                    value={selected.style?.color ?? "#ffffff"}
                    onChange={(e) => updateSelectedStyle({ color: e.target.value })}
                  />
                </HintAction>
                <TdRibbonIconButton
                  hint={H.clearFormatting}
                  ariaLabel="Limpar formatação"
                  onClick={() => {
                    const defaults = defaultTextBlockStyle(selected.type);
                    updateSelected({
                      style: { ...defaults, zIndex: selected.style?.zIndex ?? defaults.zIndex },
                    } as Partial<typeof selected>);
                  }}
                >
                  <RemoveFormatting size={15} aria-hidden="true" />
                </TdRibbonIconButton>
              </div>
            </div>
          </DeckRibbonGroup>

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
                    active={selected.style?.textAlign === align}
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
          </div>
        </DeckRibbonGroup>
      ) : (
        <p className="td-subtitle td-deck-ribbon__hint">Selecione um elemento no palco para formatar.</p>
      )}
    </div>
  );
}
