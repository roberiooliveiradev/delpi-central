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

import { ChartAddElementMenu } from "./ChartAddElementMenu";
import { ChartColorsStylesMenu } from "./ChartColorsStylesMenu";
import { ChartSelectDataModal } from "./ChartSelectDataModal";
import { ComplexSelectionFloatToolbar } from "./ComplexSelectionFloatToolbar";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { useState } from "react";

type Props = {
  block: ComunicadoChartViewBlock;
};

/**
 * Float do gráfico — shell genérico + menus de elementos / estilo / dados.
 */
export function ChartSelectionFloatToolbar({ block }: Props) {
  const {
    updateSelected,
    openDataPanel,
    selectChartPart,
    setSelectionPanelTab,
  } = useComunicadoEditor();
  const [selectDataOpen, setSelectDataOpen] = useState(false);

  const chartKind = toSeriesChartKind(block.chartType) ?? "line";
  const options = mergeComunicadoChartOptions({
    ...block.chartOptions,
    ...partsToChartOptions(block.chartParts),
  });

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
  };

  const openDataFocus = (anchorId?: string) => {
    openDataPanel();
    setSelectionPanelTab("data");
    if (anchorId) {
      requestAnimationFrame(() => {
        document.getElementById(anchorId)?.scrollIntoView({ block: "nearest" });
      });
    }
  };

  return (
    <>
    <ComplexSelectionFloatToolbar
      blockId={block.id}
      frame={block.frame}
      labels={{
        elements: "Adicionar elemento de gráfico",
        style: "Cores e estilos do gráfico",
        data: "Dados do gráfico",
      }}
      renderElements={(close) => (
        <ChartAddElementMenu
          options={options}
          chartKind={chartKind}
          onApplyChoice={applyAddElementChoice}
          onMoreOptions={(elementId) => {
            openAddElementMoreOptions(elementId);
            close();
          }}
        />
      )}
      renderStyle={(close) => (
        <ChartColorsStylesMenu
          options={options}
          onApplyOptions={(next) => {
            persistOptions(next);
            close();
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
      )}
      renderData={(close) => (
        <>
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={() => {
              setSelectDataOpen(true);
              close();
            }}
          >
            Selecionar dados…
          </button>
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={() => {
              openDataFocus("td-view-chart-axes");
              close();
            }}
          >
            Eixos e séries…
          </button>
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={() => {
              openDataFocus("td-view-data-source");
              close();
            }}
          >
            Fonte de dados…
          </button>
        </>
      )}
    />
    <ChartSelectDataModal
      open={selectDataOpen}
      onClose={() => setSelectDataOpen(false)}
      block={block}
    />
    </>
  );
}
