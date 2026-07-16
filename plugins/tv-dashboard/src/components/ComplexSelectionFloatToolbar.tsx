import { useEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { Filter, Paintbrush, Plus } from "lucide-react";
import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import type { ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import {
  complexFrameShortSidePx,
  resolveComplexFloatToolbarMetrics,
} from "../utils/complexFloatToolbarSize";
import { resolveViewportPixelSize } from "../utils/viewportPixelSize";
import { useComunicadoEditor } from "./comunicadoEditorContext";

export type ComplexFloatPanel = "elements" | "style" | "data" | null;

export type ComplexFloatToolbarLabels = {
  elements: string;
  style: string;
  data: string;
};

type Props = {
  blockId: string;
  frame: ComunicadoFrame;
  labels: ComplexFloatToolbarLabels;
  /** Conteúdo do painel `+` (estrutura / parts). */
  renderElements: (close: () => void) => ReactNode;
  /** Conteúdo do painel pincel (aparência). */
  renderStyle: (close: () => void) => ReactNode;
  /** Conteúdo do painel funil (dados / projeção). */
  renderData: (close: () => void) => ReactNode;
  elementsPopoverClassName?: string;
  stylePopoverClassName?: string;
  dataPopoverClassName?: string;
};

/**
 * Shell da coluna flutuante (+ / pincel / funil) — compartilhado por chart/kpi/table.
 * Contratos: + = estrutura visual; pincel = aparência; funil = dados.
 */
export function ComplexSelectionFloatToolbar({
  blockId,
  frame,
  labels,
  renderElements,
  renderStyle,
  renderData,
  elementsPopoverClassName = "td-chart-float__popover td-chart-float__popover--cascade",
  stylePopoverClassName = "td-chart-float__popover td-chart-float__popover--style",
  dataPopoverClassName = "td-chart-float__popover td-chart-float__popover--actions",
}: Props) {
  const { viewportProfile } = useComunicadoEditor();
  const [panel, setPanel] = useState<ComplexFloatPanel>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const elementsBtnRef = useRef<HTMLButtonElement>(null);
  const styleBtnRef = useRef<HTMLButtonElement>(null);
  const dataBtnRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  const floatMetrics = useMemo(() => {
    const designSize = resolveViewportPixelSize(viewportProfile);
    const shortSide = complexFrameShortSidePx(frame, designSize);
    return resolveComplexFloatToolbarMetrics(shortSide);
  }, [frame.h, frame.w, viewportProfile]);

  const floatStyle = useMemo(
    (): CSSProperties =>
      ({
        "--td-float-btn-size": `${floatMetrics.btnSize}px`,
        "--td-float-gap": `${floatMetrics.gap}px`,
        "--td-float-offset": `${floatMetrics.offset}px`,
        "--td-float-radius": `${floatMetrics.radius}px`,
      }) as CSSProperties,
    [floatMetrics],
  );

  useEffect(() => {
    setPanel(null);
  }, [blockId]);

  useEffect(() => {
    if (!panel) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setPanel(null);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [panel]);

  const close = () => setPanel(null);
  const iconSize = floatMetrics.iconSize;
  const activeAnchorRef =
    panel === "elements" ? elementsBtnRef : panel === "style" ? styleBtnRef : dataBtnRef;

  return (
    <div
      className="td-chart-float td-complex-float"
      ref={rootRef}
      style={floatStyle}
      onPointerDown={(event) => event.stopPropagation()}
    >
      <button
        ref={elementsBtnRef}
        type="button"
        className={[
          "td-chart-float__btn",
          panel === "elements" ? "td-chart-float__btn--active" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label={labels.elements}
        aria-expanded={panel === "elements"}
        onClick={() => setPanel((prev) => (prev === "elements" ? null : "elements"))}
      >
        <Plus size={iconSize} aria-hidden="true" strokeWidth={2.25} />
      </button>
      <button
        ref={styleBtnRef}
        type="button"
        className={[
          "td-chart-float__btn",
          panel === "style" ? "td-chart-float__btn--active" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label={labels.style}
        aria-expanded={panel === "style"}
        onClick={() => setPanel((prev) => (prev === "style" ? null : "style"))}
      >
        <Paintbrush size={iconSize} aria-hidden="true" strokeWidth={2.25} />
      </button>
      <button
        ref={dataBtnRef}
        type="button"
        className={[
          "td-chart-float__btn",
          panel === "data" ? "td-chart-float__btn--active" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label={labels.data}
        aria-expanded={panel === "data"}
        onClick={() => setPanel((prev) => (prev === "data" ? null : "data"))}
      >
        <Filter size={iconSize} aria-hidden="true" strokeWidth={2.25} />
      </button>

      {panel === "elements" ? (
        <AnchoredPanelPortal
          open
          anchorRef={activeAnchorRef}
          panelRef={popoverRef}
          variant="bare"
          preferredPlacement="right"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          className="td-chart-float__portal"
          role="menu"
          onDismiss={close}
        >
          <div className={elementsPopoverClassName}>{renderElements(close)}</div>
        </AnchoredPanelPortal>
      ) : null}

      {panel === "style" ? (
        <AnchoredPanelPortal
          open
          anchorRef={activeAnchorRef}
          panelRef={popoverRef}
          variant="bare"
          preferredPlacement="right"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          className="td-chart-float__portal"
          role="menu"
          aria-label={labels.style}
          onDismiss={close}
        >
          <div className={stylePopoverClassName}>{renderStyle(close)}</div>
        </AnchoredPanelPortal>
      ) : null}

      {panel === "data" ? (
        <AnchoredPanelPortal
          open
          anchorRef={activeAnchorRef}
          panelRef={popoverRef}
          variant="bare"
          preferredPlacement="right"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          className="td-chart-float__portal"
          role="menu"
          aria-label={labels.data}
          onDismiss={close}
        >
          <div className={dataPopoverClassName}>{renderData(close)}</div>
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
