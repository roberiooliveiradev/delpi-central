import type { ReactNode } from "react";

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

export function formActionsBemClasses(prefix: string): FormActionsClassNames {
  return {
    root: `${prefix}-form-actions`,
    alignEndModifier: `${prefix}-form-actions--end`,
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

  return <div className={rootClass}>{children}</div>;
}

export type DashboardFormActionsProps = Omit<FormActionsProps, "classNames">;

export function createDashboardFormActions(config: { classNames: FormActionsClassNames }) {
  return function DashboardFormActions(props: DashboardFormActionsProps) {
    return <FormActions classNames={config.classNames} {...props} />;
  };
}
