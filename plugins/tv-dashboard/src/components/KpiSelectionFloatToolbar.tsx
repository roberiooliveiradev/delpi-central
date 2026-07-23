import {
  applyKpiAddElementChoiceWithParts,
  kpiElementPrimaryPartRef,
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  type ComunicadoBlock,
  type ComunicadoKpiOptions,
  type ComunicadoKpiViewBlock,
  type KpiAddElementChoiceId,
  type KpiElementId,
} from "@delpi/tv-dashboard-presentation";

import { ComplexSelectionFloatToolbar } from "./ComplexSelectionFloatToolbar";
import { KpiAddElementMenu } from "./KpiAddElementMenu";
import { KpiColorsStylesMenu } from "./KpiColorsStylesMenu";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  block: ComunicadoKpiViewBlock;
};

/**
 * Float do KPI — + elementos (flyouts), pincel aparência, funil dados/métricas.
 */
export function KpiSelectionFloatToolbar({ block }: Props) {
  const { updateSelected, openDataPanel, selectKpiPart, setSelectionPanelTab } =
    useComunicadoEditor();

  const options = mergeComunicadoKpiOptions({
    ...block.kpiOptions,
    ...partsToKpiOptions(block.kpiParts),
  });

  const persistOptions = (nextOptions: ComunicadoKpiOptions) => {
    updateSelected({
      kpiOptions: nextOptions,
      kpiParts: mergeKpiPartsWithOptions(block.kpiParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  const applyAddElementChoice = (choiceId: KpiAddElementChoiceId) => {
    const result = applyKpiAddElementChoiceWithParts(choiceId, options, block.kpiParts);
    updateSelected({
      kpiOptions: mergeComunicadoKpiOptions(result.options),
      kpiParts: result.parts,
    } as Partial<ComunicadoBlock>);
  };

  const openAddElementMoreOptions = (elementId: KpiElementId) => {
    selectKpiPart(block.id, kpiElementPrimaryPartRef(elementId));
    setSelectionPanelTab("element");
    document.getElementById("td-kpi-pane-elements")?.scrollIntoView({ block: "nearest" });
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
    <ComplexSelectionFloatToolbar
      blockId={block.id}
      frame={block.frame}
      labels={{
        elements: "Elementos do KPI",
        style: "Aparência do KPI",
        data: "Dados do KPI",
      }}
      renderElements={(close) => (
        <KpiAddElementMenu
          options={options}
          parts={block.kpiParts}
          onApplyChoice={(choiceId) => {
            applyAddElementChoice(choiceId);
            close();
          }}
          onMoreOptions={(elementId) => {
            openAddElementMoreOptions(elementId);
            close();
          }}
        />
      )}
      renderStyle={(close) => (
        <KpiColorsStylesMenu
          options={options}
          onApplyOptions={(next) => {
            persistOptions(mergeComunicadoKpiOptions(next));
            close();
          }}
          footer={
            <button
              type="button"
              className="td-deck-ribbon__cascade-item"
              onClick={() => {
                openDataFocus("td-view-kpi-color-rules");
                close();
              }}
            >
              Formato e regras de cor…
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
              openDataFocus("td-view-data-source");
              close();
            }}
          >
            Selecionar fonte…
          </button>
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={() => {
              openDataFocus("td-view-kpi-metrics");
              close();
            }}
          >
            Métricas e cálculo…
          </button>
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={() => {
              openDataFocus("td-view-kpi-color-rules");
              close();
            }}
          >
            Formato e regras…
          </button>
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={() => {
              openDataFocus("td-view-kpi-target");
              close();
            }}
          >
            Meta e comparação…
          </button>
        </>
      )}
    />
  );
}
