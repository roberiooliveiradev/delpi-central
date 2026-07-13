import { useRef, useState } from "react";
import {
  BarChart3,
  Database,
  Grid3x3,
  Heading,
  ListOrdered,
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
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/**
 * Faixa Elemento para gráfico — dados, tipo (mesmo catálogo de Inserir),
 * rótulos/eixos e configurações de forma no mesmo lugar.
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
  const [chartTypeMenuOpen, setChartTypeMenuOpen] = useState(false);

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
        <div ref={chartTypeAnchorRef} className="td-composer__dropdown">
          <DeckRibbonTile
            icon={Replace}
            label="Trocar gráfico"
            hint="Abre o mesmo catálogo de tipos usado em Inserir → Gráficos."
            active={chartTypeMenuOpen}
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
              role="menu"
              aria-label="Alterar tipo de gráfico"
            >
              <ChartTypeCatalogPanel title="Alterar tipo de gráfico" onSelect={setChartType} />
            </AnchoredPanelPortal>
          ) : null}
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
