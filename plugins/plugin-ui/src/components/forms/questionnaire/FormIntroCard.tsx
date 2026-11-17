import type { ReactNode } from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";
import { FormCard } from "./FormCard";

export type FormIntroCardContext = {
  label: ReactNode;
  value: ReactNode;
};

export type FormIntroCardItem = {
  icon: ReactNode;
  content: ReactNode;
};

export type FormIntroCardProps = {
  /** Já pronto (ex.: `FormLogo`). */
  logo: ReactNode;
  /** Ação à direita do logo (ex.: `FormThemeToggle`). */
  headerAction?: ReactNode;
  /** Rótulo pequeno em maiúsculas acima do título. */
  eyebrow?: ReactNode;
  title: ReactNode;
  /** Bloco suave (`--delpi-ui-form-tint`) com rótulo + valor; omitido se ausente. */
  context?: FormIntroCardContext;
  description?: ReactNode;
  /** Lista com ícone 18 px em `--delpi-ui-accent`. */
  items?: FormIntroCardItem[];
  /** Botão primário já pronto (ex.: `ActionButton`). */
  action: ReactNode;
  footnote?: ReactNode;
  prefix?: string;
  className?: string;
};

/**
 * Cartão de abertura do kit de formulário. Todo rótulo/texto entra por
 * propriedade — o componente não contém microcopy.
 */
export function FormIntroCard({
  logo,
  headerAction,
  eyebrow,
  title,
  context,
  description,
  items,
  action,
  footnote,
  prefix = "ds",
  className,
}: FormIntroCardProps) {
  const cn = (suffix: string) =>
    delpiUiClass(`${prefix}-form-intro${suffix}`, `delpi-ui-form-intro${suffix}`);

  const classes = [
    delpiUiClass(
      `${prefix}-form-card--intro`,
      "delpi-ui-form-card--intro",
    ),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <FormCard prefix={prefix} className={classes}>
      <div className={cn("__row")}>
        {logo}
        {headerAction}
      </div>
      <div className={cn("__head")}>
        {eyebrow != null && (
          <span
            className={delpiUiClass(
              `${prefix}-form-eyebrow`,
              "delpi-ui-form-eyebrow",
            )}
          >
            {eyebrow}
          </span>
        )}
        <h1 className={cn("__title")}>{title}</h1>
      </div>
      {context && (
        <div className={cn("__context")}>
          <span className={cn("__context-label")}>{context.label}</span>
          <strong className={cn("__context-value")}>{context.value}</strong>
        </div>
      )}
      {description != null && (
        <p className={cn("__description")}>{description}</p>
      )}
      {items != null && items.length > 0 && (
        <ul className={cn("__items")}>
          {items.map((item, index) => (
            <li key={index} className={cn("__item")}>
              <span className={cn("__item-icon")} aria-hidden="true">
                {item.icon}
              </span>
              <span className={cn("__item-content")}>{item.content}</span>
            </li>
          ))}
        </ul>
      )}
      {action}
      {footnote != null && <p className={cn("__footnote")}>{footnote}</p>}
    </FormCard>
  );
}
