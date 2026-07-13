import type { ReactNode } from "react";
import type { ComunicadoChartOptions } from "@delpi/tv-dashboard-presentation";

import {
  CHART_COLOR_PALETTES,
  CHART_STYLE_RECIPES,
  applyChartColorPalette,
  applyChartStyleRecipe,
  isChartStyleRecipeActive,
  type ChartColorPalette,
  type ChartStyleRecipe,
} from "../content/chartStyleRecipes";

type Props = {
  options: ComunicadoChartOptions;
  onApplyOptions: (next: ComunicadoChartOptions) => void;
  /** Ações extras (ex.: legenda) dentro do mesmo chrome do menu. */
  footer?: ReactNode;
};

/** Painel compartilhado Alterar Cores / Estilos (ribbon + float pincel). */
export function ChartColorsStylesMenu({ options, onApplyOptions, footer }: Props) {
  const applyPalette = (palette: ChartColorPalette) => {
    onApplyOptions(applyChartColorPalette(palette, options));
  };
  const applyStyle = (recipe: ChartStyleRecipe) => {
    onApplyOptions(applyChartStyleRecipe(recipe, options));
  };

  return (
    <div className="td-chart-style-menu" role="menu" aria-label="Cores e estilos do gráfico">
      <section className="td-chart-style-menu__section">
        <h4>Alterar cores</h4>
        <p className="td-chart-style-menu__hint">
          Uma série usa a cor principal; pies e categorias usam as demais do swatch.
        </p>
        <div className="td-chart-style-menu__palettes">
          {CHART_COLOR_PALETTES.map((palette) => (
            <button
              key={palette.id}
              type="button"
              className={[
                "td-chart-style-menu__palette",
                options.seriesColor === palette.seriesColor
                  ? "td-chart-style-menu__palette--active"
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
              title={palette.label}
              aria-label={palette.label}
              onClick={() => applyPalette(palette)}
            >
              <span className="td-chart-style-menu__swatches" aria-hidden="true">
                {palette.colors.map((color) => (
                  <span key={color} style={{ background: color }} />
                ))}
              </span>
              <span className="td-chart-style-menu__palette-label">{palette.label}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="td-chart-style-menu__section">
        <h4>Estilos de gráfico</h4>
        <div className="td-chart-style-menu__styles">
          {CHART_STYLE_RECIPES.map((recipe) => {
            const active = isChartStyleRecipeActive(recipe, options);
            return (
              <button
                key={recipe.id}
                type="button"
                className={[
                  "td-chart-style-menu__style",
                  active ? "td-chart-style-menu__style--active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                title={recipe.label}
                aria-pressed={active}
                onClick={() => applyStyle(recipe)}
              >
                <span
                  className={`td-chart-style-menu__style-thumb td-chart-style-menu__style-thumb--${recipe.id}`}
                  aria-hidden="true"
                />
                <span>{recipe.label}</span>
              </button>
            );
          })}
        </div>
      </section>

      {footer ? <div className="td-chart-style-menu__footer">{footer}</div> : null}
    </div>
  );
}
