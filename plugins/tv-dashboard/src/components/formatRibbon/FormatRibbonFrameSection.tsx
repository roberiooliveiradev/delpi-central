import { FieldLabel, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  blockUsesInnerShapeChrome,
  chartPartAllowsFrame,
  clampChartPartFrame,
  clampKpiPartFrame,
  defaultChartPartFrame,
  defaultKpiPartFrame,
  getChartPartState,
  getKpiPartState,
  isPointShapeKind,
  kpiPartAllowsFrame,
  mergeChartPartsWithOptions,
  mergeKpiPartsWithOptions,
  partsToChartOptions,
  partsToKpiOptions,
  resolveBlockShapeChromeStyle,
  upsertChartPartState,
  upsertKpiPartState,
  type ComunicadoBlock,
  type ComunicadoChartViewBlock,
  type ComunicadoFrame,
  type ComunicadoKpiViewBlock,
  type KpiFramePartKind,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { useComunicadoEditor } from "../comunicadoEditorContext";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

const SIZE_KEYS = ["w", "h"] as const;
const POSITION_KEYS = ["x", "y"] as const;

const FRAME_LABELS: Record<"x" | "y" | "w" | "h", string> = {
  x: "X %",
  y: "Y %",
  w: "Larg. %",
  h: "Alt. %",
};

const FRAME_HINTS: Record<"x" | "y" | "w" | "h", string> = {
  x: H.frameX,
  y: H.frameY,
  w: H.frameW,
  h: H.frameH,
};

function formatFrameValue(value: number): number {
  return Number((Number.isFinite(value) ? value : 0).toFixed(1));
}

/** Ajusta eixo do frame mantendo o bloco dentro do palco (0–100%). */
export function patchComunicadoFrame(
  frame: ComunicadoFrame,
  key: keyof ComunicadoFrame,
  raw: number,
): ComunicadoFrame {
  const value = Number.isFinite(raw) ? raw : frame[key];
  if (key === "w" || key === "h") {
    const size = Math.max(0.5, Math.min(100, value));
    const next = { ...frame, [key]: size };
    if (key === "w") {
      next.x = Math.max(0, Math.min(100 - size, frame.x));
    } else {
      next.y = Math.max(0, Math.min(100 - size, frame.y));
    }
    return next;
  }
  const max = key === "x" ? 100 - frame.w : 100 - frame.h;
  return { ...frame, [key]: Math.max(0, Math.min(max, value)) };
}

/**
 * Posição / tamanho / rotação / raio — bloco no palco ou parte do KPI/gráfico
 * (title/value/hint/icon ou title/legend/plotArea), espelhando o inspetor.
 */
export function FormatRibbonFrameSection() {
  const {
    selected,
    selectedIds,
    selectedKpiPart,
    selectedChartPart,
    updateSelected,
    updateSelectedStyle,
  } = useComunicadoEditor();

  if (!selected || selectedIds.length > 1) return null;

  const kpiPartTarget =
    selected.type === "kpi_view" && selectedKpiPart && kpiPartAllowsFrame(selectedKpiPart)
      ? selectedKpiPart
      : null;

  if (kpiPartTarget && selected.type === "kpi_view") {
    const block = selected as ComunicadoKpiViewBlock;
    const partState = getKpiPartState(block.kpiParts, kpiPartTarget);
    const frameKind = kpiPartTarget.kind as KpiFramePartKind;
    const partFrame = clampKpiPartFrame(
      partState?.frame ?? defaultKpiPartFrame(frameKind),
    );
    const borderRadius = partState?.style?.borderRadius ?? 0;
    const frameKeys = [...POSITION_KEYS, ...SIZE_KEYS] as const;

    const setPartFrameKey = (key: "x" | "y" | "w" | "h", raw: number) => {
      const nextFrame = clampKpiPartFrame({
        ...partFrame,
        [key]: Number.isFinite(raw) ? raw : partFrame[key],
      });
      const nextParts = upsertKpiPartState(block.kpiParts, kpiPartTarget, { frame: nextFrame });
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

    return (
      <DeckRibbonGroup label="Posição e tamanho" hint={E.position ?? H.shapeSize}>
        <div className="td-deck-ribbon__frame-grid">
          {frameKeys.map((key) => (
            <span key={key} className="td-deck-ribbon__frame-field">
              <FieldLabel
                htmlFor={`td-ribbon-kpi-part-frame-${key}`}
                label={FRAME_LABELS[key]}
                hint={FRAME_HINTS[key]}
                className="td-deck-ribbon__field-label"
              />
              <NativeTextControl
                id={`td-ribbon-kpi-part-frame-${key}`}
                type="number"
                className="td-deck-ribbon__number td-deck-ribbon__number--compact"
                min={key === "w" || key === "h" ? 4 : 0}
                max={key === "w" || key === "h" ? 96 : 100}
                step={0.5}
                aria-label={FRAME_LABELS[key]}
                value={formatFrameValue(partFrame[key] ?? 0)}
                onChange={(value) => setPartFrameKey(key, Number(value))}
              />
            </span>
          ))}
          <span className="td-deck-ribbon__frame-field">
            <FieldLabel
              htmlFor="td-ribbon-kpi-part-frame-radius"
              label="Raio px"
              hint={H.borderRadius}
              className="td-deck-ribbon__field-label"
            />
            <NativeTextControl
              id="td-ribbon-kpi-part-frame-radius"
              type="number"
              className="td-deck-ribbon__number td-deck-ribbon__number--compact"
              min={0}
              max={64}
              step={1}
              aria-label="Raio dos cantos em pixels"
              value={borderRadius}
              onChange={(value) => setPartRadius(Number(value))}
            />
          </span>
        </div>
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

    const setPartFrameKey = (key: "x" | "y" | "w" | "h", raw: number) => {
      const nextFrame = clampChartPartFrame({
        ...partFrame,
        w: partFrame.w ?? defaults.w,
        h: partFrame.h ?? defaults.h,
        [key]: Number.isFinite(raw) ? raw : (partFrame[key] ?? defaults[key] ?? 0),
      });
      const nextParts = upsertChartPartState(block.chartParts, chartPartTarget, {
        frame: nextFrame,
      });
      updateSelected({
        chartParts: mergeChartPartsWithOptions(nextParts, partsToChartOptions(nextParts)),
      } as Partial<ComunicadoBlock>);
    };

    return (
      <DeckRibbonGroup label="Posição e tamanho" hint={E.position ?? H.shapeSize}>
        <div className="td-deck-ribbon__frame-grid">
          {frameKeys.map((key) => (
            <span key={key} className="td-deck-ribbon__frame-field">
              <FieldLabel
                htmlFor={`td-ribbon-chart-part-frame-${key}`}
                label={FRAME_LABELS[key]}
                hint={FRAME_HINTS[key]}
                className="td-deck-ribbon__field-label"
              />
              <NativeTextControl
                id={`td-ribbon-chart-part-frame-${key}`}
                type="number"
                className="td-deck-ribbon__number td-deck-ribbon__number--compact"
                min={key === "w" || key === "h" ? 5 : 0}
                max={100}
                step={0.5}
                aria-label={FRAME_LABELS[key]}
                value={formatFrameValue(partFrame[key] ?? defaults[key] ?? 0)}
                onChange={(value) => setPartFrameKey(key, Number(value))}
              />
            </span>
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
  const showCornerRadius =
    !pointOnly &&
    !(selected.type === "kpi_view" && selectedKpiPart == null);

  const setFrameKey = (key: "x" | "y" | "w" | "h", raw: number) => {
    updateSelected({
      frame: patchComunicadoFrame(selected.frame, key, raw),
    } as Partial<ComunicadoBlock>);
  };

  return (
    <DeckRibbonGroup label="Posição e tamanho" hint={E.position ?? H.shapeSize}>
      <div className="td-deck-ribbon__frame-grid">
        {frameKeys.map((key) => (
          <span key={key} className="td-deck-ribbon__frame-field">
            <FieldLabel
              htmlFor={`td-ribbon-frame-${key}`}
              label={FRAME_LABELS[key]}
              hint={FRAME_HINTS[key]}
              className="td-deck-ribbon__field-label"
            />
            <NativeTextControl
              id={`td-ribbon-frame-${key}`}
              type="number"
              className="td-deck-ribbon__number td-deck-ribbon__number--compact"
              min={key === "w" || key === "h" ? 0.5 : 0}
              max={100}
              step={0.5}
              aria-label={FRAME_LABELS[key]}
              value={formatFrameValue(selected.frame[key])}
              onChange={(value) => setFrameKey(key, Number(value))}
            />
          </span>
        ))}
        <span className="td-deck-ribbon__frame-field">
          <FieldLabel
            htmlFor="td-ribbon-frame-rotation"
            label="Rot. °"
            hint={H.frameRotation}
            className="td-deck-ribbon__field-label"
          />
          <NativeTextControl
            id="td-ribbon-frame-rotation"
            type="number"
            className="td-deck-ribbon__number td-deck-ribbon__number--compact"
            min={-180}
            max={180}
            step={1}
            aria-label="Rotação em graus"
            value={selected.style?.rotation ?? 0}
            onChange={(value) =>
              updateSelectedStyle({
                rotation: Math.max(-180, Math.min(180, Number(value) || 0)),
              })
            }
          />
        </span>
        {showCornerRadius ? (
          <span className="td-deck-ribbon__frame-field">
            <FieldLabel
              htmlFor="td-ribbon-frame-radius"
              label="Raio px"
              hint={H.borderRadius}
              className="td-deck-ribbon__field-label"
            />
            <NativeTextControl
              id="td-ribbon-frame-radius"
              type="number"
              className="td-deck-ribbon__number td-deck-ribbon__number--compact"
              min={0}
              max={64}
              step={1}
              aria-label="Raio dos cantos em pixels"
              value={borderRadius}
              onChange={(value) =>
                updateSelectedStyle({
                  borderRadius: Math.max(0, Math.min(64, Number(value) || 0)),
                })
              }
            />
          </span>
        ) : null}
      </div>
    </DeckRibbonGroup>
  );
}
