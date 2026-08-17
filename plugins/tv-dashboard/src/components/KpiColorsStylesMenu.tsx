import type { ReactNode } from "react";
import type { ComunicadoKpiOptions } from "@delpi/tv-dashboard-presentation";

import {
  KPI_APPEARANCE_RECIPES,
  applyKpiAppearanceRecipe,
  isKpiAppearanceRecipeActive,
} from "../content/kpiStyleRecipes";

type Props = {
  options: ComunicadoKpiOptions;
  onApplyOptions: (next: ComunicadoKpiOptions) => void;
  footer?: ReactNode;
};

const TONE_OPTIONS: Array<{ value: NonNullable<ComunicadoKpiOptions["tone"]>; label: string }> = [
  { value: "default", label: "Tom padrão" },
  { value: "positive", label: "Tom positivo" },
  { value: "negative", label: "Tom negativo" },
  { value: "warning", label: "Tom atenção" },
];

/** Painel pincel do KPI — tons e presets (formato fica no grupo Número). */
export function KpiColorsStylesMenu({ options, onApplyOptions, footer }: Props) {
  return (
    <div className="td-chart-style-menu" role="menu" aria-label="Cores e estilos do KPI">
      <section className="td-chart-style-menu__section">
        <h4>Estilos de aparência</h4>
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
                onClick={() => onApplyOptions(applyKpiAppearanceRecipe(recipe, options))}
              >
                {recipe.label}
              </button>
            );
          })}
        </div>
      </section>

      <section className="td-chart-style-menu__section">
        <h4>Tom</h4>
        <div className="td-chart-style-menu__styles">
          {TONE_OPTIONS.map((tone) => (
            <button
              key={tone.value}
              type="button"
              className={[
                "td-chart-style-menu__style",
                (options.tone ?? "default") === tone.value
                  ? "td-chart-style-menu__style--active"
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => onApplyOptions({ ...options, tone: tone.value })}
            >
              {tone.label}
            </button>
          ))}
        </div>
      </section>

      {footer}
    </div>
  );
}
