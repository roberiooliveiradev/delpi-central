import type {
  ComponentPropsWithoutRef,
  ElementType,
  ReactNode,
} from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";

export type FormCardTone = "default" | "invalid";

export type FormCardProps = {
  /** Elemento raiz — `fieldset` para o `QuestionCard`. */
  as?: "div" | "section" | "fieldset";
  /** `invalid` aplica a borda de erro (`--delpi-ui-danger`). */
  tone?: FormCardTone;
  /** Prefixo BEM do consumidor (dual-class). */
  prefix?: string;
  className?: string;
  children?: ReactNode;
} & Omit<ComponentPropsWithoutRef<"div">, "as" | "className" | "children">;

/**
 * Cartão base do kit de formulário: superfície, borda (obrigatória no tema
 * escuro), raio 12, sombra e padding responsivo. Não substitui `SectionCard`.
 */
export function FormCard({
  as = "div",
  tone = "default",
  prefix = "ds",
  className,
  children,
  ...rest
}: FormCardProps) {
  const Component = as as ElementType;
  const classes = [
    delpiUiClass(`${prefix}-form-card`, "delpi-ui-form-card"),
    tone === "invalid" &&
      delpiUiClass(
        `${prefix}-form-card--tone-invalid`,
        "delpi-ui-form-card--tone-invalid",
      ),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <Component className={classes} {...rest}>
      {children}
    </Component>
  );
}
