import type { ReactNode } from "react";

export type FormGridClassNames = {
  root: string;
};

export type FormGridProps = {
  children: ReactNode;
  className?: string;
  classNames: FormGridClassNames;
};

export function formGridBemClasses(prefix: string): FormGridClassNames {
  return {
    root: `${prefix}-form-grid`,
  };
}

export const formGridPacClasses = formGridBemClasses;

/** Grade de campos de formulário (edição ou leitura). */
export function FormGrid({ children, className, classNames }: FormGridProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  return <div className={rootClass}>{children}</div>;
}

export type DashboardFormGridProps = Omit<FormGridProps, "classNames">;

export function createDashboardFormGrid(config: { classNames: FormGridClassNames }) {
  return function DashboardFormGrid(props: DashboardFormGridProps) {
    return <FormGrid classNames={config.classNames} {...props} />;
  };
}
