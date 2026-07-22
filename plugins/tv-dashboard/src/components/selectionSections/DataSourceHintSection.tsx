import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

/** Fonte de dados: atalho para a aba Dados (conteúdo completo fica lá). */
export function DataSourceHintSection({ layout }: { layout: SelectionSectionLayout }) {
  const { openDataPanel, selected } = useComunicadoEditor();
  const title =
    selected && "title" in selected && typeof selected.title === "string"
      ? selected.title
      : "Fonte de dados";

  const body = (
    <div className="td-selection-section__data-hint">
      <p className="td-subtitle">{title}</p>
      <button type="button" className="td-btn td-btn--sm" onClick={() => openDataPanel()}>
        Abrir Dados
      </button>
    </div>
  );

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Elementos" defaultOpen>
        {body}
      </SelectionPaneSection>
    );
  }

  return <DeckRibbonGroup groupId="data-source-hint" label="Fonte de dados">{body}</DeckRibbonGroup>;
}
