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

const FORMAT_CYCLE: Array<NonNullable<ComunicadoKpiOptions["valueFormat"]>> = [
  "number",
  "percent",
  "currency",
  "compact",
  "raw",
];

/** Painel pincel do KPI — tons, presets e atalho a regras de cor. */
export function KpiColorsStylesMenu({ options, onApplyOptions, footer }: Props) {
  const formatLabel =
    options.valueFormat === "percent"
      ? "Percentual"
      : options.valueFormat === "currency"
        ? "Moeda"
        : options.valueFormat === "number"
          ? "Número"
          : options.valueFormat === "compact"
            ? "Compacto"
            : "Como veio";

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

      <section className="td-chart-style-menu__section">
        <h4>Formato do valor</h4>
        <button
          type="button"
          className="td-chart-style-menu__style"
          onClick={() => {
            const current = options.valueFormat ?? "number";
            const idx = FORMAT_CYCLE.indexOf(current);
            const next = FORMAT_CYCLE[(idx + 1) % FORMAT_CYCLE.length] ?? "number";
            onApplyOptions({ ...options, valueFormat: next });
          }}
        >
          Formato: {formatLabel}
        </button>
      </section>

      {footer}
    </div>
  );
}
