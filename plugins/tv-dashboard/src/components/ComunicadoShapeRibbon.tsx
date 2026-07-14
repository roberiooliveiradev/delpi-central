import { useRef, useState, type ReactNode } from "react";
import { Replace } from "lucide-react";
import {
  canConnectBlocks,
  chartPartVisualPrimitive,
  defaultFrame,
  defaultStrokeWidthForPrimitive,
  getInputPartState,
  getKpiPartState,
  inputPartBoxChromeLabels,
  kpiPartBoxChromeLabels,
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  resolveInputShapeChromePartRef,
  resolveKpiShapeChromePartRef,
  resolveShapePrimitive,
  shapeHasAdjustments,
  shapeSupportsFill,
  shapeSupportsStroke,
  upsertInputPartState,
  upsertKpiPartState,
  type ComunicadoChartViewBlock,
  type ComunicadoInputBlock,
  type ComunicadoKpiViewBlock,
  type ComunicadoShapeKind,
  type ComunicadoTableViewBlock,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  DECK_COLOR_BORDER,
  DECK_COLOR_SURFACE,
  DECK_INPUT_DEFAULTS,
  DECK_SHAPE_DEFAULTS,
  ShapeFillMenu,
  ShapeOutlineMenu,
  ShapeShadowMenu,
  ShapeStyleRibbonStrip,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../content/comunicadoVisualPresets";
import { rememberComunicadoShape } from "../utils/comunicadoRecentShapes";
import { selectedHasGroup } from "../utils/comunicadoGrouping";
import { resolveSelectedTextFormatTarget } from "../utils/selectedTextFormatTarget";
import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoShapeLibraryMenu } from "./ComunicadoShapeLibraryMenu";
import { FormatRibbonAlignSection } from "./FormatRibbonAlignSection";
import {
  FormatRibbonOrganizeSection,
  FormatRibbonTextBoxChrome,
  FormatRibbonTypographySections,
  FormatRibbonFrameSection,
} from "./formatRibbon";
import { ChartRibbonShapeChrome } from "./formatRibbon/ChartRibbonShapeChrome";
import { TableRibbonShapeChrome } from "./formatRibbon/TableRibbonShapeChrome";
import { PartSelectionNav } from "./ComunicadoPartFormatRibbon";
import { ShapeAdjustmentsControl } from "./ShapeAdjustmentsControl";
import { DeckRangeField } from "./deck/DeckRangeField";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const SHADOW_MENU_PRESETS = COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
  id: preset.key,
  label: preset.label,
  value: preset.value,
}));

/**
 * Faixa contextual «Forma» — chrome + tipografia por capacidade do objeto
 * (forma, caixa de texto, mídia, KPI/tabela/gráfico).
 */
export function ComunicadoShapeRibbon() {
  const {
    selected,
    selectedIds,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    blocks,
    updateSelected,
    updateSelectedStyle,
    alignSelected,
    groupSelected,
    ungroupSelected,
    connectSelected,
    clearKpiPartSelection,
    clearInputPartSelection,
    selectedInputPart,
  } = useComunicadoEditor();
  const changeShapeAnchorRef = useRef<HTMLDivElement>(null);
  const [changeShapeOpen, setChangeShapeOpen] = useState(false);

  const selectionChrome = resolveSelectionChromeMode({
    selected,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectedInputPart,
  });
  const partChrome = isPartSelectionChrome(selectionChrome) ? selectionChrome : null;

  const multiSelected = selectedIds.length >= 2;
  const canDistribute = selectedIds.length >= 3;
  const canGroup = selectedIds.length >= 2;
  const canUngroup = selectedHasGroup(blocks, selectedIds);
  const canConnect = (() => {
    if (selectedIds.length !== 2) return false;
    const [idA, idB] = selectedIds;
    const a = blocks.find((block) => block.id === idA);
    const b = blocks.find((block) => block.id === idB);
    return Boolean(a && b && canConnectBlocks(a, b));
  })();

  const textFormatTarget = resolveSelectedTextFormatTarget({
    selected,
    selectedKpiPart,
    selectedChartPart,
  });

  // Chrome Forma: parte selecionada (primitivo visual ou title/legend com fill próprio).
  // Sem seleção → chartArea.
  const selectedChartVisual =
    selected?.type === "chart_view" && selectedChartPart
      ? chartPartVisualPrimitive(selectedChartPart)
      : null;
  const chartTextChromeKinds = new Set([
    "title",
    "legend",
    "axisTitle",
    "dataLabel",
    "dataLabels",
    "dataTable",
  ]);
  const chartPartHasOwnChrome =
    Boolean(selectedChartVisual) ||
    Boolean(selectedChartPart && chartTextChromeKinds.has(selectedChartPart.kind));
  const chartPartPrimitive =
    selected?.type === "chart_view"
      ? (selectedChartVisual ??
        (selectedChartPart && chartTextChromeKinds.has(selectedChartPart.kind)
          ? ("area" as const)
          : selectedChartPart
            ? null
            : ("area" as const)))
      : null;
  const effectiveChartPart =
    selected?.type === "chart_view"
      ? selectedChartPart && chartPartHasOwnChrome
        ? selectedChartPart
        : { kind: "chartArea" as const }
      : null;

  const isShapeBlock = selected?.type === "shape";
  const isTextBox = selected?.type === "heading" || selected?.type === "text";
  const isMediaBlock = selected?.type === "image" || selected?.type === "video";
  const isChartPartPrimitive = Boolean(chartPartPrimitive);
  /** Chrome KPI: card global ou parte selecionada (title/value/hint/icon). */
  const isKpiChrome = selected?.type === "kpi_view";
  const isTableChrome = selected?.type === "table_view";
  const isInputChrome = selected?.type === "input";
  const isDataViewBlock =
    selected?.type === "kpi_view" ||
    selected?.type === "table_view" ||
    selected?.type === "chart_view";
  const hasCapabilityChrome =
    isShapeBlock ||
    isChartPartPrimitive ||
    isKpiChrome ||
    isTableChrome ||
    isInputChrome ||
    isTextBox ||
    isMediaBlock ||
    textFormatTarget != null ||
    multiSelected;

  if (!hasCapabilityChrome) {
    return (
      <div className="td-deck-ribbon__groups">
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione um elemento no palco para formatar texto, preenchimento, contorno e organização.
        </p>
      </div>
    );
  }

  const shell = (chrome: ReactNode, opts?: { organize?: boolean }) => (
    <div className="td-deck-ribbon__groups">
      {partChrome && partChrome.source === "kpi" ? (
        <PartSelectionNav chrome={partChrome} onBack={clearKpiPartSelection} />
      ) : null}
      {partChrome && partChrome.source === "input" ? (
        <PartSelectionNav chrome={partChrome} onBack={clearInputPartSelection} />
      ) : null}
      {multiSelected ? (
        <FormatRibbonAlignSection
          canDistribute={canDistribute}
          canGroup={canGroup}
          canUngroup={canUngroup}
          canConnect={canConnect}
          alignSelected={alignSelected}
          groupSelected={groupSelected}
          ungroupSelected={ungroupSelected}
          connectSelected={connectSelected}
        />
      ) : null}
      <FormatRibbonTypographySections />
      {isTextBox ? <FormatRibbonTextBoxChrome /> : null}
      <div className="td-deck-ribbon__group-cluster td-deck-ribbon__group-cluster--chrome-frame-organize">
        {chrome}
        <FormatRibbonFrameSection />
        {opts?.organize !== false &&
        (isShapeBlock || isTextBox || isMediaBlock || isDataViewBlock) ? (
          <FormatRibbonOrganizeSection />
        ) : null}
      </div>
    </div>
  );

  if (isChartPartPrimitive && selected?.type === "chart_view" && effectiveChartPart && chartPartPrimitive) {
    const block = selected as ComunicadoChartViewBlock;
    return shell(
      <ChartRibbonShapeChrome block={block} />,
    );
  }

  if (isKpiChrome && selected?.type === "kpi_view") {
    const block = selected as ComunicadoKpiViewBlock;
    const chromePart = resolveKpiShapeChromePartRef(selectedKpiPart);
    if (!chromePart) {
      return shell(
        <p className="td-subtitle td-deck-ribbon__hint">
          Seleção global do KPI — posição, tamanho e organizar. Clique no fundo ou numa parte
          para formatar preenchimento e contorno.
        </p>,
      );
    }
    const partState = getKpiPartState(block.kpiParts, chromePart);
    const isCardChrome = chromePart.kind === "card";
    const boxLabels = kpiPartBoxChromeLabels(chromePart.kind);
    const cardState = getKpiPartState(block.kpiParts, { kind: "card" });
    const fillValue = isCardChrome
      ? (cardState?.style?.fill ?? block.kpiOptions?.backgroundColor ?? DECK_COLOR_SURFACE)
      : (partState?.style?.fill ?? "transparent");
    const strokeValue = isCardChrome
      ? (cardState?.style?.stroke ?? DECK_COLOR_BORDER)
      : (partState?.style?.stroke ?? "transparent");
    const strokeWidth = isCardChrome
      ? (cardState?.style?.strokeWidth ?? 1)
      : (partState?.style?.strokeWidth ?? 0);

    const patchChromeStyle = (style: Record<string, unknown>) => {
      const nextParts = upsertKpiPartState(block.kpiParts, chromePart, {
        style: style as never,
      });
      const fromParts = partsToKpiOptions(nextParts);
      const nextOptions = mergeComunicadoKpiOptions({
        ...block.kpiOptions,
        ...fromParts,
        ...(isCardChrome && typeof style.fill === "string"
          ? { backgroundColor: style.fill }
          : {}),
      });
      updateSelected({
        kpiParts: mergeKpiPartsWithOptions(nextParts, nextOptions),
        kpiOptions: nextOptions,
      } as Partial<ComunicadoBlock>);
    };

    return shell(
      <>
        <DeckRibbonGroup
          label="Aparência"
          hint={
            isCardChrome
              ? H.shape
              : "Fundo e borda da caixa desta parte — não alteram o fundo do card."
          }
        >
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
            <ShapeStyleRibbonStrip
              maxVisible={5}
              onSelect={(preset) =>
                patchChromeStyle({
                  fill: preset.fill,
                  stroke: preset.stroke,
                  strokeWidth: preset.strokeWidth,
                })
              }
            />
            <ShapeFillMenu
              value={fillValue}
              fillLabel={boxLabels.fillShort}
              onChange={(color) => patchChromeStyle({ fill: color })}
              onNoFill={() => patchChromeStyle({ fill: "transparent" })}
            />
            <ShapeOutlineMenu
              color={strokeValue}
              strokeWidth={strokeWidth}
              minWidth={0}
              maxWidth={20}
              outlineLabel={boxLabels.strokeShort}
              onColorChange={(color) => patchChromeStyle({ stroke: color })}
              onNoOutline={() => patchChromeStyle({ stroke: "transparent", strokeWidth: 0 })}
              onStrokeWidthChange={(width) => patchChromeStyle({ strokeWidth: width })}
            />
            {isCardChrome ? (
              <ShapeShadowMenu
                value={block.style?.boxShadow}
                presets={SHADOW_MENU_PRESETS}
                shadowLabel="Sombra"
                onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
              />
            ) : null}
          </div>
        </DeckRibbonGroup>
      </>,
    );
  }

  if (isInputChrome && selected?.type === "input") {
    const block = selected as ComunicadoInputBlock;
    const chromePart = resolveInputShapeChromePartRef(selectedInputPart) ?? { kind: "frame" as const };
    const partState = getInputPartState(block.inputParts, chromePart);
    const isFrameChrome = chromePart.kind === "frame";
    const boxLabels = inputPartBoxChromeLabels(chromePart.kind);
    const fillValue =
      partState?.style?.fill ??
      (isFrameChrome ? DECK_INPUT_DEFAULTS.backgroundColor : "transparent");
    const strokeValue =
      partState?.style?.stroke ??
      (isFrameChrome ? DECK_INPUT_DEFAULTS.borderColor : "transparent");
    const strokeWidth =
      partState?.style?.strokeWidth ??
      (isFrameChrome ? DECK_INPUT_DEFAULTS.borderWidth : 0);

    const patchChromeStyle = (style: Record<string, unknown>) => {
      updateSelected({
        inputParts: upsertInputPartState(block.inputParts, chromePart, {
          style: style as never,
        }),
      } as Partial<ComunicadoBlock>);
    };

    return shell(
      <DeckRibbonGroup label="Aparência" hint={H.shape}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          <ShapeFillMenu
            value={fillValue}
            fillLabel={boxLabels.fillShort}
            onChange={(color) => patchChromeStyle({ fill: color })}
            onNoFill={() => patchChromeStyle({ fill: "transparent" })}
          />
          <ShapeOutlineMenu
            color={strokeValue}
            strokeWidth={strokeWidth}
            minWidth={0}
            maxWidth={20}
            outlineLabel={boxLabels.strokeShort}
            onColorChange={(color) => patchChromeStyle({ stroke: color })}
            onNoOutline={() => patchChromeStyle({ stroke: "transparent", strokeWidth: 0 })}
            onStrokeWidthChange={(width) => patchChromeStyle({ strokeWidth: width })}
          />
        </div>
      </DeckRibbonGroup>,
    );
  }

  if (isTableChrome && selected?.type === "table_view") {
    return shell(<TableRibbonShapeChrome block={selected as ComunicadoTableViewBlock} />);
  }

  if (!isShapeBlock || !selected || selected.type !== "shape") {
    return shell(null);
  }

  const block = selected;

  const primitive = resolveShapePrimitive(block.shape);
  const showFill = shapeSupportsFill(primitive);
  const showStroke = shapeSupportsStroke(primitive);
  const defaultStrokeWidth = block.style?.strokeWidth ?? defaultStrokeWidthForPrimitive(primitive);
  const showShapeAdjustments = shapeHasAdjustments(block.shape);

  const applyShapeKind = (kind: ComunicadoShapeKind) => {
    const prevPrimitive = resolveShapePrimitive(block.shape);
    const nextPrimitive = resolveShapePrimitive(kind);
    const patch: Record<string, unknown> = { shape: kind };
    if (prevPrimitive !== nextPrimitive) {
      const nextFrame = defaultFrame("shape", kind);
      patch.frame = {
        ...nextFrame,
        x: Math.max(0, Math.min(100 - nextFrame.w, block.frame.x)),
        y: Math.max(0, Math.min(100 - nextFrame.h, block.frame.y)),
      };
      patch.style = {
        ...block.style,
        strokeWidth: defaultStrokeWidthForPrimitive(nextPrimitive),
        ...(nextPrimitive === "point"
          ? { markerRadius: block.style?.markerRadius ?? 8 }
          : {}),
      };
    }
    updateSelected(patch as Partial<ComunicadoBlock>);
    rememberComunicadoShape(kind);
    setChangeShapeOpen(false);
  };

  return shell(
    <>
      <DeckRibbonGroup label="Formas" hint={H.shapeChange}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <div ref={changeShapeAnchorRef} className="td-composer__dropdown">
            <DeckRibbonTile
              icon={Replace}
              label="Alterar forma"
              hint={H.shapeChange}
              active={changeShapeOpen}
              onClick={() => setChangeShapeOpen((open) => !open)}
            />
            {changeShapeOpen ? (
              <ComunicadoShapeLibraryMenu
                open={changeShapeOpen}
                anchorRef={changeShapeAnchorRef}
                onSelect={applyShapeKind}
              />
            ) : null}
          </div>
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Estilos de forma" hint={H.shape}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          <ShapeStyleRibbonStrip
            onSelect={(preset) =>
              updateSelectedStyle({
                fill: preset.fill,
                stroke: preset.stroke,
                strokeWidth: preset.strokeWidth,
                boxShadow: preset.boxShadow,
              })
            }
          />
          <ShapeShadowMenu
            value={block.style?.boxShadow}
            presets={SHADOW_MENU_PRESETS}
            shadowLabel="Sombra"
            onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Preenchimento" hint={H.shape}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          {showFill ? (
            <ShapeFillMenu
              value={block.style?.fill ?? DECK_SHAPE_DEFAULTS.fill}
              fillLabel={primitive === "point" ? "Cor" : "Preench."}
              onChange={(color) => updateSelectedStyle({ fill: color })}
              onNoFill={() => updateSelectedStyle({ fill: "transparent" })}
            />
          ) : (
            <p className="td-subtitle td-deck-ribbon__hint">Sem preenchimento nesta forma.</p>
          )}
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Contorno" hint={H.strokeWidth}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          {showStroke ? (
            <ShapeOutlineMenu
              color={
                block.style?.stroke ??
                (primitive === "line" ? DECK_SHAPE_DEFAULTS.lineStroke : DECK_SHAPE_DEFAULTS.stroke)
              }
              strokeWidth={defaultStrokeWidth}
              minWidth={0}
              maxWidth={primitive === "point" ? 8 : 20}
              outlineLabel="Contorno"
              onColorChange={(color) => updateSelectedStyle({ stroke: color })}
              onNoOutline={() => updateSelectedStyle({ stroke: "transparent" })}
              onStrokeWidthChange={(width) => updateSelectedStyle({ strokeWidth: width })}
            />
          ) : (
            <p className="td-subtitle td-deck-ribbon__hint">Sem contorno nesta forma.</p>
          )}
        </div>
      </DeckRibbonGroup>

      {showShapeAdjustments ? (
        <ShapeAdjustmentsControl
          kind={block.shape}
          style={block.style}
          onChange={(patch) => updateSelectedStyle(patch)}
          variant="ribbon"
        />
      ) : null}

      {primitive === "point" ? (
        <DeckRibbonGroup label="Marcador" hint={H.shapeSize}>
          <DeckRangeField
            id="td-shape-marker-radius"
            label="Raio px"
            hint={H.shapeSize}
            min={2}
            max={48}
            step={1}
            value={block.style?.markerRadius ?? 8}
            aria-label="Raio do ponto em pixels"
            onChange={(value) =>
              updateSelectedStyle({ markerRadius: Math.max(2, Math.min(48, value || 8)) })
            }
          />
        </DeckRibbonGroup>
      ) : null}
    </>,
  );
}
