import { Database, Link2, Plus } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/**
 * Faixa contextual «Dados» — atalhos para configurar a fonte do elemento
 * ou abrir o catálogo para inserir nova fonte.
 */
export function ComunicadoDataRibbon() {
  const { openDataPanel, openDataCatalog } = useComunicadoEditor();

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Fonte" hint={H.chartData ?? "Configuração e catálogo de fontes."}>
        <DeckRibbonTile
          icon={Link2}
          label="Configurar"
          hint="Abre o painel lateral com a fonte e parâmetros do elemento selecionado."
          onClick={() => openDataPanel()}
        />
        <DeckRibbonTile
          icon={Plus}
          label="Nova fonte"
          hint="Abre o catálogo para inserir uma nova fonte de dados no slide."
          onClick={() => openDataCatalog()}
        />
        <DeckRibbonTile
          icon={Database}
          label="Painel Dados"
          hint="Abre a aba Dados do painel lateral."
          onClick={() => openDataPanel()}
        />
      </DeckRibbonGroup>
    </div>
  );
}
