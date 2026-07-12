import { useRef, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  Copy,
  Replace,
  Trash2,
} from "lucide-react";
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
  partsToChartOptions,
  partsToKpiOptions,
  resolveChartAreaStyle,
  resolvePlotAreaStyle,
  resolveShapePrimitive,
  shapeSupportsFill,
  shapeSupportsStroke,
  upsertChartPartState,
  upsertKpiPartState,
  type ComunicadoChartViewBlock,
  type ComunicadoKpiViewBlock,
  type ComunicadoShapeKind,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  DECK_COLOR_ACCENT,
  DECK_COLOR_BORDER,
  DECK_COLOR_SURFACE,
  DECK_SHAPE_DEFAULTS,
  NativeTextControl,
  OFFICE_CHART_AREA_STROKE,
  ShapeEffectsMenu,
  ShapeFillMenu,
  ShapeOutlineMenu,
  ShapeStyleMenu,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { rememberComunicadoShape } from "../utils/comunicadoRecentShapes";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoShapeLibraryMenu } from "./ComunicadoShapeLibraryMenu";
import { ShapeCornerRadiusControl } from "./ShapeCornerRadiusControl";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

/**
 * Faixa contextual «Forma» — shape, chartArea/plotArea, card KPI e moldura de tabela.
 */
export function ComunicadoShapeRibbon() {
  const {
    selected,
    selectedChartPart,
    selectedKpiPart,
    updateSelected,
    updateSelectedStyle,
    removeSelected,
    duplicateSelected,
    moveLayer,
  } = useComunicadoEditor();
  const changeShapeAnchorRef = useRef<HTMLDivElement>(null);
  const [changeShapeOpen, setChangeShapeOpen] = useState(false);

  const chartPartPrimitive =
    selected?.type === "chart_view" && selectedChartPart
      ? chartPartVisualPrimitive(selectedChartPart)
      : selected?.type === "chart_view" && !selectedChartPart
        ? ("area" as const)
        : null;
  const effectiveChartPart =
    selected?.type === "chart_view"
      ? selectedChartPart ?? { kind: "chartArea" as const }
      : null;

  const isShapeBlock = selected?.type === "shape";
  const isChartPartPrimitive = Boolean(chartPartPrimitive);
  const isKpiChrome =
    selected?.type === "kpi_view" &&
    (!selectedKpiPart || selectedKpiPart.kind === "card");
  const isTableChrome = selected?.type === "table_view";

  if (!isShapeBlock && !isChartPartPrimitive && !isKpiChrome && !isTableChrome) {
    return (
      <div className="td-deck-ribbon__groups">
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione uma forma, gráfico, KPI ou tabela — ou dê duplo clique numa parte do gráfico —
          para formatar preenchimento, contorno e cantos.
        </p>
      </div>
    );
  }

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
      } as Partial<typeof selected>);
    };

    return (
      <div className="td-deck-ribbon__groups">
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
          </div>
        </DeckRibbonGroup>

        {showCorners ? (
          <ShapeCornerRadiusControl
            id="td-chart-area-corner-radius"
            value={cornerRadius}
            onChange={(radius) => patchPartStyle({ borderRadius: radius })}
          />
        ) : null}

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
                    style,
                  );
                  updateSelected({ chartParts: nextParts } as Partial<typeof selected>);
                }}
              />
            </div>
          </DeckRibbonGroup>
        ) : null}
      </div>
    );
  }

  if (isKpiChrome && selected?.type === "kpi_view") {
    const block = selected as ComunicadoKpiViewBlock;
    const cardState = getKpiPartState(block.kpiParts, { kind: "card" });
    const fillValue = cardState?.style?.fill ?? block.kpiOptions?.backgroundColor ?? DECK_COLOR_SURFACE;
    const strokeValue = cardState?.style?.stroke ?? DECK_COLOR_BORDER;
    const strokeWidth = cardState?.style?.strokeWidth ?? 1;
    const cornerRadius = cardState?.style?.borderRadius ?? block.style?.borderRadius ?? 0;

    const patchCardStyle = (style: Record<string, unknown>) => {
      const nextParts = upsertKpiPartState(block.kpiParts, { kind: "card" }, {
        style: style as never,
      });
      const nextOptions = mergeComunicadoKpiOptions({
        ...block.kpiOptions,
        ...partsToKpiOptions(nextParts),
      });
      const nextBlockStyle = { ...block.style };
      if (typeof style.borderRadius === "number") {
        nextBlockStyle.borderRadius = style.borderRadius;
      }
      updateSelected({
        kpiParts: nextParts,
        kpiOptions: nextOptions,
        style: nextBlockStyle,
      } as Partial<typeof selected>);
    };

    return (
      <div className="td-deck-ribbon__groups">
        <DeckRibbonGroup label="Estilos de forma" hint={H.shape}>
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
          </div>
        </DeckRibbonGroup>
        <DeckRibbonGroup label="Preenchimento" hint={H.shape}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
            <ShapeFillMenu
              value={fillValue}
              fillLabel="Preench."
              onChange={(color) => patchCardStyle({ fill: color })}
              onNoFill={() => patchCardStyle({ fill: "transparent" })}
            />
          </div>
        </DeckRibbonGroup>
        <DeckRibbonGroup label="Contorno" hint={H.strokeWidth}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
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
          </div>
        </DeckRibbonGroup>
        <ShapeCornerRadiusControl
          id="td-kpi-card-corner-radius"
          value={cornerRadius}
          onChange={(radius) => patchCardStyle({ borderRadius: radius })}
        />
      </div>
    );
  }

  if (isTableChrome && selected?.type === "table_view") {
    const block = selected as ComunicadoTableViewBlock;
    const fillValue = block.style?.backgroundColor ?? block.style?.fill ?? DECK_COLOR_SURFACE;
    const strokeValue = block.style?.borderColor ?? block.style?.stroke ?? OFFICE_CHART_AREA_STROKE;
    const strokeWidth = block.style?.borderWidth ?? block.style?.strokeWidth ?? 1;
    const cornerRadius = block.style?.borderRadius ?? 0;

    return (
      <div className="td-deck-ribbon__groups">
        <DeckRibbonGroup label="Estilos de forma" hint={H.shape}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
            <ShapeStyleMenu
              onSelect={(preset) =>
                updateSelectedStyle({
                  fill: preset.fill,
                  backgroundColor: preset.fill,
                  stroke: preset.stroke,
                  borderColor: preset.stroke,
                  strokeWidth: preset.strokeWidth,
                  borderWidth: preset.strokeWidth,
                  boxShadow: preset.boxShadow,
                })
              }
            />
          </div>
        </DeckRibbonGroup>
        <DeckRibbonGroup label="Preenchimento" hint={H.shape}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
            <ShapeFillMenu
              value={fillValue}
              fillLabel="Preench."
              onChange={(color) => updateSelectedStyle({ fill: color, backgroundColor: color })}
              onNoFill={() => updateSelectedStyle({ fill: "transparent", backgroundColor: "transparent" })}
            />
          </div>
        </DeckRibbonGroup>
        <DeckRibbonGroup label="Contorno" hint={H.strokeWidth}>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
            <ShapeOutlineMenu
              color={strokeValue}
              strokeWidth={strokeWidth}
              minWidth={0}
              maxWidth={20}
              outlineLabel="Contorno"
              onColorChange={(color) => updateSelectedStyle({ stroke: color, borderColor: color })}
              onNoOutline={() =>
                updateSelectedStyle({ stroke: "transparent", borderColor: "transparent", borderWidth: 0, strokeWidth: 0 })
              }
              onStrokeWidthChange={(width) =>
                updateSelectedStyle({ strokeWidth: width, borderWidth: width })
              }
            />
          </div>
        </DeckRibbonGroup>
        <ShapeCornerRadiusControl
          id="td-table-corner-radius"
          value={cornerRadius}
          onChange={(radius) => updateSelectedStyle({ borderRadius: radius })}
        />
      </div>
    );
  }

  const block = selected!;
  if (block.type !== "shape") return null;

  const primitive = resolveShapePrimitive(block.shape);
  const showFill = shapeSupportsFill(primitive);
  const showStroke = shapeSupportsStroke(primitive);
  const defaultStrokeWidth = block.style?.strokeWidth ?? defaultStrokeWidthForPrimitive(primitive);
  const showCorners = primitive === "area";

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
    updateSelected(patch as Partial<typeof selected>);
    rememberComunicadoShape(kind);
    setChangeShapeOpen(false);
  };

  const setFrameSize = (axis: "w" | "h", raw: number) => {
    const value = Math.max(0.5, Math.min(100, Number.isFinite(raw) ? raw : block.frame[axis]));
    const next = { ...block.frame, [axis]: value };
    if (axis === "w") {
      next.x = Math.max(0, Math.min(100 - value, block.frame.x));
    } else {
      next.y = Math.max(0, Math.min(100 - value, block.frame.y));
    }
    updateSelected({ frame: next } as Partial<typeof selected>);
  };

  return (
    <div className="td-deck-ribbon__groups">
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
          <ShapeEffectsMenu
            onSelect={(effectId, optionId) => {
              if (effectId === "shadow" && !optionId) {
                updateSelectedStyle({ boxShadow: "0 4px 14px rgba(0, 0, 0, 0.28)" });
              }
            }}
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
              color={block.style?.stroke ?? DECK_SHAPE_DEFAULTS.stroke}
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

      {showCorners ? (
        <ShapeCornerRadiusControl
          id="td-shape-corner-radius"
          value={block.style?.borderRadius ?? 0}
          onChange={(radius) => updateSelectedStyle({ borderRadius: radius })}
        />
      ) : null}

      <DeckRibbonGroup label="Organizar" hint={H.organize}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile icon={Copy} label="Duplicar" hint={H.duplicateBlock} onClick={duplicateSelected} />
          <DeckRibbonTile icon={ArrowUp} label="Frente" hint={E.layerUp} onClick={() => moveLayer("up")} />
          <DeckRibbonTile icon={ArrowDown} label="Fundo" hint={E.layerDown} onClick={() => moveLayer("down")} />
          <DeckRibbonTile icon={Trash2} label="Remover" hint={E.remove} onClick={removeSelected} />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Tamanho" hint={H.shapeSize}>
        <div className="td-deck-ribbon__toolbar td-deck-ribbon__toolbar--inline">
          <label className="td-deck-ribbon__field-label" htmlFor="td-shape-width">
            Largura %
          </label>
          <NativeTextControl
            id="td-shape-width"
            type="number"
            className="td-deck-ribbon__number td-deck-ribbon__number--compact"
            min={0.5}
            max={100}
            step={0.5}
            aria-label="Largura da forma em percentual do slide"
            value={Number(block.frame.w.toFixed(1))}
            onChange={(value) => setFrameSize("w", Number(value))}
          />
          <label className="td-deck-ribbon__field-label" htmlFor="td-shape-height">
            Altura %
          </label>
          <NativeTextControl
            id="td-shape-height"
            type="number"
            className="td-deck-ribbon__number td-deck-ribbon__number--compact"
            min={0.5}
            max={100}
            step={0.5}
            aria-label="Altura da forma em percentual do slide"
            value={Number(block.frame.h.toFixed(1))}
            onChange={(value) => setFrameSize("h", Number(value))}
          />
        </div>
      </DeckRibbonGroup>
    </div>
  );
}
