import type { ReactNode } from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";

export type FormNoticeTone = "warning" | "info";

export type FormNoticeProps = {
  tone?: FormNoticeTone;
  children: ReactNode;
  /** Prefixo BEM do consumidor (dual-class). */
  prefix?: string;
  className?: string;
};

/**
 * Aviso em bloco do formulário (`role="note"`): warning usa os tokens
 * `--delpi-ui-form-warning-*`; info usa tint + accent-text. Conteúdo livre
 * por `children`.
 */
export function FormNotice({
  tone = "warning",
  children,
  prefix = "ds",
  className,
}: FormNoticeProps) {
  return (
    <div
      role="note"
      className={[
        delpiUiClass(`${prefix}-form-notice`, "delpi-ui-form-notice"),
        delpiUiClass(
          `${prefix}-form-notice--${tone}`,
          `delpi-ui-form-notice--${tone}`,
        ),
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </div>
  );
}
