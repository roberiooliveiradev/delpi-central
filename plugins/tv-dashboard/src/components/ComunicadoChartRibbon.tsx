import { useRef, useState } from "react";
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

import { CHART_ADD_ELEMENT_ITEMS } from "../content/chartAddElementItems";
import {
  CHART_QUICK_LAYOUTS,
  applyChartQuickLayout,
} from "../content/chartQuickLayouts";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../utils/resolveSelectionChromeMode";
import { ChartAddElementMenu } from "./ChartAddElementMenu";
import { ChartChangeTypeDialog } from "./ChartChangeTypeDialog";
import { ChartColorsStylesMenu } from "./ChartColorsStylesMenu";
import { ComunicadoPartFormatRibbon } from "./ComunicadoPartFormatRibbon";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { FormatRibbonOrganizeSection, FormatRibbonFrameSection, FormatRibbonTypographySections } from "./formatRibbon";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonLargeButton } from "./deck/DeckRibbonLargeButton";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/**
 * Faixa Elemento para gráfico — Layout Rápido, Adicionar elemento, Alterar tipo.
 */
export function ComunicadoChartRibbon() {
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

  const selectionChrome = resolveSelectionChromeMode({
    selected,
    selectedChartPart,
  });
  if (isPartSelectionChrome(selectionChrome)) {
    return <ComunicadoPartFormatRibbon chrome={selectionChrome} />;
  }

  if (!selected || selected.type !== "chart_view") {
    return (
      <div className="td-deck-ribbon__groups">
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione um gráfico no palco para editar tipo, rótulos, eixos e tipografia.
        </p>
      </div>
    );
  }

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

  return (
    <div className="td-deck-ribbon__groups">
      <FormatRibbonTypographySections />

      <DeckRibbonGroup label="Layout do gráfico" hint={H.chartLabels} wide>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <div ref={addElementAnchorRef} className="td-composer__dropdown">
            <DeckRibbonLargeButton
              icon={LayoutTemplate}
              label={"Adicionar\nelemento"}
              hint="Inclui ou remove elementos do gráfico (título, legenda, eixos…)."
              onClick={() => {
                setAddElementOpen((open) => !open);
                setLayoutOpen(false);
                setColorsOpen(false);
              }}
            />
            {addElementOpen ? (
              <AnchoredPanelPortal
                open={addElementOpen}
                anchorRef={addElementAnchorRef}
                panelRef={addElementPanelRef}
                variant="bare"
                portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
                className="td-chart-add-element-portal"
                role="menu"
                aria-label="Adicionar elemento de gráfico"
              >
                <div>
                  <ChartAddElementMenu
                    options={options}
                    chartKind={chartKind}
                    onApplyChoice={applyAddElementChoice}
                    onMoreOptions={openAddElementMoreOptions}
                  />
                </div>
              </AnchoredPanelPortal>
            ) : null}
          </div>

          <div ref={layoutAnchorRef} className="td-composer__dropdown">
            <DeckRibbonLargeButton
              icon={Grid3x3}
              label={"Layout\nrápido"}
              hint="Aplica um conjunto de visibilidade de título, legenda, eixos e tabela."
              onClick={() => {
                setLayoutOpen((open) => !open);
                setAddElementOpen(false);
                setColorsOpen(false);
              }}
            />
            {layoutOpen ? (
              <AnchoredPanelPortal
                open={layoutOpen}
                anchorRef={layoutAnchorRef}
                panelRef={layoutPanelRef}
                variant="bare"
                portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
                className="td-chart-quick-layout-portal"
                role="menu"
                aria-label="Layout rápido"
              >
                <div className="td-chart-quick-layout">
                  {CHART_QUICK_LAYOUTS.map((layout) => (
                    <button
                      key={layout.id}
                      type="button"
                      className="td-chart-quick-layout__item"
                      title={layout.hint}
                      onClick={() => applyLayout(layout.id)}
                    >
                      <span
                        className={`td-chart-quick-layout__wire td-chart-quick-layout__wire--${layout.id}`}
                        aria-hidden="true"
                      />
                      <span className="td-chart-quick-layout__label">{layout.label}</span>
                    </button>
                  ))}
                </div>
              </AnchoredPanelPortal>
            ) : null}
          </div>
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Estilos" hint="Cores da série e presets de tema/grade.">
        <div ref={colorsAnchorRef} className="td-composer__dropdown">
          <DeckRibbonLargeButton
            icon={Palette}
            label={"Alterar\ncores"}
            hint="Paletas Delpi para a cor da série e estilos rápidos (tema, grade, marcadores)."
            onClick={() => {
              setColorsOpen((open) => !open);
              setAddElementOpen(false);
              setLayoutOpen(false);
            }}
          />
          {colorsOpen ? (
            <AnchoredPanelPortal
              open={colorsOpen}
              anchorRef={colorsAnchorRef}
              panelRef={colorsPanelRef}
              variant="bare"
              portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
              className="td-chart-colors-portal"
              role="menu"
              aria-label="Alterar cores e estilos"
            >
              <div className="td-chart-float__popover td-chart-float__popover--style">
                <ChartColorsStylesMenu
                  options={options}
                  onApplyOptions={(next) => {
                    persistOptions(next);
                    setColorsOpen(false);
                  }}
                />
              </div>
            </AnchoredPanelPortal>
          ) : null}
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Dados" hint={H.chartData}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Database}
            label="Selecionar dados"
            hint="Abre o painel de fontes de dados (como Selecionar Dados no Excel)."
            onClick={() => openDataPanel()}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Tipo" hint={H.chartType}>
        <DeckRibbonLargeButton
          icon={Replace}
          label={"Alterar tipo\nde gráfico"}
          hint="Abre o diálogo com o mesmo catálogo de tipos de Inserir → Gráficos."
          onClick={() => setChangeTypeOpen(true)}
        />
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Rótulos" hint={H.chartLabels}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          {CHART_ADD_ELEMENT_ITEMS.filter((item) =>
            ["chartTitle", "axisTitles", "legend", "dataLabels", "dataTable"].includes(item.id),
          ).map((item) => {
            const enabled = isChartElementEnabled(item.id, options);
            const focused = isChartElementOpenForPart(item.id, selectedChartPart);
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
                      toggleElement(item.id, false);
                    } else {
                      const part = chartElementPrimaryPartRef(item.id);
                      if (part) selectChartPart(block.id, part);
                    }
                    return;
                  }
                  toggleElement(item.id, !enabled);
                }}
              />
            );
          })}
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Eixos" hint={H.chartAxes}>
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
            const enabled = isChartElementEnabled(item.id, options);
            const focused = isChartElementOpenForPart(item.id, selectedChartPart);
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
                      toggleElement(item.id, false);
                    } else {
                      const part = chartElementPrimaryPartRef(item.id);
                      if (part) selectChartPart(block.id, part);
                    }
                    return;
                  }
                  toggleElement(item.id, true);
                }}
              />
            );
          })}
        </div>
      </DeckRibbonGroup>

      <div className="td-deck-ribbon__group-cluster td-deck-ribbon__group-cluster--frame-organize">
        <FormatRibbonFrameSection />
        <FormatRibbonOrganizeSection />
      </div>

      <ChartChangeTypeDialog
        open={changeTypeOpen}
        currentType={block.chartType as DelpiChartType}
        onClose={() => setChangeTypeOpen(false)}
        onConfirm={setChartType}
      />
    </div>
  );
}
