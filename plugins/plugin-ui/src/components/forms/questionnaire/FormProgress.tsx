import type { ReactNode } from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";

export type FormProgressProps = {
  done: number;
  total: number;
  /** Nome acessível da barra (obrigatório — texto do consumidor). */
  ariaLabel: string;
  /**
   * Rótulo visível opcional (ex.: "3 de 12"). No `FormHeaderCard` o texto do
   * progresso fica na linha da etapa e não é repetido aqui.
   */
  label?: ReactNode;
  prefix?: string;
  className?: string;
};

/**
 * Barra de progresso do kit: trilho 6 px raio 3 (`--delpi-ui-form-track`)
 * com preenchimento `--delpi-ui-accent`. `aria-valuenow` é
 * `round(100 × done ÷ total)` — `0` quando `total` é `0`.
 */
export function FormProgress({
  done,
  total,
  ariaLabel,
  label,
  prefix = "ds",
  className,
}: FormProgressProps) {
  const percent =
    total > 0
      ? Math.min(100, Math.max(0, Math.round((100 * done) / total)))
      : 0;

  const classes = [
    delpiUiClass(`${prefix}-form-progress`, "delpi-ui-form-progress"),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes}>
      {label != null && (
        <span
          className={delpiUiClass(
            `${prefix}-form-progress__label`,
            "delpi-ui-form-progress__label",
          )}
        >
          {label}
        </span>
      )}
      <div
        className={delpiUiClass(
          `${prefix}-form-progress__track`,
          "delpi-ui-form-progress__track",
        )}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        aria-label={ariaLabel}
      >
        <div
          className={delpiUiClass(
            `${prefix}-form-progress__fill`,
            "delpi-ui-form-progress__fill",
          )}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
