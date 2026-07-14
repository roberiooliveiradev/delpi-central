import {
  blockUsesInnerShapeChrome,
  chartPartAllowsFrame,
  clampChartPartFrame,
  clampKpiPartFrame,
  defaultChartPartFrame,
  defaultKpiPartFrame,
  formatDesignPx,
  framePercentToPageBottomLeftPx,
  getChartPartState,
  getKpiPartState,
  hostRelativeFrameToPageBottomLeftPx,
  resolveKpiPartFrame,
  isPointShapeKind,
  kpiPartAllowsFrame,
  mergeChartPartsWithOptions,
  mergeKpiPartsWithOptions,
  partsToChartOptions,
  partsToKpiOptions,
  patchComunicadoFrame,
  patchComunicadoFramePageBottomLeftPx,
  patchHostRelativeFramePageBottomLeftPx,
  resolveBlockShapeChromeStyle,
  resolveViewportPixelSize,
  scaleChartPartTypographyOnResize,
  scaleComplexBlockOnResize,
  scaleKpiPartTypographyOnResize,
  seedKpiPartsFreeLayoutFrames,
  upsertChartPartState,
  upsertKpiPartState,
  type ComunicadoBlock,
  type ComunicadoChartViewBlock,
  type ComunicadoFrame,
  type ComunicadoKpiViewBlock,
  type KpiFramePartKind,
  type ViewportPixelSize,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { DeckRangeField } from "../deck/DeckRangeField";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { useComunicadoEditor } from "../comunicadoEditorContext";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

const SIZE_KEYS = ["w", "h"] as const;
const POSITION_KEYS = ["x", "y"] as const;

const FRAME_LABELS: Record<"x" | "y" | "w" | "h", string> = {
  x: "X px",
  y: "Y px",
  w: "Larg. px",
  h: "Alt. px",
};

const FRAME_HINTS: Record<"x" | "y" | "w" | "h", string> = {
  x: H.frameX,
  y: H.frameY,
  w: H.frameW,
  h: H.frameH,
};

/** @deprecated Preferir `patchComunicadoFrame` / `patchComunicadoFrameDesignPx` em presentation. */
export { patchComunicadoFrame };

/**
 * Posição / tamanho / rotação / raio — bloco no palco ou parte do KPI/gráfico
 * (title/value/hint/icon ou title/legend/plotArea), espelhando o inspetor.
 * UI em px de design; modelo permanece em %.
 */
export function FormatRibbonFrameSection() {
  const {
    selected,
    selectedIds,
    selectedKpiPart,
    selectedChartPart,
    updateSelected,
    updateSelectedStyle,
    viewportProfile,
  } = useComunicadoEditor();

  const slideDesign = resolveViewportPixelSize(viewportProfile);

  if (!selected || selectedIds.length > 1) return null;

  /* Parte de gráfico sem geometria própria (rótulos, série, eixos…) — não editar o frame do bloco. */
  if (
    selected.type === "chart_view" &&
    selectedChartPart &&
    !chartPartAllowsFrame(selectedChartPart)
  ) {
    return null;
  }

  const kpiPartTarget =
    selected.type === "kpi_view" && selectedKpiPart && kpiPartAllowsFrame(selectedKpiPart)
      ? selectedKpiPart
      : null;

  if (kpiPartTarget && selected.type === "kpi_view") {
    const block = selected as ComunicadoKpiViewBlock;
    const partState = getKpiPartState(block.kpiParts, kpiPartTarget);
    const frameKind = kpiPartTarget.kind as KpiFramePartKind;
    const explicitFrame = resolveKpiPartFrame(partState);
    const partFrame = clampKpiPartFrame(explicitFrame ?? defaultKpiPartFrame(frameKind));
    const borderRadius = partState?.style?.borderRadius ?? 0;
    const frameKeys = [...POSITION_KEYS, ...SIZE_KEYS] as const;
    const partFrameFull: ComunicadoFrame = {
      x: partFrame.x,
      y: partFrame.y,
      w: partFrame.w ?? 20,
      h: partFrame.h ?? 20,
    };
    const partFramePx = hostRelativeFrameToPageBottomLeftPx(
      partFrameFull,
      block.frame,
      slideDesign,
    );

    const setPartFrameKey = (key: "x" | "y" | "w" | "h", rawPx: number) => {
      const nextPct = patchHostRelativeFramePageBottomLeftPx(
        partFrameFull,
        block.frame,
        key,
        rawPx,
        slideDesign,
      );
      const nextFrame = clampKpiPartFrame(nextPct);
      let nextParts = upsertKpiPartState(block.kpiParts, kpiPartTarget, { frame: nextFrame });
      if (key === "w" || key === "h") {
        nextParts = scaleKpiPartTypographyOnResize(
          nextParts,
          kpiPartTarget,
          partFrameFull,
          { w: nextFrame.w ?? partFrameFull.w, h: nextFrame.h ?? partFrameFull.h },
        );
      }
      updateSelected({
        kpiParts: mergeKpiPartsWithOptions(nextParts, partsToKpiOptions(nextParts)),
      } as Partial<ComunicadoBlock>);
    };

    const setPartRadius = (raw: number) => {
      const nextParts = upsertKpiPartState(block.kpiParts, kpiPartTarget, {
        style: { borderRadius: Math.max(0, Math.min(64, Number(raw) || 0)) },
      });
      updateSelected({
        kpiParts: mergeKpiPartsWithOptions(nextParts, partsToKpiOptions(nextParts)),
      } as Partial<ComunicadoBlock>);
    };

    const enableFreePosition = () => {
      const nextParts = seedKpiPartsFreeLayoutFrames(block.kpiParts);
      updateSelected({
        kpiParts: mergeKpiPartsWithOptions(nextParts, partsToKpiOptions(nextParts)),
      } as Partial<ComunicadoBlock>);
    };

    return (
      <DeckRibbonGroup
        label="Posição e tamanho"
        hint="Posição absoluta na página (px de design), origem no canto inferior esquerdo."
      >
        {!explicitFrame ? (
          <button type="button" className="td-btn td-btn--sm" onClick={enableFreePosition}>
            Posicionar livremente…
          </button>
        ) : (
          <div className="td-deck-ribbon__frame-grid">
            {frameKeys.map((key) => (
              <DeckRangeField
                key={key}
                id={`td-ribbon-kpi-part-frame-${key}`}
                label={FRAME_LABELS[key]}
                hint={FRAME_HINTS[key]}
                min={key === "w" || key === "h" ? 1 : 0}
                max={key === "x" || key === "w" ? slideDesign.width : slideDesign.height}
                step={1}
                value={formatDesignPx(partFramePx[key] ?? 0)}
                displayValue={String(formatDesignPx(partFramePx[key] ?? 0))}
                aria-label={FRAME_LABELS[key]}
                onChange={(value) => setPartFrameKey(key, value)}
              />
            ))}
            <DeckRangeField
              id="td-ribbon-kpi-part-frame-radius"
              label="Raio px"
              hint={H.borderRadius}
              min={0}
              max={64}
              step={1}
              value={borderRadius}
              aria-label="Raio dos cantos em pixels"
              onChange={(value) => setPartRadius(value)}
            />
          </div>
        )}
      </DeckRibbonGroup>
    );
  }

  const chartPartTarget =
    selected.type === "chart_view" && selectedChartPart && chartPartAllowsFrame(selectedChartPart)
      ? selectedChartPart
      : null;

  if (chartPartTarget && selected.type === "chart_view") {
    const block = selected as ComunicadoChartViewBlock;
    const partState = getChartPartState(block.chartParts, chartPartTarget);
    const defaults = defaultChartPartFrame(chartPartTarget);
    const partFrame = clampChartPartFrame(partState?.frame ?? defaults);
    const frameKeys = [...POSITION_KEYS, ...SIZE_KEYS] as const;
    const partFrameForPx: ComunicadoFrame = {
      x: partFrame.x,
      y: partFrame.y,
      w: partFrame.w ?? defaults.w ?? 20,
      h: partFrame.h ?? defaults.h ?? 20,
    };
    const partFramePx = hostRelativeFrameToPageBottomLeftPx(
      partFrameForPx,
      block.frame,
      slideDesign,
    );

    const setPartFrameKey = (key: "x" | "y" | "w" | "h", rawPx: number) => {
      const nextPct = patchHostRelativeFramePageBottomLeftPx(
        partFrameForPx,
        block.frame,
        key,
        rawPx,
        slideDesign,
      );
      const nextFrame = clampChartPartFrame({
        ...partFrame,
        ...nextPct,
        w: nextPct.w ?? partFrame.w ?? defaults.w,
        h: nextPct.h ?? partFrame.h ?? defaults.h,
      });
      let nextParts = upsertChartPartState(block.chartParts, chartPartTarget, {
        frame: nextFrame,
      });
      if (key === "w" || key === "h") {
        nextParts = scaleChartPartTypographyOnResize(
          nextParts,
          chartPartTarget,
          partFrameForPx,
          { w: nextFrame.w ?? partFrameForPx.w, h: nextFrame.h ?? partFrameForPx.h },
        );
      }
      updateSelected({
        chartParts: mergeChartPartsWithOptions(nextParts, partsToChartOptions(nextParts)),
      } as Partial<ComunicadoBlock>);
    };

    return (
      <DeckRibbonGroup label="Posição e tamanho" hint={E.position ?? H.shapeSize}>
        <div className="td-deck-ribbon__frame-grid">
          {frameKeys.map((key) => (
            <DeckRangeField
              key={key}
              id={`td-ribbon-chart-part-frame-${key}`}
              label={FRAME_LABELS[key]}
              hint={FRAME_HINTS[key]}
              min={key === "w" || key === "h" ? 1 : 0}
              max={key === "x" || key === "w" ? slideDesign.width : slideDesign.height}
              step={1}
              value={formatDesignPx(partFramePx[key] ?? 0)}
              displayValue={String(formatDesignPx(partFramePx[key] ?? 0))}
              aria-label={FRAME_LABELS[key]}
              onChange={(value) => setPartFrameKey(key, value)}
            />
          ))}
        </div>
      </DeckRibbonGroup>
    );
  }

  const pointOnly =
    selected.type === "shape" && isPointShapeKind(selected.shape);
  const frameKeys = pointOnly
    ? POSITION_KEYS
    : ([...POSITION_KEYS, ...SIZE_KEYS] as const);

  const innerChrome = blockUsesInnerShapeChrome(selected)
    ? resolveBlockShapeChromeStyle(selected)
    : null;
  const borderRadius = innerChrome?.borderRadius ?? selected.style?.borderRadius ?? 0;
  const showCornerRadius = !pointOnly && selected.type !== "chart_view";

  const framePx = framePercentToPageBottomLeftPx(selected.frame, slideDesign);

  const setFrameKey = (key: "x" | "y" | "w" | "h", rawPx: number) => {
    const nextFrame = patchComunicadoFramePageBottomLeftPx(
      selected.frame,
      key,
      rawPx,
      slideDesign,
    );
    if (
      (key === "w" || key === "h") &&
      (selected.type === "kpi_view" ||
        selected.type === "chart_view" ||
        selected.type === "table_view")
    ) {
      const scaled = scaleComplexBlockOnResize(
        { ...selected, frame: nextFrame },
        selected.frame,
        nextFrame,
      );
      updateSelected({
        frame: nextFrame,
        ...(scaled.type === "kpi_view" ? { kpiParts: scaled.kpiParts } : {}),
        ...(scaled.type === "chart_view" ? { chartParts: scaled.chartParts } : {}),
        ...(scaled.type === "table_view" ? { tableOptions: scaled.tableOptions } : {}),
      } as Partial<ComunicadoBlock>);
      return;
    }
    updateSelected({ frame: nextFrame } as Partial<ComunicadoBlock>);
  };

  const axisMax = (key: "x" | "y" | "w" | "h", design: ViewportPixelSize) =>
    key === "x" || key === "w" ? design.width : design.height;

  return (
    <DeckRibbonGroup label="Posição e tamanho" hint={E.position ?? H.shapeSize}>
      <div className="td-deck-ribbon__frame-grid">
        {frameKeys.map((key) => (
          <DeckRangeField
            key={key}
            id={`td-ribbon-frame-${key}`}
            label={FRAME_LABELS[key]}
            hint={FRAME_HINTS[key]}
            min={key === "w" || key === "h" ? 1 : 0}
            max={axisMax(key, slideDesign)}
            step={1}
            value={formatDesignPx(framePx[key])}
            displayValue={String(formatDesignPx(framePx[key]))}
            aria-label={FRAME_LABELS[key]}
            onChange={(value) => setFrameKey(key, value)}
          />
        ))}
        <DeckRangeField
          id="td-ribbon-frame-rotation"
          label="Rot. °"
          hint={H.frameRotation}
          min={-180}
          max={180}
          step={1}
          value={selected.style?.rotation ?? 0}
          aria-label="Rotação em graus"
          onChange={(value) =>
            updateSelectedStyle({
              rotation: Math.max(-180, Math.min(180, value)),
            })
          }
        />
        {showCornerRadius ? (
          <DeckRangeField
            id="td-ribbon-frame-radius"
            label="Raio px"
            hint={H.borderRadius}
            min={0}
            max={64}
            step={1}
            value={borderRadius}
            aria-label="Raio dos cantos em pixels"
            onChange={(value) =>
              updateSelectedStyle({
                borderRadius: Math.max(0, Math.min(64, value)),
              })
            }
          />
        ) : null}
      </div>
    </DeckRibbonGroup>
  );
}
