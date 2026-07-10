import { ComunicadoFormatRibbon } from "./ComunicadoFormatRibbon";
import { ComunicadoInsertRibbon } from "./ComunicadoInsertRibbon";

type Labels = Record<string, string>;

type Props = {
  activeTab: "insert" | "format";
  labels?: Labels;
};

/** Conteúdo compartilhado das faixas Inserir / Formatar (deck + modal embutido). */
export function ComunicadoRibbonContent({ activeTab, labels = {} }: Props) {
  if (activeTab === "insert") {
    return <ComunicadoInsertRibbon labels={labels} />;
  }
  return <ComunicadoFormatRibbon labels={labels} />;
}
