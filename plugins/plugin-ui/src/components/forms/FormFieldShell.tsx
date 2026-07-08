import type { ReactNode } from "react";

import { FieldLabel } from "../help/FieldLabel";

export type FormFieldShellClassNames = {
  root: string;
  spanWideModifier: string;
  fieldLabel: string;
};

export type FormFieldShellProps = {
  id: string;
  label: string;
  hint?: string;
  span?: boolean;
  className?: string;
  /** Conteúdo após o controle (ex.: mensagem de erro do plugin). */
  afterControl?: ReactNode;
  classNames: FormFieldShellClassNames;
  children: ReactNode;
};

export function formFieldShellBemClasses(prefix: string): FormFieldShellClassNames {
  return {
    root: `${prefix}-field`,
    spanWideModifier: `${prefix}-span-2`,
    fieldLabel: `${prefix}-field__label`,
  };
}

export const formFieldShellKaizenClasses = formFieldShellBemClasses;

/** Wrapper label + controle nativo (input/select/textarea direto no field). */
export function FormFieldShell({
  id,
  label,
  hint,
  span = false,
  className,
  afterControl,
  classNames,
  children,
}: FormFieldShellProps) {
  const rootClass = [classNames.root, span ? classNames.spanWideModifier : "", className]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass}>
      <FieldLabel label={label} htmlFor={id} hint={hint} className={classNames.fieldLabel} />
      {children}
      {afterControl}
    </div>
  );
}

export type DashboardFormFieldShellProps = Omit<FormFieldShellProps, "classNames">;

export function createDashboardFormFieldShell(config: { classNames: FormFieldShellClassNames }) {
  return function DashboardFormFieldShell(props: DashboardFormFieldShellProps) {
    return <FormFieldShell classNames={config.classNames} {...props} />;
  };
}
