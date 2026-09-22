import type { ReactNode } from "react";
import type { ComunicadoKpiOptions } from "@delpi/tv-dashboard-presentation";

import {
  KPI_APPEARANCE_RECIPES,
  KPI_TONE_OPTIONS,
  applyKpiAppearanceRecipe,
  applyKpiTone,
  isKpiAppearanceRecipeActive,
  isKpiToneActive,
} from "../content/kpiStyleRecipes";

type Props = {
  options: ComunicadoKpiOptions;
  onApplyOptions: (next: ComunicadoKpiOptions) => void;
  footer?: ReactNode;
};

/** Painel pincel do KPI — tema + tom (formato fica no grupo Número). */
export function KpiColorsStylesMenu({ options, onApplyOptions, footer }: Props) {
  return (
    <div className="td-chart-style-menu" role="menu" aria-label="Cores e estilos do KPI">
      <section className="td-chart-style-menu__section">
        <h4>Estilos de aparência</h4>
        <p className="td-chart-style-menu__hint">Tema do card (fundo e contraste).</p>
        <div className="td-chart-style-menu__styles">
          {KPI_APPEARANCE_RECIPES.map((recipe) => {
            const active = isKpiAppearanceRecipeActive(recipe, options);
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
                aria-label={recipe.label}
                aria-pressed={active}
                onClick={() => onApplyOptions(applyKpiAppearanceRecipe(recipe, options))}
              >
                <span
                  className={`td-chart-style-menu__style-thumb td-chart-style-menu__style-thumb--kpi-${recipe.id}`}
                  aria-hidden="true"
                />
                <span>{recipe.label}</span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="td-chart-style-menu__section">
        <h4>Tom</h4>
        <p className="td-chart-style-menu__hint">Cor semântica do valor e do ícone.</p>
        <div className="td-chart-style-menu__styles">
          {KPI_TONE_OPTIONS.map((tone) => {
            const active = isKpiToneActive(tone, options);
            return (
              <button
                key={tone.id}
                type="button"
                className={[
                  "td-chart-style-menu__style",
                  active ? "td-chart-style-menu__style--active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                title={tone.label}
                aria-label={tone.label}
                aria-pressed={active}
                onClick={() => onApplyOptions(applyKpiTone(tone, options))}
              >
                <span
                  className={`td-chart-style-menu__style-thumb td-chart-style-menu__style-thumb--kpi-tone-${tone.id}`}
                  aria-hidden="true"
                />
                <span>{tone.label}</span>
              </button>
            );
          })}
        </div>
      </section>

      {footer ? <div className="td-chart-style-menu__footer">{footer}</div> : null}
    </div>
  );
}
