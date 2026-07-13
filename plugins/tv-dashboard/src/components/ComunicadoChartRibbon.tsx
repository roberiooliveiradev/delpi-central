import { useRef, useState } from "react";
import {
  BarChart3,
  ChevronRight,
  Database,
  Grid3x3,
  Heading,
  ListOrdered,
  Plus,
  Replace,
  Table2,
  Tags,
  Type,
} from "lucide-react";
import {
  AnchoredPanelPortal,
  ChartTypeCatalogPanel,
  type DelpiChartType,
} from "@delpi/plugin-ui/index";
import {
  applyChartElementVisibility,
  chartElementPrimaryPartRef,
  isChartElementEnabled,
  mergeComunicadoChartOptions,
  partsToChartOptions,
  type ComunicadoChartType,
  type ComunicadoChartViewBlock,
  type ChartElementId,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { FormatRibbonOrganizeSection, FormatRibbonFrameSection, FormatRibbonTypographySections } from "./formatRibbon";
import { ChartRibbonShapeChrome } from "./formatRibbon/ChartRibbonShapeChrome";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonLargeButton } from "./deck/DeckRibbonLargeButton";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const ADD_ELEMENT_ITEMS: Array<{
  id: ChartElementId;
  icon: typeof Heading;
  label: string;
}> = [
  { id: "chartTitle", icon: Heading, label: "Título do gráfico" },
  { id: "axisTitles", icon: Type, label: "Títulos dos eixos" },
  { id: "legend", icon: ListOrdered, label: "Legenda" },
  { id: "dataLabels", icon: Tags, label: "Rótulos de dados" },
  { id: "dataTable", icon: Table2, label: "Tabela de dados" },
  { id: "axes", icon: BarChart3, label: "Eixos" },
  { id: "gridlines", icon: Grid3x3, label: "Linhas de grade" },
];

/**
 * Faixa Elemento para gráfico — Layout (adicionar elemento) + tipo + rótulos.
 */
export function ComunicadoChartRibbon() {
  const {
    selected,
    selectedChartPart,
    updateSelected,
    selectChartPart,
    openDataPanel,
  } = useComunicadoEditor();
  const chartTypeAnchorRef = useRef<HTMLDivElement>(null);
  const chartTypePanelRef = useRef<HTMLDivElement>(null);
  const addElementAnchorRef = useRef<HTMLDivElement>(null);
  const addElementPanelRef = useRef<HTMLDivElement>(null);
  const [chartTypeMenuOpen, setChartTypeMenuOpen] = useState(false);
  const [addElementOpen, setAddElementOpen] = useState(false);

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

  const setChartType = (chartType: DelpiChartType) => {
    updateSelected({ chartType: chartType as ComunicadoChartType } as Partial<ComunicadoBlock>);
    setChartTypeMenuOpen(false);
  };

  return (
    <div className="td-deck-ribbon__groups">
      <FormatRibbonTypographySections />

      <DeckRibbonGroup label="Layout do gráfico" hint={H.chartLabels}>
        <div ref={addElementAnchorRef} className="td-composer__dropdown">
          <DeckRibbonLargeButton
            icon={Plus}
            label={"Adicionar\nelemento"}
            hint="Inclui ou remove elementos do gráfico (título, legenda, eixos…)."
            onClick={() => setAddElementOpen((open) => !open)}
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
              <div ref={addElementPanelRef}>
                <ul className="td-deck-ribbon__cascade-menu">
                  {ADD_ELEMENT_ITEMS.map((item) => {
                    const enabled = isChartElementEnabled(item.id, options);
                    const Icon = item.icon;
                    return (
                      <li key={item.id}>
                        <button
                          type="button"
                          role="menuitemcheckbox"
                          aria-checked={enabled}
                          className="td-deck-ribbon__cascade-item"
                          onClick={() => {
                            toggleElement(item.id, !enabled);
                          }}
                        >
                          <Icon size={16} aria-hidden="true" />
                          <span>{item.label}</span>
                          {enabled ? <ChevronRight size={14} aria-hidden="true" /> : null}
                        </button>
                      </li>
                    );
                  })}
                </ul>
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
        <div ref={chartTypeAnchorRef} className="td-composer__dropdown">
          <DeckRibbonLargeButton
            icon={Replace}
            label={"Alterar tipo\nde gráfico"}
            hint="Abre o mesmo catálogo de tipos usado em Inserir → Gráficos."
            onClick={() => setChartTypeMenuOpen((open) => !open)}
          />
          {chartTypeMenuOpen ? (
            <AnchoredPanelPortal
              open={chartTypeMenuOpen}
              anchorRef={chartTypeAnchorRef}
              panelRef={chartTypePanelRef}
              variant="bare"
              portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
              className="td-chart-catalog-portal"
              role="dialog"
              aria-label="Alterar tipo de gráfico"
            >
              <ChartTypeCatalogPanel title="Alterar tipo de gráfico" onSelect={setChartType} />
            </AnchoredPanelPortal>
          ) : null}
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Rótulos" hint={H.chartLabels}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          {ADD_ELEMENT_ITEMS.filter((item) =>
            ["chartTitle", "axisTitles", "legend", "dataLabels", "dataTable"].includes(item.id),
          ).map((item) => (
            <DeckRibbonTile
              key={item.id}
              icon={item.icon}
              label={item.label.split(" ")[0] ?? item.label}
              hint={item.label}
              active={isChartElementEnabled(item.id, options)}
              onClick={() =>
                toggleElement(item.id, !isChartElementEnabled(item.id, options))
              }
            />
          ))}
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Eixos" hint={H.chartAxes}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={BarChart3}
            label="Eixos"
            hint="Mostrar ou ocultar eixos e rótulos de escala."
            active={isChartElementEnabled("axes", options)}
            onClick={() => toggleElement("axes", !isChartElementEnabled("axes", options))}
          />
          <DeckRibbonTile
            icon={Grid3x3}
            label="Grade"
            hint="Linhas de grade horizontais."
            active={isChartElementEnabled("gridlines", options)}
            onClick={() =>
              toggleElement("gridlines", !isChartElementEnabled("gridlines", options))
            }
          />
        </div>
      </DeckRibbonGroup>

      <ChartRibbonShapeChrome block={block} />
      <FormatRibbonFrameSection />
      <FormatRibbonOrganizeSection />

      {selectedChartPart == null ? (
        <p className="td-subtitle td-deck-ribbon__hint">
          Forma aplica-se à área do gráfico. Clique em título, legenda ou série para formatar a
          parte.
        </p>
      ) : null}
    </div>
  );
}
