import { useId, type ReactNode } from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";
import { FormCard } from "./FormCard";

export type QuestionCardProps = {
  /** Rótulo do tema em maiúsculas (ex.: "Qualidade"). */
  eyebrow?: ReactNode;
  /** Número da pergunta (renderizado como "{n}. " antes do enunciado). */
  number?: ReactNode;
  prompt: ReactNode;
  /** Exibe asterisco em `--delpi-ui-danger` (aria-hidden). */
  required?: boolean;
  /** Texto acessível da obrigatoriedade (sr-only), ex.: "obrigatória". */
  requiredLabel?: string;
  /** Marca de pergunta opcional (ex.: "(opcional)"). */
  optionalLabel?: ReactNode;
  /** Mensagem de erro — liga `tone="invalid"` e `aria-describedby`. */
  error?: ReactNode;
  prefix?: string;
  className?: string;
  /** Área da resposta (escala/campo — pacotes seguintes). */
  children?: ReactNode;
};

/**
 * Quadro da pergunta: `fieldset` com `legend` visível (primeiro filho) que
 * agrupa eyebrow + número + enunciado + marca de obrigatória/opcional —
 * o nome acessível do grupo fica "Qualidade 1. Como você avalia…".
 */
export function QuestionCard({
  eyebrow,
  number,
  prompt,
  required = false,
  requiredLabel,
  optionalLabel,
  error,
  prefix = "ds",
  className,
  children,
}: QuestionCardProps) {
  const errorId = useId();
  const hasError = error != null;

  const cn = (suffix: string) =>
    delpiUiClass(
      `${prefix}-form-question${suffix}`,
      `delpi-ui-form-question${suffix}`,
    );

  return (
    <FormCard
      as="fieldset"
      tone={hasError ? "invalid" : "default"}
      prefix={prefix}
      className={[
        delpiUiClass(`${prefix}-form-question`, "delpi-ui-form-question"),
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      aria-describedby={hasError ? errorId : undefined}
    >
      <legend className={cn("__legend")}>
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
        <span className={cn("__prompt")}>
          {number != null && <>{number}. </>}
          {prompt}
          {required && (
            <span className={cn("__required")} aria-hidden="true">
              {" *"}
            </span>
          )}
          {required && requiredLabel && (
            <span className={cn("__sr-only")}> {requiredLabel}</span>
          )}
          {!required && optionalLabel != null && (
            <span className={cn("__optional")}> {optionalLabel}</span>
          )}
        </span>
      </legend>
      {children}
      {hasError && (
        <p id={errorId} className={cn("__error")}>
          {error}
        </p>
      )}
    </FormCard>
  );
}
