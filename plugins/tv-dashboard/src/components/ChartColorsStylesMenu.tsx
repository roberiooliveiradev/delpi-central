import type { ReactNode } from "react";
import type { ComunicadoChartOptions } from "@delpi/tv-dashboard-presentation";

import {
  CHART_STYLE_RECIPES,
  applyChartColorPalette,
  applyChartColorScaleMode,
  applyChartColorScalePolarity,
  applyChartStyleRecipe,
  chartPalettesByKind,
  isChartColorPaletteActive,
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

function PaletteGrid({
  palettes,
  options,
  onApply,
}: {
  palettes: ChartColorPalette[];
  options: ComunicadoChartOptions;
  onApply: (palette: ChartColorPalette) => void;
}) {
  return (
    <div className="td-chart-style-menu__palettes">
      {palettes.map((palette) => {
        const active = isChartColorPaletteActive(palette, options);
        return (
          <button
            key={palette.id}
            type="button"
            className={[
              "td-chart-style-menu__palette",
              active ? "td-chart-style-menu__palette--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            title={palette.hint ? `${palette.label} — ${palette.hint}` : palette.label}
            aria-label={palette.label}
            onClick={() => onApply(palette)}
          >
            <span className="td-chart-style-menu__swatches" aria-hidden="true">
              {palette.colors.map((color) => (
                <span key={`${palette.id}-${color}`} style={{ background: color }} />
              ))}
            </span>
            <span className="td-chart-style-menu__palette-label">{palette.label}</span>
          </button>
        );
      })}
    </div>
  );
}

/** Painel compartilhado Alterar Cores / Estilos (ribbon + float pincel). */
export function ChartColorsStylesMenu({ options, onApplyOptions, footer }: Props) {
  const categorical = chartPalettesByKind("categorical");
  const semantic = chartPalettesByKind("semantic");
  const colorByValue = options.colorScale?.mode === "by_value";
  const polarity = options.colorScale?.polarity ?? "high_is_bad";

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
        <p className="td-chart-style-menu__hint">Série = 1ª cor; categorias usam o swatch.</p>
        <PaletteGrid palettes={categorical} options={options} onApply={applyPalette} />
      </section>

      <section className="td-chart-style-menu__section">
        <h4>Escalas (melhor / pior)</h4>
        <p className="td-chart-style-menu__hint">
          Pelo valor: rampa no número. Sem isso: ordem das categorias.
        </p>
        <PaletteGrid palettes={semantic} options={options} onApply={applyPalette} />
        <div className="td-chart-style-menu__scale-controls">
          <label className="td-chart-style-menu__scale-toggle">
            <input
              type="checkbox"
              checked={colorByValue}
              onChange={(event) => {
                onApplyOptions(
                  applyChartColorScaleMode(
                    options,
                    event.target.checked ? "by_value" : "off",
                    polarity,
                  ),
                );
              }}
            />
            <span>Colorir pelo valor</span>
          </label>
          <div
            className="td-chart-style-menu__polarity"
            role="group"
            aria-label="Polaridade da escala"
          >
            <button
              type="button"
              className={[
                "td-chart-style-menu__polarity-btn",
                polarity === "high_is_bad" ? "td-chart-style-menu__polarity-btn--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              aria-pressed={polarity === "high_is_bad"}
              disabled={!colorByValue}
              onClick={() =>
                onApplyOptions(applyChartColorScalePolarity(options, "high_is_bad"))
              }
            >
              Alto = pior
            </button>
            <button
              type="button"
              className={[
                "td-chart-style-menu__polarity-btn",
                polarity === "high_is_good" ? "td-chart-style-menu__polarity-btn--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              aria-pressed={polarity === "high_is_good"}
              disabled={!colorByValue}
              onClick={() =>
                onApplyOptions(applyChartColorScalePolarity(options, "high_is_good"))
              }
            >
              Alto = melhor
            </button>
          </div>
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
