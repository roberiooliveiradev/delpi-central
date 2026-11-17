import type { ReactNode } from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";

export type QuestionAnswerStackProps = {
  prefix?: string;
  className?: string;
  children?: ReactNode;
};

/**
 * Pilha da área de resposta do QuestionCard (R6): dentro do `fieldset`, os
 * filhos não-`legend` vivem num content box anônimo e o gap do cartão não se
 * aplica entre eles — esta pilha garante o ritmo 12 px / 14 px (≥ 600 px)
 * entre escala, legenda, linha da nota, N/A e campo.
 */
export function QuestionAnswerStack({
  prefix = "ds",
  className,
  children,
}: QuestionAnswerStackProps) {
  return (
    <div
      className={[
        delpiUiClass(
          `${prefix}-form-answer-stack`,
          "delpi-ui-form-answer-stack",
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
