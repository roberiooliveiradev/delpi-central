import {
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  presetDefaultTableOptions,
  tableElementPrimaryPartRef,
  type ComunicadoBlock,
  type ComunicadoTableOptions,
  type ComunicadoTableViewBlock,
  type TableElementId,
} from "@delpi/tv-dashboard-presentation";

import {
  applyTableAddElementChoice,
  type TableAddElementChoiceId,
} from "../content/tableAddElementMenuCatalog";
import { type TableStyleRecipe } from "../content/tableStyleRecipes";
import { ComplexSelectionFloatToolbar } from "./ComplexSelectionFloatToolbar";
import { TableAddElementMenu } from "./TableAddElementMenu";
import { TableDataMenu, type TableDataMenuActionId } from "./TableDataMenu";
import { TableStylesMenu } from "./TableStylesMenu";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  block: ComunicadoTableViewBlock;
};

/**
 * Float da tabela — + elementos, pincel estilos, funil dados (mesmos menus da ribbon).
 */
export function TableSelectionFloatToolbar({ block }: Props) {
  const { updateSelected, openDataPanel, selectTablePart, setSelectionPanelTab } =
    useComunicadoEditor();

  const options = mergeComunicadoTableOptions(block.tableOptions, block.tablePreset);

  const persistOptions = (nextOptions: ComunicadoTableOptions, preset = block.tablePreset) => {
    updateSelected({
      tableOptions: nextOptions,
      tablePreset: preset,
      tableParts: mergeTablePartsWithOptions(block.tableParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  const applyAddElementChoice = (choiceId: TableAddElementChoiceId) => {
    const patch = applyTableAddElementChoice(choiceId, options);
    const next = mergeComunicadoTableOptions({ ...options, ...patch }, block.tablePreset);
    persistOptions(next);
  };

  const openAddElementMoreOptions = (elementId: TableElementId) => {
    const part = tableElementPrimaryPartRef(elementId);
    if (part) selectTablePart(block.id, part);
    setSelectionPanelTab("element");
  };

  const applyRecipe = (recipe: TableStyleRecipe) => {
    const next = mergeComunicadoTableOptions(
      { ...options, ...recipe.options },
      recipe.preset,
    );
    persistOptions(next, recipe.preset);
  };

  const clearTableStyle = () => {
    persistOptions(presetDefaultTableOptions("grid"), "grid");
  };

  const openDataFocus = (actionId: TableDataMenuActionId) => {
    openDataPanel();
    setSelectionPanelTab("data");
    const anchorId =
      actionId === "columns" ? "td-view-table-columns" : "td-view-data-source";
    requestAnimationFrame(() => {
      document.getElementById(anchorId)?.scrollIntoView({ block: "nearest" });
    });
  };

  return (
    <ComplexSelectionFloatToolbar
      blockId={block.id}
      frame={block.frame}
      labels={{
        elements: "Elementos da tabela",
        style: "Estilos da tabela",
        data: "Dados da tabela",
      }}
      renderElements={(close) => (
        <TableAddElementMenu
          options={options}
          onApplyChoice={applyAddElementChoice}
          onMoreOptions={(elementId) => {
            openAddElementMoreOptions(elementId);
            close();
          }}
        />
      )}
      renderStyle={(close) => (
        <TableStylesMenu
          options={options}
          preset={block.tablePreset}
          onApplyRecipe={(recipe) => {
            applyRecipe(recipe);
            close();
          }}
          onClear={() => {
            clearTableStyle();
            close();
          }}
        />
      )}
      renderData={(close) => (
        <TableDataMenu
          onSelect={(actionId) => {
            openDataFocus(actionId);
            close();
          }}
        />
      )}
    />
  );
}
