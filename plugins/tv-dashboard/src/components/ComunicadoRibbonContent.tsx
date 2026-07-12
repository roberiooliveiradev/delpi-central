import { ComunicadoChartRibbon } from "./ComunicadoChartRibbon";
import { ComunicadoDataRibbon } from "./ComunicadoDataRibbon";
import { ComunicadoFormatRibbon } from "./ComunicadoFormatRibbon";
import { ComunicadoInsertRibbon } from "./ComunicadoInsertRibbon";
import { ComunicadoShapeRibbon } from "./ComunicadoShapeRibbon";
import { ComunicadoTableRibbon } from "./ComunicadoTableRibbon";
import { ComunicadoViewRibbon } from "./ComunicadoViewRibbon";

type Labels = Record<string, string>;

type Props = {
  activeTab: "insert" | "format" | "chart" | "table" | "shape" | "data" | "view";
  labels?: Labels;
};

/** Conteúdo compartilhado das faixas Inserir / Formatar / contextuais / Exibir. */
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
  if (activeTab === "table") {
    return <ComunicadoTableRibbon />;
  }
  if (activeTab === "shape") {
    return <ComunicadoShapeRibbon />;
  }
  if (activeTab === "data") {
    return <ComunicadoDataRibbon />;
  }
  return <ComunicadoFormatRibbon labels={labels} />;
}
