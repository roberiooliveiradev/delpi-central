import type { ReactNode } from "react";
import type { ComunicadoTableOptions, ComunicadoTablePreset } from "@delpi/tv-dashboard-presentation";

import {
  resolveActiveTableStyleRecipeId,
  tableStyleRecipesByCategory,
  type TableStyleRecipe,
} from "../content/tableStyleRecipes";

type Props = {
  options: ComunicadoTableOptions;
  preset?: ComunicadoTablePreset | null;
  onApplyRecipe: (recipe: TableStyleRecipe) => void;
  onClear?: () => void;
  footer?: ReactNode;
};

const CATEGORY_LABELS: Record<TableStyleRecipe["category"], string> = {
  light: "Claros",
  medium: "Médios",
  dark: "Escuros",
};

/**
 * Painel compartilhado de estilos da tabela (ribbon «Alterar estilos» + float pincel).
 * Paridade visual com ChartColorsStylesMenu.
 */
export function TableStylesMenu({
  options,
  preset,
  onApplyRecipe,
  onClear,
  footer,
}: Props) {
  const activeId = resolveActiveTableStyleRecipeId(options, preset ?? "grid");

  return (
    <div className="td-chart-style-menu" role="menu" aria-label="Estilos da tabela">
      {(["light", "medium", "dark"] as const).map((category) => {
        const recipes = tableStyleRecipesByCategory(category);
        if (recipes.length === 0) return null;
        return (
          <section key={category} className="td-chart-style-menu__section">
            <h4>{CATEGORY_LABELS[category]}</h4>
            <div className="td-chart-style-menu__styles">
              {recipes.map((recipe) => {
                const active = activeId === recipe.id;
                const headerBg = recipe.options.headerBg ?? "#e2e8f0";
                const cellBg = recipe.options.cellBg ?? "#ffffff";
                const borderColor = recipe.options.borderColor ?? "#cbd5e1";
                return (
                  <button
                    key={recipe.id}
                    type="button"
                    role="menuitemradio"
                    aria-checked={active}
                    className={[
                      "td-chart-style-menu__style",
                      active ? "td-chart-style-menu__style--active" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    title={recipe.label}
                    onClick={() => onApplyRecipe(recipe)}
                  >
                    <span
                      className="td-chart-style-menu__style-thumb td-table-style-menu__thumb"
                      aria-hidden="true"
                      style={{
                        background: `linear-gradient(180deg, ${headerBg} 38%, ${cellBg} 38%)`,
                        boxShadow: `inset 0 0 0 1px ${borderColor}`,
                      }}
                    />
                    <span>{recipe.label}</span>
                  </button>
                );
              })}
            </div>
          </section>
        );
      })}

      {onClear ? (
        <div className="td-chart-style-menu__footer">
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={onClear}
          >
            Limpar estilo
          </button>
        </div>
      ) : null}

      {footer ? <div className="td-chart-style-menu__footer">{footer}</div> : null}
    </div>
  );
}
