import { useEffect, useRef, useState } from "react";
import { Filter, Paintbrush, Plus } from "lucide-react";
import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import {
  applyChartElementVisibility,
  isChartElementEnabled,
  mergeComunicadoChartOptions,
  partsToChartOptions,
  type ChartElementId,
  type ComunicadoBlock,
  type ComunicadoChartViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { ChartAddElementMenu } from "./ChartAddElementMenu";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  block: ComunicadoChartViewBlock;
};

type FloatPanel = "elements" | "style" | "data" | null;

/**
 * Coluna flutuante à direita do bbox do gráfico (+ / pincel / funil).
 * `+` reutiliza o mesmo menu «Adicionar elemento» da ribbon.
 */
export function ChartSelectionFloatToolbar({ block }: Props) {
  const { updateSelected, openDataPanel, requestRibbonTab } = useComunicadoEditor();
  const [panel, setPanel] = useState<FloatPanel>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

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

  return (
    <div
      className="td-chart-float"
      ref={rootRef}
      onPointerDown={(event) => event.stopPropagation()}
    >
      <button
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
        <Plus size={16} aria-hidden="true" />
      </button>
      <button
        type="button"
        className={[
          "td-chart-float__btn",
          panel === "style" ? "td-chart-float__btn--active" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label="Estilo do gráfico"
        aria-expanded={panel === "style"}
        onClick={() => setPanel((prev) => (prev === "style" ? null : "style"))}
      >
        <Paintbrush size={16} aria-hidden="true" />
      </button>
      <button
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
        <Filter size={16} aria-hidden="true" />
      </button>

      {panel === "elements" ? (
        <AnchoredPanelPortal
          open
          anchorRef={rootRef}
          panelRef={popoverRef}
          variant="bare"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          className="td-chart-float__portal"
          role="menu"
        >
          <div ref={popoverRef} className="td-chart-float__popover">
            <ChartAddElementMenu options={options} onToggle={toggleElement} />
          </div>
        </AnchoredPanelPortal>
      ) : null}

      {panel === "style" ? (
        <AnchoredPanelPortal
          open
          anchorRef={rootRef}
          panelRef={popoverRef}
          variant="bare"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          className="td-chart-float__portal"
          role="menu"
        >
          <div ref={popoverRef} className="td-chart-float__popover td-chart-float__popover--actions">
            <button
              type="button"
              className="td-deck-ribbon__cascade-item"
              onClick={() => {
                requestRibbonTab("element");
                setPanel(null);
              }}
            >
              Abrir estilos na faixa Elemento
            </button>
            <button
              type="button"
              className="td-deck-ribbon__cascade-item"
              onClick={() => {
                toggleElement("legend", !isChartElementEnabled("legend", options));
              }}
            >
              {isChartElementEnabled("legend", options) ? "Ocultar legenda" : "Mostrar legenda"}
            </button>
          </div>
        </AnchoredPanelPortal>
      ) : null}

      {panel === "data" ? (
        <AnchoredPanelPortal
          open
          anchorRef={rootRef}
          panelRef={popoverRef}
          variant="bare"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          className="td-chart-float__portal"
          role="menu"
        >
          <div ref={popoverRef} className="td-chart-float__popover td-chart-float__popover--actions">
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
