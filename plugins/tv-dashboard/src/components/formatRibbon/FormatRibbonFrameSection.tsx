import { Move } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode, type RefObject } from "react";
import {
  blockUsesInnerShapeChrome,
  chartPartAllowsFrame,
  clampChartPartFrame,
  clampInputPartFrame,
  clampKpiPartFrame,
  defaultChartPartFrame,
  defaultInputPartFrame,
  defaultKpiPartFrame,
  formatDesignPx,
  framePercentToPageBottomLeftPx,
  getChartPartState,
  getInputPartState,
  getKpiPartState,
  hostRelativeFrameToPageBottomLeftPx,
  resolveInputPartFrame,
  resolveKpiPartFrame,
  isPointShapeKind,
  inputPartAllowsFrame,
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
  scaleInputPartTypographyOnResize,
  scaleKpiPartTypographyOnResize,
  seedKpiPartsFreeLayoutFrames,
  upsertChartPartState,
  upsertInputPartState,
  upsertKpiPartState,
  type ComunicadoBlock,
  type ComunicadoChartViewBlock,
  type ComunicadoFrame,
  type ComunicadoInputBlock,
  type ComunicadoKpiViewBlock,
  type KpiFramePartKind,
  type ViewportPixelSize,
} from "@delpi/tv-dashboard-presentation";
import { AnchoredPanelPortal, HintAction } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";
import { enableInputFreeLayoutFromDom } from "../../utils/enableInputFreeLayoutFromDom";
import {
  DeckRangeField,
  type DeckRangeFieldProps,
} from "../deck/DeckRangeField";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { useComunicadoEditor } from "../comunicadoEditorContext";

type FrameFieldDensity = NonNullable<DeckRangeFieldProps["density"]>;

function FrameRangeField({
  density,
  ...props
}: DeckRangeFieldProps & { density: FrameFieldDensity }) {
  return <DeckRangeField density={density} {...props} />;
}

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;
const POSITION_GROUP_HINT =
  E.position ??
  "Posição e tamanho em pixels de design da página, com origem no canto inferior esquerdo.";

function useCloseOnOutside(
  refs: Array<RefObject<HTMLElement | null>>,
  active: boolean,
  onOutside: () => void,
) {
  useEffect(() => {
    if (!active) return;
    const handlePointerDown = (event: MouseEvent | TouchEvent) => {
      const target = event.target as Node | null;
      if (!target) return;
      if (refs.some((ref) => ref.current?.contains(target))) return;
      if (
        target instanceof Element &&
        target.closest(
          '[aria-modal="true"], .delpi-ui-shape-menu__panel, .delpi-ui-color-picker, .delpi-ui-select__panel, .delpi-ui-shape-dialog, .delpi-ui-help-tooltip',
        )
      ) {
        return;
      }
      onOutside();
    };
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("touchstart", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("touchstart", handlePointerDown);
    };
  }, [active, onOutside, refs]);
}

type FrameSizeGroupProps = {
  embed: boolean;
  captionPlacement: "below" | "none";
  hint?: string;
  /** Ação fora do painel (ex.: «Posicionar livremente…») — ribbon e painel sem popover. */
  emptyAction?: ReactNode;
  children: ReactNode;
};

/**
 * Ribbon: tile «Posição» + grade no popover ancorado.
 * Embed (sidebar): grade embutida na seção do accordion.
 */
function FrameSizeGroup({
  embed,
  captionPlacement,
  hint = POSITION_GROUP_HINT,
  emptyAction,
  children,
}: FrameSizeGroupProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  useCloseOnOutside([rootRef, panelRef], open, () => setOpen(false));

  if (embed || emptyAction) {
    return (
      <DeckRibbonGroup
        label="Posição e tamanho"
        hint={hint}
        captionPlacement={captionPlacement}
      >
        {emptyAction ?? children}
      </DeckRibbonGroup>
    );
  }

  return (
    <DeckRibbonGroup
      label="Posição e tamanho"
      hint={hint}
      captionPlacement={captionPlacement}
    >
      <div
        ref={rootRef}
        className="td-frame-size-entry delpi-ui-shape-menu td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus"
      >
        <HintAction hint={hint} ariaLabel="Ajuda: Posição e tamanho">
          <button
            type="button"
            className={[
              "delpi-ui-shape-menu__trigger",
              open ? "td-frame-size-entry__trigger--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            aria-label="Posição e tamanho"
            aria-haspopup="dialog"
            aria-expanded={open}
            onClick={() => setOpen((prev) => !prev)}
          >
            <span className="delpi-ui-shape-menu__trigger-icon" aria-hidden="true">
              <Move size={18} />
            </span>
            <span className="delpi-ui-shape-menu__trigger-label">Posição</span>
          </button>
        </HintAction>
        {open ? (
          <AnchoredPanelPortal
            open={open}
            anchorRef={rootRef}
            panelRef={panelRef}
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            className="td-frame-size-popover"
            role="dialog"
            aria-label="Posição e tamanho"
            preferredPlacement="bottom"
          >
            {children}
          </AnchoredPanelPortal>
        ) : null}
      </div>
    </DeckRibbonGroup>
  );
}

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
 * Ribbon: tile + grade no popover ancorado; sidebar (`embed`): grade embutida.
 * `density=full` (padrão): slider + input; `density=compact`: só inputs.
 */
export function FormatRibbonFrameSection({
  density = "full",
  embed = false,
}: {
  density?: FrameFieldDensity;
  /** Painel: omite caption do ribbon (accordion já titulou). */
  embed?: boolean;
} = {}) {
  const captionPlacement = embed ? ("none" as const) : ("below" as const);
  const {
    selected,
    selectedIds,
    selectedKpiPart,
    selectedChartPart,
    selectedInputPart,
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

  const inputPartTarget =
    selected.type === "input" && selectedInputPart && inputPartAllowsFrame(selectedInputPart)
      ? selectedInputPart
      : null;

  if (inputPartTarget && selected.type === "input") {
    const block = selected as ComunicadoInputBlock;
    const partState = getInputPartState(block.inputParts, inputPartTarget);
    const explicitFrame = resolveInputPartFrame(partState);
    const partFrame = clampInputPartFrame(
      explicitFrame ?? defaultInputPartFrame(inputPartTarget.kind),
    );
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
      const nextFrame = clampInputPartFrame(nextPct);
      let nextParts = upsertInputPartState(block.inputParts, inputPartTarget, {
        frame: nextFrame,
      });
      if (key === "w" || key === "h") {
        nextParts = scaleInputPartTypographyOnResize(
          nextParts,
          inputPartTarget,
          partFrameFull,
          { w: nextFrame.w ?? partFrameFull.w, h: nextFrame.h ?? partFrameFull.h },
        );
      }
      updateSelected({ inputParts: nextParts } as Partial<ComunicadoBlock>);
    };

    const setPartRadius = (raw: number) => {
      const nextParts = upsertInputPartState(block.inputParts, inputPartTarget, {
        style: { borderRadius: Math.max(0, Math.min(64, Number(raw) || 0)) },
      });
      updateSelected({ inputParts: nextParts } as Partial<ComunicadoBlock>);
    };

    const enableFreePosition = () => {
      enableInputFreeLayoutFromDom(block.id, block.inputParts, (next) => {
        updateSelected({ inputParts: next } as Partial<ComunicadoBlock>);
      });
    };

    return (
      <FrameSizeGroup
        embed={embed}
        captionPlacement={captionPlacement}
        emptyAction={
          !explicitFrame ? (
            <button type="button" className="td-btn td-btn--sm" onClick={enableFreePosition}>
              Posicionar livremente…
            </button>
          ) : undefined
        }
      >
        <div className="td-deck-ribbon__frame-grid">
          {frameKeys.map((key) => (
            <FrameRangeField
              density={density}
              key={key}
              id={`td-ribbon-input-part-frame-${key}`}
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
          <FrameRangeField
            density={density}
            id="td-ribbon-input-part-frame-radius"
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
      </FrameSizeGroup>
    );
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
      <FrameSizeGroup
        embed={embed}
        captionPlacement={captionPlacement}
        emptyAction={
          !explicitFrame ? (
            <button type="button" className="td-btn td-btn--sm" onClick={enableFreePosition}>
              Posicionar livremente…
            </button>
          ) : undefined
        }
      >
        <div className="td-deck-ribbon__frame-grid">
          {frameKeys.map((key) => (
            <FrameRangeField
              density={density}
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
          <FrameRangeField
            density={density}
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
      </FrameSizeGroup>
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
      <FrameSizeGroup embed={embed} captionPlacement={captionPlacement}>
        <div className="td-deck-ribbon__frame-grid">
          {frameKeys.map((key) => (
            <FrameRangeField
              density={density}
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
      </FrameSizeGroup>
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
    <FrameSizeGroup embed={embed} captionPlacement={captionPlacement}>
      <div className="td-deck-ribbon__frame-grid">
        {frameKeys.map((key) => (
          <FrameRangeField
            density={density}
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
        <FrameRangeField
          density={density}
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
          <FrameRangeField
            density={density}
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
    </FrameSizeGroup>
  );
}
