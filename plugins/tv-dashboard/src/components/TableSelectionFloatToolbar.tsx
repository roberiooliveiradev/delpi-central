import {
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
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
import {
  findTableStyleRecipe,
  resolveActiveTableStyleRecipeId,
  TABLE_STYLE_RECIPES,
} from "../content/tableStyleRecipes";
import { ComplexSelectionFloatToolbar } from "./ComplexSelectionFloatToolbar";
import { FloatChecklist, FloatChecklistItem } from "./FloatChecklist";
import { TableAddElementMenu } from "./TableAddElementMenu";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  block: ComunicadoTableViewBlock;
};

/**
 * Float da tabela — + elementos (flyouts), pincel recipes, funil colunas/fonte.
 */
export function TableSelectionFloatToolbar({ block }: Props) {
  const { updateSelected, openDataPanel, selectTablePart, setSelectionPanelTab } =
    useComunicadoEditor();

  const options = mergeComunicadoTableOptions(block.tableOptions, block.tablePreset);
  const activeStyleId = resolveActiveTableStyleRecipeId(options, block.tablePreset ?? "grid");

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

  const applyRecipe = (recipeId: string) => {
    const recipe = findTableStyleRecipe(recipeId);
    if (!recipe) return;
    const next = mergeComunicadoTableOptions(
      { ...options, ...recipe.options },
      recipe.preset,
    );
    persistOptions(next, recipe.preset);
  };

  const openDataFocus = (anchorId?: string) => {
    openDataPanel();
    setSelectionPanelTab("data");
    if (anchorId) {
      requestAnimationFrame(() => {
        document.getElementById(anchorId)?.scrollIntoView({ block: "nearest" });
      });
    }
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
        <FloatChecklist aria-label="Estilos da tabela">
          {TABLE_STYLE_RECIPES.slice(0, 8).map((recipe) => (
            <FloatChecklistItem
              key={recipe.id}
              label={recipe.label}
              active={activeStyleId === recipe.id}
              onClick={() => {
                applyRecipe(recipe.id);
                close();
              }}
            />
          ))}
        </FloatChecklist>
      )}
      renderData={(close) => (
        <>
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={() => {
              openDataFocus("td-view-data-source");
              close();
            }}
          >
            Selecionar fonte…
          </button>
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={() => {
              openDataFocus("td-view-table-columns");
              close();
            }}
          >
            Colunas do visual…
          </button>
        </>
      )}
    />
  );
}
