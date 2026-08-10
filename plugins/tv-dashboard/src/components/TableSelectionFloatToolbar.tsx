import {
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  presetDefaultTableOptions,
  tableElementPrimaryPartRef,
  clearTablePartThemePaint,
  type ComunicadoBlock,
  type ComunicadoTableOptions,
  type ComunicadoTableViewBlock,
  type TableElementId,
} from "@delpi/tv-dashboard-presentation";
import { useState } from "react";

import {
  applyTableAddElementChoice,
  type TableAddElementChoiceId,
} from "../content/tableAddElementMenuCatalog";
import { type TableStyleRecipe, buildTableStyleRecipeApplication } from "../content/tableStyleRecipes";
import { ComplexSelectionFloatToolbar } from "./ComplexSelectionFloatToolbar";
import { TableAddElementMenu } from "./TableAddElementMenu";
import { TableColumnsSelectModal } from "./TableColumnsSelectModal";
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
  const [columnsModalOpen, setColumnsModalOpen] = useState(false);

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
    const applied = buildTableStyleRecipeApplication({
      currentOptions: block.tableOptions,
      currentParts: block.tableParts,
      recipe,
    });
    updateSelected({
      tableOptions: applied.tableOptions,
      tableParts: applied.tableParts,
      tablePreset: applied.tablePreset,
    } as Partial<ComunicadoBlock>);
  };

  const clearTableStyle = () => {
    const defaults = presetDefaultTableOptions("grid");
    updateSelected({
      tableOptions: defaults,
      tablePreset: "grid",
      tableParts: mergeTablePartsWithOptions(
        clearTablePartThemePaint(block.tableParts),
        defaults,
      ),
    } as Partial<ComunicadoBlock>);
  };

  const openDataFocus = (actionId: TableDataMenuActionId) => {
    if (actionId === "columns") {
      setColumnsModalOpen(true);
      return;
    }
    openDataPanel();
    setSelectionPanelTab("data");
    requestAnimationFrame(() => {
      document.getElementById("td-view-data-source")?.scrollIntoView({ block: "nearest" });
    });
  };

  return (
    <>
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
      <TableColumnsSelectModal
        open={columnsModalOpen}
        onClose={() => setColumnsModalOpen(false)}
        block={block}
      />
    </>
  );
}
