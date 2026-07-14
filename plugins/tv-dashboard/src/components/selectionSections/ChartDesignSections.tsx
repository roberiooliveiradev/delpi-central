import { useRef, useState, type ReactNode } from "react";
import {
  BarChart3,
  Database,
  Grid3x3,
  LayoutTemplate,
  Palette,
  Replace,
} from "lucide-react";
import {
  AnchoredPanelPortal,
  type DelpiChartType,
} from "@delpi/plugin-ui/index";
import {
  applyChartAddElementChoiceWithParts,
  applyChartElementVisibility,
  chartElementPrimaryPartRef,
  isChartElementEnabled,
  isChartElementOpenForPart,
  mergeChartPartsWithOptions,
  mergeComunicadoChartOptions,
  partsToChartOptions,
  toSeriesChartKind,
  type ChartAddElementChoiceId,
  type ChartElementId,
  type ComunicadoBlock,
  type ComunicadoChartOptions,
  type ComunicadoChartType,
  type ComunicadoChartViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { CHART_ADD_ELEMENT_ITEMS } from "../../content/chartAddElementItems";
import {
  CHART_QUICK_LAYOUTS,
  applyChartQuickLayout,
} from "../../content/chartQuickLayouts";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";
import { ChartAddElementMenu } from "../ChartAddElementMenu";
import { ChartChangeTypeDialog } from "../ChartChangeTypeDialog";
import { ChartColorsStylesMenu } from "../ChartColorsStylesMenu";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonLargeButton } from "../deck/DeckRibbonLargeButton";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

function wrapPane(
  title: string,
  hint: string | undefined,
  layout: SelectionSectionLayout,
  body: ReactNode,
  wide?: boolean,
) {
  if (layout === "pane") {
    return (
      <SelectionPaneSection title={title} hint={hint} defaultOpen={false}>
        {body}
      </SelectionPaneSection>
    );
  }
  return (
    <DeckRibbonGroup label={title} hint={hint} wide={wide}>
      {body}
    </DeckRibbonGroup>
  );
}

function useChartDesignControls() {
  const {
    selected,
    selectedChartPart,
    updateSelected,
    selectChartPart,
    openDataPanel,
    setSelectionPanelTab,
  } = useComunicadoEditor();

  const addElementAnchorRef = useRef<HTMLDivElement>(null);
  const addElementPanelRef = useRef<HTMLDivElement>(null);
  const layoutAnchorRef = useRef<HTMLDivElement>(null);
  const layoutPanelRef = useRef<HTMLDivElement>(null);
  const colorsAnchorRef = useRef<HTMLDivElement>(null);
  const colorsPanelRef = useRef<HTMLDivElement>(null);
  const [addElementOpen, setAddElementOpen] = useState(false);
  const [layoutOpen, setLayoutOpen] = useState(false);
  const [colorsOpen, setColorsOpen] = useState(false);
  const [changeTypeOpen, setChangeTypeOpen] = useState(false);

  if (!selected || selected.type !== "chart_view") return null;

  const block = selected as ComunicadoChartViewBlock;
  const chartKind = toSeriesChartKind(block.chartType) ?? "line";
  const options = mergeComunicadoChartOptions({
    ...block.chartOptions,
    ...partsToChartOptions(block.chartParts),
  });

  const toggleElement = (elementId: ChartElementId, enabled: boolean) => {
    const result = applyChartElementVisibility(elementId, enabled, options, block.chartParts);
    updateSelected({
      chartOptions: result.options,
      chartParts: result.parts,
    } as Partial<ComunicadoBlock>);
    if (enabled) {
      const part = chartElementPrimaryPartRef(elementId);
      if (part) selectChartPart(block.id, part);
    }
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
    setAddElementOpen(false);
  };

  const applyLayout = (layoutId: string) => {
    const layout = CHART_QUICK_LAYOUTS.find((item) => item.id === layoutId);
    if (!layout) return;
    const result = applyChartQuickLayout(layout, options, block.chartParts);
    updateSelected({
      chartOptions: result.options,
      chartParts: result.parts,
    } as Partial<ComunicadoBlock>);
    setLayoutOpen(false);
  };

  const setChartType = (chartType: DelpiChartType) => {
    updateSelected({ chartType: chartType as ComunicadoChartType } as Partial<ComunicadoBlock>);
    setChangeTypeOpen(false);
  };

  const persistOptions = (nextOptions: ComunicadoChartOptions) => {
    updateSelected({
      chartOptions: nextOptions,
      chartParts: mergeChartPartsWithOptions(block.chartParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  return {
    block,
    chartKind,
    options,
    selectedChartPart,
    addElementAnchorRef,
    addElementPanelRef,
    layoutAnchorRef,
    layoutPanelRef,
    colorsAnchorRef,
    colorsPanelRef,
    addElementOpen,
    setAddElementOpen,
    layoutOpen,
    setLayoutOpen,
    colorsOpen,
    setColorsOpen,
    changeTypeOpen,
    setChangeTypeOpen,
    toggleElement,
    applyAddElementChoice,
    openAddElementMoreOptions,
    applyLayout,
    setChartType,
    persistOptions,
    openDataPanel,
    selectChartPart,
  };
}

export function ChartLayoutSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useChartDesignControls();
  if (!ctrl) return null;

  const body = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <div ref={ctrl.addElementAnchorRef} className="td-composer__dropdown">
        <DeckRibbonLargeButton
          icon={LayoutTemplate}
          label={"Adicionar\nelemento"}
          hint="Inclui ou remove elementos do gráfico (título, legenda, eixos…)."
          onClick={() => {
            ctrl.setAddElementOpen((open) => !open);
            ctrl.setLayoutOpen(false);
            ctrl.setColorsOpen(false);
          }}
        />
        {ctrl.addElementOpen ? (
          <AnchoredPanelPortal
            open={ctrl.addElementOpen}
            anchorRef={ctrl.addElementAnchorRef}
            panelRef={ctrl.addElementPanelRef}
            variant="bare"
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            className="td-chart-add-element-portal"
            role="menu"
            aria-label="Adicionar elemento de gráfico"
          >
            <div>
              <ChartAddElementMenu
                options={ctrl.options}
                chartKind={ctrl.chartKind}
                onApplyChoice={ctrl.applyAddElementChoice}
                onMoreOptions={ctrl.openAddElementMoreOptions}
              />
            </div>
          </AnchoredPanelPortal>
        ) : null}
      </div>

      <div ref={ctrl.layoutAnchorRef} className="td-composer__dropdown">
        <DeckRibbonLargeButton
          icon={Grid3x3}
          label={"Layout\nrápido"}
          hint="Aplica um conjunto de visibilidade de título, legenda, eixos e tabela."
          onClick={() => {
            ctrl.setLayoutOpen((open) => !open);
            ctrl.setAddElementOpen(false);
            ctrl.setColorsOpen(false);
          }}
        />
        {ctrl.layoutOpen ? (
          <AnchoredPanelPortal
            open={ctrl.layoutOpen}
            anchorRef={ctrl.layoutAnchorRef}
            panelRef={ctrl.layoutPanelRef}
            variant="bare"
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            className="td-chart-quick-layout-portal"
            role="menu"
            aria-label="Layout rápido"
          >
            <div className="td-chart-quick-layout">
              {CHART_QUICK_LAYOUTS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className="td-chart-quick-layout__item"
                  title={item.hint}
                  onClick={() => ctrl.applyLayout(item.id)}
                >
                  <span
                    className={`td-chart-quick-layout__wire td-chart-quick-layout__wire--${item.id}`}
                    aria-hidden="true"
                  />
                  <span className="td-chart-quick-layout__label">{item.label}</span>
                </button>
              ))}
            </div>
          </AnchoredPanelPortal>
        ) : null}
      </div>
    </div>
  );

  return wrapPane("Layout do gráfico", H.chartLabels, layout, body, true);
}

export function ChartStylesSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useChartDesignControls();
  if (!ctrl) return null;

  const styles = (
    <div ref={ctrl.colorsAnchorRef} className="td-composer__dropdown">
      <DeckRibbonLargeButton
        icon={Palette}
        label={"Alterar\ncores"}
        hint="Paletas Delpi para a cor da série e estilos rápidos (tema, grade, marcadores)."
        onClick={() => {
          ctrl.setColorsOpen((open) => !open);
          ctrl.setAddElementOpen(false);
          ctrl.setLayoutOpen(false);
        }}
      />
      {ctrl.colorsOpen ? (
        <AnchoredPanelPortal
          open={ctrl.colorsOpen}
          anchorRef={ctrl.colorsAnchorRef}
          panelRef={ctrl.colorsPanelRef}
          variant="bare"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          className="td-chart-colors-portal"
          role="menu"
          aria-label="Alterar cores e estilos"
        >
          <div className="td-chart-float__popover td-chart-float__popover--style">
            <ChartColorsStylesMenu
              options={ctrl.options}
              onApplyOptions={(next) => {
                ctrl.persistOptions(next);
                ctrl.setColorsOpen(false);
              }}
            />
          </div>
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );

  const data = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTile
        icon={Database}
        label="Selecionar dados"
        hint="Abre o painel de fontes de dados (como Selecionar Dados no Excel)."
        onClick={() => ctrl.openDataPanel()}
      />
    </div>
  );

  if (layout === "pane") {
    return (
      <>
        <SelectionPaneSection
          title="Estilos"
          hint="Cores da série e presets de tema/grade."
          defaultOpen={false}
        >
          {styles}
        </SelectionPaneSection>
        <SelectionPaneSection title="Dados" hint={H.chartData} defaultOpen={false}>
          {data}
        </SelectionPaneSection>
      </>
    );
  }

  return (
    <>
      <DeckRibbonGroup label="Estilos" hint="Cores da série e presets de tema/grade.">
        {styles}
      </DeckRibbonGroup>
      <DeckRibbonGroup label="Dados" hint={H.chartData}>
        {data}
      </DeckRibbonGroup>
    </>
  );
}

export function ChartTypeSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useChartDesignControls();
  if (!ctrl) return null;

  const body = (
    <>
      <DeckRibbonLargeButton
        icon={Replace}
        label={"Alterar tipo\nde gráfico"}
        hint="Abre o diálogo com o mesmo catálogo de tipos de Inserir → Gráficos."
        onClick={() => ctrl.setChangeTypeOpen(true)}
      />
      <ChartChangeTypeDialog
        open={ctrl.changeTypeOpen}
        currentType={ctrl.block.chartType as DelpiChartType}
        onClose={() => ctrl.setChangeTypeOpen(false)}
        onConfirm={ctrl.setChartType}
      />
    </>
  );

  return wrapPane("Tipo", H.chartType, layout, body);
}

export function ChartLabelsSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useChartDesignControls();
  if (!ctrl) return null;

  const body = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      {CHART_ADD_ELEMENT_ITEMS.filter((item) =>
        ["chartTitle", "axisTitles", "legend", "dataLabels", "dataTable"].includes(item.id),
      ).map((item) => {
        const enabled = isChartElementEnabled(item.id, ctrl.options);
        const focused = isChartElementOpenForPart(item.id, ctrl.selectedChartPart);
        return (
          <DeckRibbonTile
            key={item.id}
            icon={item.icon}
            label={item.label.split(" ")[0] ?? item.label}
            hint={
              item.id === "dataLabels"
                ? "Liga os rótulos e edita tipografia de todos de uma vez."
                : item.label
            }
            active={enabled || focused}
            onClick={() => {
              if (item.id === "dataLabels" && enabled) {
                if (focused) {
                  ctrl.toggleElement(item.id, false);
                } else {
                  const part = chartElementPrimaryPartRef(item.id);
                  if (part) ctrl.selectChartPart(ctrl.block.id, part);
                }
                return;
              }
              ctrl.toggleElement(item.id, !enabled);
            }}
          />
        );
      })}
    </div>
  );

  return wrapPane("Rótulos", H.chartLabels, layout, body);
}

export function ChartAxesSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useChartDesignControls();
  if (!ctrl) return null;

  const body = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      {(
        [
          {
            id: "axes" as const,
            icon: BarChart3,
            label: "Eixos",
            hint: "Liga os eixos e seleciona ambos para contorno/estilo.",
          },
          {
            id: "gridlines" as const,
            icon: Grid3x3,
            label: "Grade",
            hint: "Liga a grade horizontal e edita o traço das linhas.",
          },
        ] as const
      ).map((item) => {
        const enabled = isChartElementEnabled(item.id, ctrl.options);
        const focused = isChartElementOpenForPart(item.id, ctrl.selectedChartPart);
        return (
          <DeckRibbonTile
            key={item.id}
            icon={item.icon}
            label={item.label}
            hint={item.hint}
            active={enabled || focused}
            onClick={() => {
              if (enabled) {
                if (focused) {
                  ctrl.toggleElement(item.id, false);
                } else {
                  const part = chartElementPrimaryPartRef(item.id);
                  if (part) ctrl.selectChartPart(ctrl.block.id, part);
                }
                return;
              }
              ctrl.toggleElement(item.id, true);
            }}
          />
        );
      })}
    </div>
  );

  return wrapPane("Eixos", H.chartAxes, layout, body);
}
