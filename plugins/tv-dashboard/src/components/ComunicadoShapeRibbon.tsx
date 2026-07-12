import { useRef, useState, type ReactNode } from "react";
import { Copy, Replace } from "lucide-react";
import {
  applyMarkerStyleToAll,
  chartPartVisualPrimitive,
  chartPrimitiveSupportsFill,
  chartPrimitiveSupportsStroke,
  defaultFrame,
  defaultStrokeWidthForPrimitive,
  getChartPartState,
  getKpiPartState,
  mergeComunicadoChartOptions,
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  mergeTablePartsWithOptions,
  partsToChartOptions,
  partsToKpiOptions,
  resolveChartAreaStyle,
  resolvePlotAreaStyle,
  resolveShapePrimitive,
  resolveTableFrameStyle,
  shapeHasAdjustments,
  shapeSupportsFill,
  shapeSupportsStroke,
  upsertChartPartState,
  upsertKpiPartState,
  upsertTablePartState,
  type ComunicadoChartViewBlock,
  type ComunicadoKpiViewBlock,
  type ComunicadoShapeKind,
  type ComunicadoTableViewBlock,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  DECK_COLOR_ACCENT,
  DECK_COLOR_BORDER,
  DECK_COLOR_SURFACE,
  DECK_SHAPE_DEFAULTS,
  NativeTextControl,
  ShapeFillMenu,
  ShapeOutlineMenu,
  ShapeShadowMenu,
  ShapeStyleMenu,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../content/comunicadoVisualPresets";
import { rememberComunicadoShape } from "../utils/comunicadoRecentShapes";
import { selectedHasGroup } from "../utils/comunicadoGrouping";
import { resolveSelectedTextFormatTarget } from "../utils/selectedTextFormatTarget";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoShapeLibraryMenu } from "./ComunicadoShapeLibraryMenu";
import { FormatRibbonAlignSection } from "./FormatRibbonAlignSection";
import {
  FormatRibbonOrganizeSection,
  FormatRibbonTextBoxChrome,
  FormatRibbonTypographySections,
  FormatRibbonFrameSection,
} from "./formatRibbon";
import { ShapeAdjustmentsControl } from "./ShapeAdjustmentsControl";
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
    blocks,
    updateSelected,
    updateSelectedStyle,
    alignSelected,
    groupSelected,
    ungroupSelected,
  } = useComunicadoEditor();
  const changeShapeAnchorRef = useRef<HTMLDivElement>(null);
  const [changeShapeOpen, setChangeShapeOpen] = useState(false);

  const multiSelected = selectedIds.length >= 2;
  const canDistribute = selectedIds.length >= 3;
  const canGroup = selectedIds.length >= 2;
  const canUngroup = selectedHasGroup(blocks, selectedIds);

  const textFormatTarget = resolveSelectedTextFormatTarget({
    selected,
    selectedKpiPart,
    selectedChartPart,
  });

  // Parte textual (título/legenda) não tem primitivo visual — chrome cai no chartArea
  // para a faixa Forma não ficar só com Fonte/Parágrafo e espaço vazio.
  const selectedChartVisual =
    selected?.type === "chart_view" && selectedChartPart
      ? chartPartVisualPrimitive(selectedChartPart)
      : null;
  const chartPartPrimitive =
    selected?.type === "chart_view"
      ? (selectedChartVisual ?? ("area" as const))
      : null;
  const effectiveChartPart =
    selected?.type === "chart_view"
      ? selectedChartVisual && selectedChartPart
        ? selectedChartPart
        : { kind: "chartArea" as const }
      : null;

  const isShapeBlock = selected?.type === "shape";
  const isTextBox = selected?.type === "heading" || selected?.type === "text";
  const isMediaBlock = selected?.type === "image" || selected?.type === "video";
  const isChartPartPrimitive = Boolean(chartPartPrimitive);
  /** Chrome do cartão KPI mesmo com parte de texto (título/valor) selecionada. */
  const isKpiChrome = selected?.type === "kpi_view";
  const isTableChrome = selected?.type === "table_view";
  const isDataViewBlock =
    selected?.type === "kpi_view" ||
    selected?.type === "table_view" ||
    selected?.type === "chart_view";
  const hasCapabilityChrome =
    isShapeBlock ||
    isChartPartPrimitive ||
    isKpiChrome ||
    isTableChrome ||
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
      <FormatRibbonTypographySections />
      {isTextBox ? <FormatRibbonTextBoxChrome /> : null}
      {chrome}
      <FormatRibbonFrameSection />
      {opts?.organize !== false &&
      (isShapeBlock || isTextBox || isMediaBlock || isDataViewBlock) ? (
        <FormatRibbonOrganizeSection />
      ) : null}
    </div>
  );

  if (isChartPartPrimitive && selected?.type === "chart_view" && effectiveChartPart && chartPartPrimitive) {
    const block = selected as ComunicadoChartViewBlock;
    const partState = getChartPartState(block.chartParts, effectiveChartPart);
    const showFill = chartPrimitiveSupportsFill(chartPartPrimitive);
    const showStroke = chartPrimitiveSupportsStroke(chartPartPrimitive);
    const areaChrome =
      effectiveChartPart.kind === "chartArea"
        ? resolveChartAreaStyle(block.chartOptions ?? {}, block.chartParts)
        : effectiveChartPart.kind === "plotArea"
          ? {
              ...resolvePlotAreaStyle(block.chartParts),
              borderRadius: partState?.style?.borderRadius ?? 0,
            }
          : null;
    const fillValue =
      areaChrome?.fill ?? partState?.style?.fill ?? DECK_COLOR_ACCENT;
    const strokeValue =
      areaChrome?.stroke ?? partState?.style?.stroke ?? DECK_COLOR_ACCENT;
    const strokeWidth =
      areaChrome?.strokeWidth ??
      partState?.style?.strokeWidth ??
      defaultStrokeWidthForPrimitive(chartPartPrimitive);
    const cornerRadius = areaChrome?.borderRadius ?? partState?.style?.borderRadius ?? 0;
    const showCorners =
      effectiveChartPart.kind === "chartArea" || effectiveChartPart.kind === "plotArea";

    const patchPartStyle = (style: Record<string, unknown>) => {
      let nextParts = upsertChartPartState(block.chartParts, effectiveChartPart, {
        style: style as never,
      });
      const nextOptions = mergeComunicadoChartOptions({
        ...block.chartOptions,
        ...partsToChartOptions(nextParts),
      });
      if (effectiveChartPart.kind === "series" && typeof style.stroke === "string") {
        nextOptions.seriesColor = style.stroke;
      }
      if (effectiveChartPart.kind === "chartArea" && typeof style.fill === "string") {
        nextOptions.backgroundColor = style.fill;
      }
      updateSelected({
        chartParts: nextParts,
        chartOptions: nextOptions,
      } as Partial<ComunicadoBlock>);
    };

    return shell(
      <>
        <DeckRibbonGroup label="Estilos de forma" hint={H.shape}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
            <ShapeStyleMenu
              onSelect={(preset) =>
                patchPartStyle({
                  fill: preset.fill,
                  stroke: preset.stroke,
                  strokeWidth: preset.strokeWidth,
                  ...(showCorners ? { borderRadius: cornerRadius } : {}),
                })
              }
            />
          </div>
        </DeckRibbonGroup>

        <DeckRibbonGroup label="Preenchimento" hint={H.shape}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
            {showFill ? (
              <ShapeFillMenu
                value={fillValue}
                fillLabel={chartPartPrimitive === "point" ? "Cor" : "Preench."}
                onChange={(color) => patchPartStyle({ fill: color })}
                onNoFill={() => patchPartStyle({ fill: "transparent" })}
              />
            ) : (
              <p className="td-subtitle td-deck-ribbon__hint">Sem preenchimento neste primitivo.</p>
            )}
          </div>
        </DeckRibbonGroup>

        <DeckRibbonGroup label="Contorno" hint={H.strokeWidth}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
            {showStroke ? (
              <ShapeOutlineMenu
                color={strokeValue}
                strokeWidth={strokeWidth}
                minWidth={0}
                maxWidth={chartPartPrimitive === "point" ? 8 : 20}
                outlineLabel="Contorno"
                onColorChange={(color) => patchPartStyle({ stroke: color })}
                onNoOutline={() => patchPartStyle({ stroke: "transparent", strokeWidth: 0 })}
                onStrokeWidthChange={(width) => patchPartStyle({ strokeWidth: width })}
              />
            ) : (
              <p className="td-subtitle td-deck-ribbon__hint">Sem contorno neste primitivo.</p>
            )}
            {showCorners ? (
              <ShapeShadowMenu
                value={block.style?.boxShadow}
                presets={SHADOW_MENU_PRESETS}
                shadowLabel="Sombra"
                onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
              />
            ) : null}
          </div>
        </DeckRibbonGroup>

        {effectiveChartPart.kind === "marker" ? (
          <DeckRibbonGroup label="Marcador" hint={H.shape}>
            <div className="td-deck-ribbon__toolbar td-deck-ribbon__toolbar--inline">
              <label className="td-deck-ribbon__field-label" htmlFor="td-chart-marker-radius">
                Raio
              </label>
              <NativeTextControl
                id="td-chart-marker-radius"
                type="number"
                className="td-deck-ribbon__number td-deck-ribbon__number--compact"
                min={1}
                max={12}
                step={0.5}
                value={partState?.style?.markerRadius ?? 2.5}
                onChange={(value) =>
                  patchPartStyle({ markerRadius: Number(value) || 2.5 })
                }
              />
              <DeckRibbonTile
                icon={Copy}
                label="Aplicar a todos"
                hint="Replica o estilo do marcador em todos os pontos da série."
                onClick={() => {
                  const nextParts = applyMarkerStyleToAll(
                    block.chartParts,
                    block.resolved?.chart?.points?.length ?? 0,
                    effectiveChartPart.kind === "marker" ? effectiveChartPart.seriesIndex ?? 0 : 0,
                    partState?.style ?? {},
                  );
                  updateSelected({ chartParts: nextParts } as Partial<ComunicadoBlock>);
                }}
              />
            </div>
          </DeckRibbonGroup>
        ) : null}
      </>,
    );
  }

  if (isKpiChrome && selected?.type === "kpi_view") {
    const block = selected as ComunicadoKpiViewBlock;
    const cardState = getKpiPartState(block.kpiParts, { kind: "card" });
    const fillValue = cardState?.style?.fill ?? block.kpiOptions?.backgroundColor ?? DECK_COLOR_SURFACE;
    const strokeValue = cardState?.style?.stroke ?? DECK_COLOR_BORDER;
    const strokeWidth = cardState?.style?.strokeWidth ?? 1;

    const patchCardStyle = (style: Record<string, unknown>) => {
      const nextParts = upsertKpiPartState(block.kpiParts, { kind: "card" }, {
        style: style as never,
      });
      const fromParts = partsToKpiOptions(nextParts);
      const nextOptions = mergeComunicadoKpiOptions({
        ...block.kpiOptions,
        ...fromParts,
        ...(typeof style.fill === "string" ? { backgroundColor: style.fill } : {}),
      });
      updateSelected({
        kpiParts: mergeKpiPartsWithOptions(nextParts, nextOptions),
        kpiOptions: nextOptions,
      } as Partial<ComunicadoBlock>);
    };

    return shell(
      <>
        <DeckRibbonGroup label="Aparência" hint={H.shape}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
            <ShapeStyleMenu
              onSelect={(preset) =>
                patchCardStyle({
                  fill: preset.fill,
                  stroke: preset.stroke,
                  strokeWidth: preset.strokeWidth,
                })
              }
            />
            <ShapeFillMenu
              value={fillValue}
              fillLabel="Preench."
              onChange={(color) => patchCardStyle({ fill: color })}
              onNoFill={() => patchCardStyle({ fill: "transparent" })}
            />
            <ShapeOutlineMenu
              color={strokeValue}
              strokeWidth={strokeWidth}
              minWidth={0}
              maxWidth={20}
              outlineLabel="Contorno"
              onColorChange={(color) => patchCardStyle({ stroke: color })}
              onNoOutline={() => patchCardStyle({ stroke: "transparent", strokeWidth: 0 })}
              onStrokeWidthChange={(width) => patchCardStyle({ strokeWidth: width })}
            />
            <ShapeShadowMenu
              value={block.style?.boxShadow}
              presets={SHADOW_MENU_PRESETS}
              shadowLabel="Sombra"
              onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
            />
          </div>
        </DeckRibbonGroup>
      </>,
    );
  }

  if (isTableChrome && selected?.type === "table_view") {
    const block = selected as ComunicadoTableViewBlock;
    const frame = resolveTableFrameStyle(block.tableParts);
    const fillValue = frame.fill;
    const strokeValue = frame.stroke;
    const strokeWidth = frame.strokeWidth;

    const patchFrameStyle = (style: Record<string, unknown>) => {
      const nextParts = upsertTablePartState(block.tableParts, { kind: "frame" }, {
        style: style as never,
      });
      updateSelected({
        tableParts: mergeTablePartsWithOptions(nextParts, block.tableOptions),
        ...(typeof style.borderRadius === "number"
          ? { style: { ...block.style, borderRadius: style.borderRadius } }
          : {}),
      } as Partial<ComunicadoBlock>);
    };

    return shell(
      <>
        <DeckRibbonGroup label="Aparência" hint={H.shape}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
            <ShapeStyleMenu
              onSelect={(preset) =>
                patchFrameStyle({
                  fill: preset.fill,
                  stroke: preset.stroke,
                  strokeWidth: preset.strokeWidth,
                })
              }
            />
            <ShapeFillMenu
              value={fillValue}
              fillLabel="Preench."
              onChange={(color) => patchFrameStyle({ fill: color })}
              onNoFill={() => patchFrameStyle({ fill: "transparent" })}
            />
            <ShapeOutlineMenu
              color={strokeValue}
              strokeWidth={strokeWidth}
              minWidth={0}
              maxWidth={20}
              outlineLabel="Contorno"
              onColorChange={(color) => patchFrameStyle({ stroke: color })}
              onNoOutline={() => patchFrameStyle({ stroke: "transparent", strokeWidth: 0 })}
              onStrokeWidthChange={(width) => patchFrameStyle({ strokeWidth: width })}
            />
            <ShapeShadowMenu
              value={block.style?.boxShadow}
              presets={SHADOW_MENU_PRESETS}
              shadowLabel="Sombra"
              onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
            />
          </div>
        </DeckRibbonGroup>
      </>,
    );
  }

  if (!isShapeBlock) {
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
          <div className="td-deck-ribbon__toolbar td-deck-ribbon__toolbar--inline">
            <label className="td-deck-ribbon__field-label" htmlFor="td-shape-marker-radius">
              Raio px
            </label>
            <NativeTextControl
              id="td-shape-marker-radius"
              type="number"
              className="td-deck-ribbon__number td-deck-ribbon__number--compact"
              min={2}
              max={48}
              step={1}
              aria-label="Raio do ponto em pixels"
              value={block.style?.markerRadius ?? 8}
              onChange={(value) =>
                updateSelectedStyle({ markerRadius: Math.max(2, Math.min(48, Number(value) || 8)) })
              }
            />
          </div>
        </DeckRibbonGroup>
      ) : null}
    </>,
  );
}
