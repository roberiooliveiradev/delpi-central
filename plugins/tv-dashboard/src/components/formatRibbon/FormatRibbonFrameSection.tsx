import { Move } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";
import {
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
import { FormatRibbonOpacityFields } from "./FormatRibbonOrganizeSection";

type FrameFieldDensity = NonNullable<DeckRangeFieldProps["density"]>;

function FrameRangeField({
  density,
  ...props
}: DeckRangeFieldProps & { density: FrameFieldDensity }) {
  return <DeckRangeField density={density} {...props} />;
}

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const SIZE_POSITION_GROUP_HINT =
  H.sizePosition ??
  "Posição, tamanho e rotação em pixels de design da página (origem no canto inferior esquerdo).";

type FrameSizeGroupProps = {
  embed: boolean;
  captionPlacement: "below" | "none";
  hint?: string;
  /** Ação fora do painel (ex.: «Posicionar livremente…») — ribbon e painel sem popover. */
  emptyAction?: ReactNode;
  /** Quando false, só geometria. Padrão false — opacidade fica na seção Forma. */
  includeOpacity?: boolean;
  children?: ReactNode;
};

/**
 * Ribbon: tile «Posição» + grade (posição/tamanho/rotação) no popover.
 * Embed (sidebar): campos embutidos na seção do accordion.
 */
function FrameSizeGroup({
  embed,
  captionPlacement,
  hint = SIZE_POSITION_GROUP_HINT,
  emptyAction,
  includeOpacity = false,
  children,
}: FrameSizeGroupProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const opacityFields = includeOpacity ? (
    <FormatRibbonOpacityFields className="td-deck-ribbon__organize-props td-frame-size-popover__opacity" />
  ) : null;

  const body = emptyAction ? (
    <>
      {emptyAction}
      {opacityFields}
    </>
  ) : (
    <>
      {children}
      {opacityFields}
    </>
  );

  if (embed || emptyAction) {
    return (
      <DeckRibbonGroup label="Tamanho e posição" hint={hint} captionPlacement={captionPlacement}>
        {body}
      </DeckRibbonGroup>
    );
  }

  return (
    <DeckRibbonGroup label="Tamanho e posição" hint={hint} captionPlacement={captionPlacement}>
      <div
        ref={rootRef}
        className="td-frame-size-entry delpi-ui-shape-menu td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus"
      >
        <HintAction hint={hint} ariaLabel="Ajuda: Tamanho e posição">
          <button
            ref={triggerRef}
            type="button"
            className={[
              "delpi-ui-shape-menu__trigger",
              open ? "td-frame-size-entry__trigger--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            aria-label="Tamanho e posição"
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
            anchorRef={triggerRef}
            panelRef={panelRef}
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            className="td-frame-size-popover"
            role="dialog"
            aria-label="Tamanho e posição"
            preferredPlacement="bottom"
            allowFlip={false}
            gap={10}
            density="compact"
            onDismiss={() => setOpen(false)}
          >
            {body}
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
 * Tamanho e posição: X/Y / largura / altura / rotação — bloco no palco ou
 * parte do KPI/gráfico. UI em px de design; modelo permanece em %.
 * Ribbon: tile + grade no popover; sidebar (`embed`): grade embutida.
 * Opacidade e raio ficam na seção Forma.
 */
export function FormatRibbonFrameSection({
  density = "full",
  embed = false,
  includeOpacity = false,
}: {
  density?: FrameFieldDensity;
  /** Painel: omite caption do ribbon (accordion já titulou). */
  embed?: boolean;
  /**
   * @deprecated Opacidade/ajuste ficam em `AppearanceSection` (Exibição).
   * Mantido só para hosts legados — preferir sempre false.
   */
  includeOpacity?: boolean;
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

  /* Parte de gráfico sem geometria própria — só opacidade no grupo Exibição. */
  if (
    selected.type === "chart_view" &&
    selectedChartPart &&
    !chartPartAllowsFrame(selectedChartPart)
  ) {
    if (!includeOpacity) return null;
    return (
      <FrameSizeGroup embed={embed} captionPlacement={captionPlacement} includeOpacity />
    );
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

    const enableFreePosition = () => {
      enableInputFreeLayoutFromDom(block.id, block.inputParts, (next) => {
        updateSelected({ inputParts: next } as Partial<ComunicadoBlock>);
      });
    };

    return (
      <FrameSizeGroup
        embed={embed}
        captionPlacement={captionPlacement}
        includeOpacity={includeOpacity}
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
        includeOpacity={includeOpacity}
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
      <FrameSizeGroup
        embed={embed}
        captionPlacement={captionPlacement}
        includeOpacity={includeOpacity}
      >
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
    <FrameSizeGroup
      embed={embed}
      captionPlacement={captionPlacement}
      includeOpacity={includeOpacity}
    >
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
      </div>
    </FrameSizeGroup>
  );
}
