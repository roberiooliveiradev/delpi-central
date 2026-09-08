import type { CSSProperties, ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type FormActionsAlign = "start" | "end";

export type FormActionsClassNames = {
  root: string;
  alignEndModifier: string;
};

export type FormActionsProps = {
  children: ReactNode;
  align?: FormActionsAlign;
  className?: string;
  classNames: FormActionsClassNames;
};

/** Espaçamento default entre CTAs (Voltar/Próximo, Cancelar/Salvar, …). */
export const FORM_ACTIONS_GAP_PX = 24;

/** Separação vertical do conteúdo acima (campo/lista → barra de ações). */
export const FORM_ACTIONS_BLOCK_START_PX = 24;

const formActionsGapStyle: CSSProperties = {
  gap: FORM_ACTIONS_GAP_PX,
  columnGap: FORM_ACTIONS_GAP_PX,
  rowGap: 12,
  marginBlockStart: FORM_ACTIONS_BLOCK_START_PX,
};

export function formActionsBemClasses(prefix: string): FormActionsClassNames {
  const root = `${prefix}-form-actions`;
  const ui = "delpi-ui-form-actions";
  return {
    root: delpiUiClass(root, ui),
    alignEndModifier: delpiUiClass(`${root}--end`, `${ui}--end`),
  };
}

export const formActionsPacClasses = formActionsBemClasses;

/** Barra de botões de formulário (salvar, cancelar, etc.). */
export function FormActions({
  children,
  align = "start",
  className,
  classNames,
}: FormActionsProps) {
  const rootClass = [
    classNames.root,
    align === "end" ? classNames.alignEndModifier : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClass}
      style={formActionsGapStyle}
      data-form-actions-gap={FORM_ACTIONS_GAP_PX}
      data-form-actions-block-start={FORM_ACTIONS_BLOCK_START_PX}
    >
      {children}
    </div>
  );
}

export type DashboardFormActionsProps = Omit<FormActionsProps, "classNames">;

export function createDashboardFormActions(config: { classNames: FormActionsClassNames }) {
  return function DashboardFormActions(props: DashboardFormActionsProps) {
    return <FormActions classNames={config.classNames} {...props} />;
  };
}
