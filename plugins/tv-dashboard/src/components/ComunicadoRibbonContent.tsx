import { ComunicadoChartRibbon } from "./ComunicadoChartRibbon";
import { ComunicadoDataRibbon } from "./ComunicadoDataRibbon";
import { ComunicadoElementRibbon } from "./ComunicadoElementRibbon";
import { ComunicadoInsertRibbon } from "./ComunicadoInsertRibbon";
import { ComunicadoTableDesignRibbon } from "./ComunicadoTableDesignRibbon";
import { ComunicadoTableLayoutRibbon } from "./ComunicadoTableLayoutRibbon";
import { ComunicadoViewRibbon } from "./ComunicadoViewRibbon";

type Labels = Record<string, string>;

export type ComunicadoRibbonContentTab =
  | "insert"
  | "element"
  | "tableDesign"
  | "tableLayout"
  | "data"
  | "view";

type Props = {
  /** Camadas abre o painel lateral — não renderiza faixa de conteúdo. */
  activeTab: ComunicadoRibbonContentTab;
  labels?: Labels;
};

/** Conteúdo das faixas Inserir / Elemento·Tabela·Dados / Exibir. */
export function ComunicadoRibbonContent({ activeTab, labels = {} }: Props) {
  if (activeTab === "insert") {
    return <ComunicadoInsertRibbon labels={labels} />;
  }
  if (activeTab === "view") {
    return <ComunicadoViewRibbon />;
  }
  if (activeTab === "tableDesign") {
    return <ComunicadoTableDesignRibbon />;
  }
  if (activeTab === "tableLayout") {
    return <ComunicadoTableLayoutRibbon />;
  }
  if (activeTab === "element") {
    return <ComunicadoElementRibbon />;
  }
  if (activeTab === "data") {
    return <ComunicadoDataRibbon />;
  }
  return null;
}

/** @deprecated — reexport para imports legados de testes. */
export { ComunicadoChartRibbon };
