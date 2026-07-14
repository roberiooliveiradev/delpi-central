import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { Filter, Paintbrush, Plus } from "lucide-react";
import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import {
  applyChartAddElementChoiceWithParts,
  applyChartElementVisibility,
  chartElementPrimaryPartRef,
  isChartElementEnabled,
  mergeChartPartsWithOptions,
  mergeComunicadoChartOptions,
  partsToChartOptions,
  toSeriesChartKind,
  type ChartAddElementChoiceId,
  type ChartElementId,
  type ComunicadoBlock,
  type ComunicadoChartOptions,
  type ComunicadoChartViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import {
  chartFrameShortSidePx,
  resolveChartFloatToolbarMetrics,
} from "../utils/chartFloatToolbarSize";
import { resolveViewportPixelSize } from "../utils/viewportPixelSize";
import { ChartAddElementMenu } from "./ChartAddElementMenu";
import { ChartColorsStylesMenu } from "./ChartColorsStylesMenu";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  block: ComunicadoChartViewBlock;
};

type FloatPanel = "elements" | "style" | "data" | null;

/**
 * Coluna flutuante à direita do bbox do gráfico (+ / pincel / funil).
 * `+` e pincel reutilizam os mesmos menus da ribbon.
 * Botões escalam com o lado curto do gráfico (design px).
 * Menus ancoram no botão ativo e preferem abrir ao lado quando há espaço.
 */
export function ChartSelectionFloatToolbar({ block }: Props) {
  const {
    updateSelected,
    openDataPanel,
    selectChartPart,
    setSelectionPanelTab,
    viewportProfile,
  } = useComunicadoEditor();
  const [panel, setPanel] = useState<FloatPanel>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const elementsBtnRef = useRef<HTMLButtonElement>(null);
  const styleBtnRef = useRef<HTMLButtonElement>(null);
  const dataBtnRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  const floatMetrics = useMemo(() => {
    const designSize = resolveViewportPixelSize(viewportProfile);
    const shortSide = chartFrameShortSidePx(block.frame, designSize);
    return resolveChartFloatToolbarMetrics(shortSide);
  }, [block.frame.h, block.frame.w, viewportProfile]);

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

  const chartKind = toSeriesChartKind(block.chartType) ?? "line";
  const options = mergeComunicadoChartOptions({
    ...block.chartOptions,
    ...partsToChartOptions(block.chartParts),
  });

  useEffect(() => {
    setPanel(null);
  }, [block.id]);

  useEffect(() => {
    if (!panel) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setPanel(null);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [panel]);

  const persistOptions = (nextOptions: ComunicadoChartOptions) => {
    updateSelected({
      chartOptions: nextOptions,
      chartParts: mergeChartPartsWithOptions(block.chartParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  const toggleElement = (elementId: ChartElementId, enabled: boolean) => {
    const result = applyChartElementVisibility(
      elementId,
      enabled,
      options,
      block.chartParts,
    );
    updateSelected({
      chartOptions: result.options,
      chartParts: result.parts,
    } as Partial<ComunicadoBlock>);
  };

  const applyAddElementChoice = (choiceId: ChartAddElementChoiceId) => {
    const result = applyChartAddElementChoiceWithParts(choiceId, options, block.chartParts);
    updateSelected({
      chartOptions: result.options,
      chartParts: result.parts,
    } as Partial<ComunicadoBlock>);
  };

  const openAddElementMoreOptions = (elementId: ChartElementId) => {
    const part = chartElementPrimaryPartRef(elementId);
    if (part) selectChartPart(block.id, part);
    setSelectionPanelTab("element");
    document.getElementById("td-chart-pane-elements")?.scrollIntoView({ block: "nearest" });
    setPanel(null);
  };

  const iconSize = floatMetrics.iconSize;
  const activeAnchorRef =
    panel === "elements" ? elementsBtnRef : panel === "style" ? styleBtnRef : dataBtnRef;

  return (
    <div
      className="td-chart-float"
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
        aria-label="Adicionar elemento de gráfico"
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
        aria-label="Cores e estilos do gráfico"
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
        aria-label="Dados do gráfico"
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
          onDismiss={() => setPanel(null)}
        >
          <div className="td-chart-float__popover td-chart-float__popover--cascade">
            <ChartAddElementMenu
              options={options}
              chartKind={chartKind}
              onApplyChoice={applyAddElementChoice}
              onMoreOptions={openAddElementMoreOptions}
            />
          </div>
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
          aria-label="Cores e estilos do gráfico"
          onDismiss={() => setPanel(null)}
        >
          <div className="td-chart-float__popover td-chart-float__popover--style">
            <ChartColorsStylesMenu
              options={options}
              onApplyOptions={(next) => {
                persistOptions(next);
                setPanel(null);
              }}
              footer={
                <button
                  type="button"
                  className="td-deck-ribbon__cascade-item"
                  onClick={() => {
                    toggleElement("legend", !isChartElementEnabled("legend", options));
                  }}
                >
                  {isChartElementEnabled("legend", options) ? "Ocultar legenda" : "Mostrar legenda"}
                </button>
              }
            />
          </div>
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
          aria-label="Dados do gráfico"
          onDismiss={() => setPanel(null)}
        >
          <div className="td-chart-float__popover td-chart-float__popover--actions">
            <button
              type="button"
              className="td-deck-ribbon__cascade-item"
              onClick={() => {
                openDataPanel();
                setPanel(null);
              }}
            >
              Selecionar dados…
            </button>
          </div>
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
