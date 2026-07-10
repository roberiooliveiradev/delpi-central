import { ComunicadoFormatRibbon } from "./ComunicadoFormatRibbon";
import { ComunicadoInsertRibbon } from "./ComunicadoInsertRibbon";
import { ComunicadoViewRibbon } from "./ComunicadoViewRibbon";

type Labels = Record<string, string>;

type Props = {
  activeTab: "insert" | "format" | "view";
  labels?: Labels;
};

/** Conteúdo compartilhado das faixas Inserir / Formatar / Exibir (deck + modal embutido). */
export function ComunicadoRibbonContent({ activeTab, labels = {} }: Props) {
  if (activeTab === "insert") {
    return <ComunicadoInsertRibbon labels={labels} />;
  }
  if (activeTab === "view") {
    return <ComunicadoViewRibbon />;
  }
  return <ComunicadoFormatRibbon labels={labels} />;
}
