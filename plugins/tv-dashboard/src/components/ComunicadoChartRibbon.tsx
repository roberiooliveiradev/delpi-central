import {
  BarChart3,
  ChartArea,
  ChartColumn,
  ChartColumnStacked,
  ChartLine,
  ChartNetwork,
  ChartNoAxesCombined,
  ChartPie,
  ChartScatter,
  ChartSpline,
  CircleDot,
  Database,
  Filter,
  Grid3x3,
  Heading,
  ListOrdered,
  Paintbrush,
  Table2,
  Tags,
  Type,
} from "lucide-react";
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
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/**
 * Faixa contextual «Gráfico» — espelha a aba Gráfico do Excel Online:
 * Dados · Tipo · Rótulos · Eixos · Formato.
 */
export function ComunicadoChartRibbon() {
  const {
    selected,
    selectedChartPart,
    updateSelected,
    selectChartPart,
    openDataPanel,
    requestRibbonTab,
  } = useComunicadoEditor();

  if (!selected || selected.type !== "chart_view") {
    return (
      <div className="td-deck-ribbon__groups">
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione um gráfico no palco para editar tipo, rótulos, eixos e formato (como no Excel).
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

  const setChartType = (chartType: ComunicadoChartType) => {
    updateSelected({ chartType } as Partial<ComunicadoBlock>);
  };

  const openFormatSelection = () => {
    if (selectedChartPart) {
      selectChartPart(block.id, selectedChartPart);
    } else {
      selectChartPart(block.id, { kind: "chartArea" });
    }
    requestRibbonTab("format");
  };

  return (
    <div className="td-deck-ribbon__groups">
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

      <DeckRibbonGroup label="Alterar tipo" hint={H.chartType}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={ChartColumn}
            label="Coluna"
            hint="Gráfico de colunas/barras."
            active={block.chartType === "bar"}
            onClick={() => setChartType("bar")}
          />
          <DeckRibbonTile
            icon={ChartColumnStacked}
            label="Empilhado"
            hint="Colunas empilhadas."
            active={block.chartType === "stacked_bar"}
            onClick={() => setChartType("stacked_bar")}
          />
          <DeckRibbonTile
            icon={BarChart3}
            label="Histograma"
            hint="Histograma (faixas)."
            active={block.chartType === "histogram"}
            onClick={() => setChartType("histogram")}
          />
          <DeckRibbonTile
            icon={ChartLine}
            label="Linha"
            hint="Gráfico de linhas."
            active={block.chartType === "line"}
            onClick={() => setChartType("line")}
          />
          <DeckRibbonTile
            icon={ChartArea}
            label="Área"
            hint="Gráfico de área (preenchimento sob a série)."
            active={block.chartType === "area"}
            onClick={() => setChartType("area")}
          />
          <DeckRibbonTile
            icon={ChartPie}
            label="Pizza"
            hint="Gráfico de pizza (fatias selecionáveis)."
            active={block.chartType === "pie" || block.chartType === "doughnut"}
            onClick={() => setChartType("pie")}
          />
          <DeckRibbonTile
            icon={ChartSpline}
            label="Combo"
            hint="Colunas + linha no mesmo gráfico."
            active={block.chartType === "combo"}
            onClick={() => setChartType("combo")}
          />
          <DeckRibbonTile
            icon={ChartScatter}
            label="Dispersão"
            hint="Gráfico de dispersão (XY)."
            active={block.chartType === "scatter"}
            onClick={() => setChartType("scatter")}
          />
          <DeckRibbonTile
            icon={CircleDot}
            label="Bolhas"
            hint="Gráfico de bolhas."
            active={block.chartType === "bubble"}
            onClick={() => setChartType("bubble")}
          />
          <DeckRibbonTile
            icon={ChartNetwork}
            label="Radar"
            hint="Gráfico radar / teia."
            active={block.chartType === "radar"}
            onClick={() => setChartType("radar")}
          />
          <DeckRibbonTile
            icon={ChartNoAxesCombined}
            label="Cascata"
            hint="Gráfico em cascata (waterfall)."
            active={block.chartType === "waterfall"}
            onClick={() => setChartType("waterfall")}
          />
          <DeckRibbonTile
            icon={Filter}
            label="Funil"
            hint="Gráfico de funil."
            active={block.chartType === "funnel"}
            onClick={() => setChartType("funnel")}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Rótulos" hint={H.chartLabels}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Heading}
            label="Título"
            hint="Exibir ou ocultar o título do gráfico."
            active={isChartElementEnabled("chartTitle", options)}
            onClick={() =>
              toggleElement("chartTitle", !isChartElementEnabled("chartTitle", options))
            }
          />
          <DeckRibbonTile
            icon={Type}
            label="Eixos"
            hint="Títulos dos eixos X e Y."
            active={isChartElementEnabled("axisTitles", options)}
            onClick={() =>
              toggleElement("axisTitles", !isChartElementEnabled("axisTitles", options))
            }
          />
          <DeckRibbonTile
            icon={ListOrdered}
            label="Legenda"
            hint="Exibir ou ocultar a legenda."
            active={isChartElementEnabled("legend", options)}
            onClick={() => toggleElement("legend", !isChartElementEnabled("legend", options))}
          />
          <DeckRibbonTile
            icon={Tags}
            label="Rótulos"
            hint="Rótulos de dados nos pontos."
            active={isChartElementEnabled("dataLabels", options)}
            onClick={() =>
              toggleElement("dataLabels", !isChartElementEnabled("dataLabels", options))
            }
          />
          <DeckRibbonTile
            icon={Table2}
            label="Tabela"
            hint="Tabela de dados abaixo do gráfico."
            active={isChartElementEnabled("dataTable", options)}
            onClick={() =>
              toggleElement("dataTable", !isChartElementEnabled("dataTable", options))
            }
          />
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

      <DeckRibbonGroup label="Formato" hint={H.chartFormat}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Paintbrush}
            label="Formato"
            hint="Abre Formatar com a parte selecionada (área, série, marcador…)."
            onClick={openFormatSelection}
          />
        </div>
      </DeckRibbonGroup>
    </div>
  );
}
