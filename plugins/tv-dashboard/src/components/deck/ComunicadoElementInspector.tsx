import { NativeTextControl } from "@delpi/plugin-ui/index";
import {
  isDataBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isComunicadoVisualBoxBlock,
  normalizeHrefInput,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import { useEffect, useMemo, useState } from "react";

import { listDataRoutes, type BranchScope, type TvDataRouteCatalogItem } from "../../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { comunicadoBlockTypeLabel } from "../../utils/comunicadoBlockLabels";
import { DataBindingInspector } from "../DataBindingInspector";
import { DataPreparePanel } from "../DataPreparePanel";
import { TextDataBindingInspector, canShowTextDataBindingInspector } from "../TextDataBindingInspector";
import { ChartViewOptionsInspector } from "../ChartViewOptionsInspector";
import { TableViewOptionsInspector } from "../TableViewOptionsInspector";
import { VisualDataViewInspector } from "../VisualDataViewInspector";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import {
  SelectionSectionsHost,
  SelectionTypedWithTailHost,
} from "../selectionSections";
import { DeckField } from "./DeckField";
import { DeckInspectorLayout } from "./DeckInspectorLayout";
import { DeckPropertySection } from "./DeckPropertySection";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

type Labels = Record<string, string>;

export function ComunicadoElementInspector({
  labels = {},
  placement = "default",
  panelFocus = "element",
  onOpenDataSources,
  branchScope = null,
}: {
  labels?: Labels;
  placement?: "default" | "side";
  /**
   * Escopo do conteúdo no painel lateral — espelha as abas da top bar.
   * `element` = tudo; `tableDesign` / `tableLayout` = fatia da tabela.
   */
  panelFocus?: "element" | "tableDesign" | "tableLayout";
  onOpenDataSources?: () => void;
  branchScope?: BranchScope | null;
}) {
  const {
    selected,
    selectedIds,
    selectedKpiPart,
    selectedChartPart,
    selectedTablePart,
    selectedInputPart,
    updateSelected,
    updateBlockLink,
    blocks,
  } = useComunicadoEditor();

  const hasPartSelection = Boolean(
    selectedKpiPart || selectedChartPart || selectedTablePart || selectedInputPart,
  );

  const multiSelect = selectedIds.length > 1;
  const isVisualBox = selected ? isComunicadoVisualBoxBlock(selected) : false;
  const isIconBlock = selected?.type === "icon";
  const isMediaBlock = selected?.type === "image" || selected?.type === "video";
  const isSidebarLinkBlock = isMediaBlock || isVisualBox || isIconBlock;
  const isDataBlock = selected ? isDataBlockType(selected.type) || isDataSourceBlockType(selected.type) : false;
  const isViewBlock = selected ? isDataViewBlockType(selected.type) : false;
  const isVisualBoxData = selected ? canShowTextDataBindingInspector(selected) : false;
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);

  useEffect(() => {
    if (!isDataBlock && !isVisualBoxData) return;
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, [isDataBlock, isVisualBoxData]);

  const selectedRoute = useMemo(() => {
    if (isDataBlock && selected && "dataBinding" in selected) {
      return routes.find((route) => route.operationId === selected.dataBinding.operationId) ?? null;
    }
    if (isVisualBoxData && selected?.dataSourceId) {
      const source = blocks.find((block) => block.id === selected.dataSourceId);
      if (source && "dataBinding" in source) {
        return routes.find((route) => route.operationId === source.dataBinding.operationId) ?? null;
      }
    }
    return null;
  }, [blocks, isDataBlock, isVisualBoxData, routes, selected]);

  if (selectedIds.length === 0 || !selected) {
    return (
      <DeckInspectorLayout variant={placement}>
        <p className="td-subtitle td-deck-inspector__empty">
          Selecione um elemento no palco ou arraste para posicionar.
        </p>
      </DeckInspectorLayout>
    );
  }

  const pane = placement === "side";
  const typeLabel = comunicadoBlockTypeLabel(selected.type);

  return (
    <DeckInspectorLayout variant={placement}>
      <DeckPropertySection
        pane={pane}
        title={labels.comunicadoBlocks ?? "Elemento selecionado"}
        hint={E.panel}
        defaultOpen
      >
        {multiSelect ? (
          <p className="td-deck-inspector__meta td-deck-inspector__meta--multi">
            {selectedIds.length} elementos selecionados — edite texto e link direto no palco.
          </p>
        ) : (
          <p className="td-deck-inspector__meta">{typeLabel}</p>
        )}

        {!multiSelect && selected.type === "shape" ? (
          <DeckField id="td-shape-content" label="Texto na forma" hint={E.shapeText}>
            <NativeTextControl
              id="td-shape-content"
              type="text"
              value={selected.content ?? ""}
              onChange={(value) => updateSelected({ content: value } as Partial<ComunicadoBlock>)}
            />
          </DeckField>
        ) : null}

        {!multiSelect && isSidebarLinkBlock ? (
          <DeckField id="td-block-link" label="Link" hint={E.link}>
            <NativeTextControl
              id="td-block-link"
              type="url"
              placeholder="https://…"
              value={"href" in selected ? (selected.href ?? "") : ""}
              onChange={(value) =>
                updateBlockLink(selected.id, normalizeHrefInput(value) || undefined)
              }
            />
          </DeckField>
        ) : null}
      </DeckPropertySection>

      {!multiSelect && isDataBlock ? (
        <DataBindingInspector route={selectedRoute} pane={pane} branchScope={branchScope} />
      ) : null}
      {!multiSelect && selected.type === "data_source" ? (
        <DataPreparePanel pane={pane} block={selected} />
      ) : null}
      {!multiSelect && isViewBlock ? (
        <VisualDataViewInspector
          pane={pane}
          route={selectedRoute}
          onOpenDataSources={onOpenDataSources}
        />
      ) : null}
      {!multiSelect && isVisualBoxData ? (
        <TextDataBindingInspector
          pane={pane}
          route={selectedRoute}
          onOpenDataSources={onOpenDataSources}
        />
      ) : null}

      {!multiSelect && selected.type === "chart_view" && !selectedChartPart ? (
        <>
          <SelectionTypedWithTailHost
            layout="pane"
            labels={labels}
            typed={[
              "typography",
              "chartLayout",
              "chartStyles",
              "chartType",
              "chartLabels",
              "chartAxes",
              "chartSeries",
            ]}
          />
          <ChartViewOptionsInspector pane={pane} omitSeries />
        </>
      ) : null}

      {!multiSelect && selected.type === "table_view" && !selectedTablePart ? (
        <>
          <SelectionTypedWithTailHost
            layout="pane"
            labels={labels}
            typed={
              panelFocus === "tableLayout"
                ? ["tableLayoutData", "tableLayoutDisplay", "tableLayoutAlign"]
                : panelFocus === "tableDesign"
                  ? ["tableStyleOptions", "tableStyles", "tableBorders"]
                  : [
                      "tableStyleOptions",
                      "tableStyles",
                      "tableBorders",
                      "tableLayoutData",
                      "tableLayoutDisplay",
                      "tableLayoutAlign",
                    ]
            }
          />
          {panelFocus !== "tableDesign" ? (
            <TableViewOptionsInspector pane={pane} omitDesignChrome omitCellAlign />
          ) : null}
        </>
      ) : null}

      {!multiSelect && selected.type === "table_view" && selectedTablePart ? (
        <TableViewOptionsInspector pane={pane} omitDesignChrome />
      ) : null}

      {multiSelect ? (
        <SelectionSectionsHost layout="pane" full labels={labels} />
      ) : null}

      {/* Texto, forma, icon, media, canvas, kpi, input, data — host full (visualBox ordena tipografia→forma). */}
      {!multiSelect &&
      selected.type !== "table_view" &&
      selected.type !== "chart_view" &&
      !hasPartSelection ? (
        <SelectionSectionsHost layout="pane" full labels={labels} />
      ) : null}

      {!multiSelect && hasPartSelection ? (
        <SelectionSectionsHost layout="pane" full labels={labels} />
      ) : null}
    </DeckInspectorLayout>
  );
}
