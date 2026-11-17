import { Moon, Sun } from "lucide-react";

import { delpiUiClass } from "../../../utils/delpiUiClass";
import { useQuestionnaireColorScheme } from "./QuestionnaireThemeScope";

export type FormThemeToggleProps = {
  /** Nome acessível do botão (obrigatório — texto do consumidor). */
  ariaLabel: string;
  prefix?: string;
  className?: string;
};

/**
 * Botão redondo 44×44 que alterna o tema do `QuestionnaireThemeScope` mais
 * próximo (lua no claro, sol no escuro). Não renderiza quando o escopo tem
 * esquema fixo (`canToggle === false`).
 */
export function FormThemeToggle({
  ariaLabel,
  prefix = "ds",
  className,
}: FormThemeToggleProps) {
  const { scheme, toggle, canToggle } = useQuestionnaireColorScheme();

  if (!canToggle) {
    return null;
  }

  const Icon = scheme === "dark" ? Sun : Moon;
  const classes = [
    delpiUiClass(
      `${prefix}-form-theme-toggle`,
      "delpi-ui-form-theme-toggle",
    ),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      type="button"
      className={classes}
      aria-label={ariaLabel}
      aria-pressed={scheme === "dark"}
      onClick={toggle}
    >
      <Icon size={20} aria-hidden="true" />
    </button>
  );
}
