import { ComunicadoChartRibbon } from "./ComunicadoChartRibbon";
import { ComunicadoDataRibbon } from "./ComunicadoDataRibbon";
import { ComunicadoElementRibbon } from "./ComunicadoElementRibbon";
import { ComunicadoInsertRibbon } from "./ComunicadoInsertRibbon";
import { ComunicadoLayersRibbon } from "./ComunicadoLayersRibbon";
import { ComunicadoViewRibbon } from "./ComunicadoViewRibbon";

type Labels = Record<string, string>;

type Props = {
  activeTab: "insert" | "element" | "data" | "layers" | "view";
  labels?: Labels;
};

/** Conteúdo das faixas Inserir / Elemento·Dados·Camadas / Exibir. */
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
  if (activeTab === "layers") {
    return <ComunicadoLayersRibbon />;
  }
  return null;
}

/** @deprecated — reexport para imports legados de testes. */
export { ComunicadoChartRibbon };
