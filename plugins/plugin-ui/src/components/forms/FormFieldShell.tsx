import type { ReactNode } from "react";

import { FieldLabel } from "../help/FieldLabel";

export type FormFieldShellClassNames = {
  root: string;
  spanWideModifier: string;
  fieldLabel: string;
  /** Opcional — linha label + aside; fallback `fieldLabel` quando ausente. */
  labelRow?: string;
  labelAside?: string;
};

export type FormFieldShellProps = {
  id: string;
  label: string;
  hint?: string;
  span?: boolean;
  className?: string;
  /** Conteúdo na linha do label, à direita (ex.: switch Valor/Expressão). */
  labelAside?: ReactNode;
  /** Conteúdo antes do controle (ex.: ícone à esquerda). */
  beforeControl?: ReactNode;
  /** Envolve beforeControl + controle (ex.: `a5s-nc-input-wrap`). */
  controlWrapperClassName?: string;
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
    labelRow: `${prefix}-field__label-row`,
    labelAside: `${prefix}-field__label-aside`,
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
  labelAside,
  beforeControl,
  controlWrapperClassName,
  afterControl,
  classNames,
  children,
}: FormFieldShellProps) {
  const rootClass = [classNames.root, span ? classNames.spanWideModifier : "", className]
    .filter(Boolean)
    .join(" ");

  const control = controlWrapperClassName ? (
    <span className={controlWrapperClassName}>
      {beforeControl}
      {children}
    </span>
  ) : (
    <>
      {beforeControl}
      {children}
    </>
  );

  const labelNode = (
    <FieldLabel label={label} htmlFor={id} hint={hint} className={classNames.fieldLabel} />
  );

  return (
    <div className={rootClass}>
      {labelAside != null ? (
        <div className={classNames.labelRow ?? classNames.fieldLabel}>
          {labelNode}
          <span className={classNames.labelAside}>{labelAside}</span>
        </div>
      ) : (
        labelNode
      )}
      {control}
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
