import { ComunicadoChartRibbon } from "./ComunicadoChartRibbon";
import { ComunicadoDataRibbon } from "./ComunicadoDataRibbon";
import { ComunicadoElementRibbon } from "./ComunicadoElementRibbon";
import { ComunicadoInsertRibbon } from "./ComunicadoInsertRibbon";
import { ComunicadoViewRibbon } from "./ComunicadoViewRibbon";

type Labels = Record<string, string>;

type Props = {
  /** Camadas abre em modal no chrome — não renderiza na ribbon. */
  activeTab: "insert" | "element" | "data" | "view";
  labels?: Labels;
};

/** Conteúdo das faixas Inserir / Elemento·Dados / Exibir. */
export function ComunicadoRibbonContent({ activeTab, labels = {} }: Props) {
  if (activeTab === "insert") {
    return <ComunicadoInsertRibbon labels={labels} />;
  }
  if (activeTab === "view") {
    return <ComunicadoViewRibbon />;
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
