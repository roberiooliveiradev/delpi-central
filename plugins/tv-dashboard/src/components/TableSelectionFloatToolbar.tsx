import {
  TABLE_ELEMENT_CATALOG,
  isTableElementEnabled,
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  setTableElementEnabled,
  tableElementPrimaryPartRef,
  type ComunicadoBlock,
  type ComunicadoTableOptions,
  type ComunicadoTableViewBlock,
  type TableElementId,
} from "@delpi/tv-dashboard-presentation";

import {
  findTableStyleRecipe,
  resolveActiveTableStyleRecipeId,
  TABLE_STYLE_RECIPES,
} from "../content/tableStyleRecipes";
import { ComplexSelectionFloatToolbar } from "./ComplexSelectionFloatToolbar";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  block: ComunicadoTableViewBlock;
};

/**
 * Float da tabela — + elementos de estilo, pincel recipes, funil colunas/fonte.
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

  const toggleElement = (elementId: TableElementId, enabled: boolean) => {
    const patch = setTableElementEnabled(elementId, enabled);
    const next = mergeComunicadoTableOptions({ ...options, ...patch }, block.tablePreset);
    persistOptions(next);
    const part = tableElementPrimaryPartRef(elementId);
    if (part && enabled) selectTablePart(block.id, part);
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
      renderElements={() => (
        <div className="td-float-checklist" role="group" aria-label="Elementos da tabela">
          {TABLE_ELEMENT_CATALOG.map((element) => {
            const enabled = isTableElementEnabled(element.id, options);
            return (
              <button
                key={element.id}
                type="button"
                className={[
                  "td-deck-ribbon__cascade-item",
                  enabled ? "td-float-checklist__item--on" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                title={element.hint}
                onClick={() => toggleElement(element.id, !enabled)}
              >
                {enabled ? "✓ " : ""}
                {element.label}
              </button>
            );
          })}
        </div>
      )}
      renderStyle={(close) => (
        <div className="td-float-checklist" role="group" aria-label="Estilos da tabela">
          {TABLE_STYLE_RECIPES.slice(0, 8).map((recipe) => (
            <button
              key={recipe.id}
              type="button"
              className={[
                "td-deck-ribbon__cascade-item",
                activeStyleId === recipe.id ? "td-float-checklist__item--on" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => {
                applyRecipe(recipe.id);
                close();
              }}
            >
              {activeStyleId === recipe.id ? "✓ " : ""}
              {recipe.label}
            </button>
          ))}
        </div>
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
