import { ComunicadoChartRibbon } from "./ComunicadoChartRibbon";
import { ComunicadoFormatRibbon } from "./ComunicadoFormatRibbon";
import { ComunicadoInsertRibbon } from "./ComunicadoInsertRibbon";
import { ComunicadoShapeRibbon } from "./ComunicadoShapeRibbon";
import { ComunicadoViewRibbon } from "./ComunicadoViewRibbon";

type Labels = Record<string, string>;

type Props = {
  activeTab: "insert" | "format" | "chart" | "shape" | "view";
  labels?: Labels;
};

/** Conteúdo compartilhado das faixas Inserir / Formatar / Gráfico / Forma / Exibir. */
export function ComunicadoRibbonContent({ activeTab, labels = {} }: Props) {
  if (activeTab === "insert") {
    return <ComunicadoInsertRibbon labels={labels} />;
  }
  if (activeTab === "view") {
    return <ComunicadoViewRibbon />;
  }
  if (activeTab === "chart") {
    return <ComunicadoChartRibbon />;
  }
  if (activeTab === "shape") {
    return <ComunicadoShapeRibbon />;
  }
  return <ComunicadoFormatRibbon labels={labels} />;
}
