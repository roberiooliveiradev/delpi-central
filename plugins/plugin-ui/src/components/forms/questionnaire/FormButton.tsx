import type { ReactNode } from "react";

import { ActionButton } from "../../actions/ActionButton";
import { delpiUiClass } from "../../../utils/delpiUiClass";

export type FormButtonVariant = "primary" | "secondary";

export type FormButtonProps = {
  variant?: FormButtonVariant;
  /** Substitui o rótulo por `busyLabel` e desabilita mantendo o foco. */
  busy?: boolean;
  busyLabel?: ReactNode;
  fullWidth?: boolean;
  type?: "button" | "submit";
  onClick?: () => void;
  children: ReactNode;
  /** Prefixo BEM do consumidor (dual-class). */
  prefix?: string;
  className?: string;
};

/**
 * Botão do kit de formulário sobre o `ActionButton` existente (não alterado):
 * `secondary` mapeia para a variante `default`; `busy` usa `disabled` +
 * `softDisabled` (aria-disabled + guarda de clique — o foco não é perdido
 * durante o envio). O visual vem de `questionnaire.css` com seletores
 * escopados em `.delpi-ui-form-root` — especificidade, nunca ordem de
 * `@import` nem `!important`.
 */
export function FormButton({
  variant = "primary",
  busy = false,
  busyLabel,
  fullWidth = false,
  type = "button",
  onClick,
  children,
  prefix = "ds",
  className,
}: FormButtonProps) {
  const rootClass = [
    delpiUiClass(`${prefix}-form-button`, "delpi-ui-form-button"),
    variant === "primary" &&
      delpiUiClass(
        `${prefix}-form-button--primary`,
        "delpi-ui-form-button--primary",
      ),
    variant === "secondary" &&
      delpiUiClass(
        `${prefix}-form-button--secondary`,
        "delpi-ui-form-button--secondary",
      ),
    fullWidth &&
      delpiUiClass(
        `${prefix}-form-button--full`,
        "delpi-ui-form-button--full",
      ),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <ActionButton
      variant={variant === "primary" ? "primary" : "default"}
      type={type}
      onClick={onClick}
      disabled={busy}
      softDisabled
      className={rootClass}
    >
      {busy ? busyLabel ?? children : children}
    </ActionButton>
  );
}
