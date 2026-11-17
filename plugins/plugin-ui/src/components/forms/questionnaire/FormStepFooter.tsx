import type { ReactNode } from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";

import { FormButton } from "./FormButton";

export type FormStepFooterAction = {
  label: ReactNode;
  onClick: () => void;
};

export type FormStepFooterProps = {
  /** Pendência/erro da etapa (vermelho, `role="status"`). */
  message?: ReactNode;
  back?: FormStepFooterAction;
  next: FormStepFooterAction & {
    busy?: boolean;
    busyLabel?: ReactNode;
  };
  /** Prefixo BEM do consumidor (dual-class). */
  prefix?: string;
  className?: string;
};

/**
 * Rodapé de ações de uma etapa do formulário. Abaixo de 600 px fica fixo na
 * base (`position: sticky; bottom: 0`, margem negativa até as bordas da
 * coluna); acima disso flui normalmente no fim da coluna. Sem lógica de
 * fluxo — recebe apenas dados e callbacks.
 */
export function FormStepFooter({
  message,
  back,
  next,
  prefix = "ds",
  className,
}: FormStepFooterProps) {
  const cn = (suffix: string) =>
    delpiUiClass(
      `${prefix}-form-step-footer${suffix}`,
      `delpi-ui-form-step-footer${suffix}`,
    );

  return (
    <footer
      className={[cn(""), className].filter(Boolean).join(" ")}
    >
      {message != null && (
        <p className={cn("__message")} role="status">
          {message}
        </p>
      )}
      <div className={cn("__actions")}>
        {back != null && (
          <FormButton
            variant="secondary"
            onClick={back.onClick}
            className={cn("__back")}
          >
            {back.label}
          </FormButton>
        )}
        <FormButton
          variant="primary"
          busy={next.busy}
          busyLabel={next.busyLabel}
          onClick={next.onClick}
          className={cn("__next")}
        >
          {next.label}
        </FormButton>
      </div>
    </footer>
  );
}
