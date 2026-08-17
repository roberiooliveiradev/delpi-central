// portal/src/ui-kit/form/FormField.tsx

import React, { type ReactNode } from "react";
import "./FormField.css";

export type FormFieldProps = {
  label: string;
  required?: boolean;
  error?: string[] | undefined;
  hint?: ReactNode;
  htmlFor?: string;
  children: ReactNode;
  className?: string;
};

export function FormField({
  label,
  required,
  error,
  hint,
  htmlFor,
  children,
  className,
}: FormFieldProps) {
  const hasError = !!(error && error.length > 0);
  const classes = ["portal-ui-field", className ?? ""]
    .filter(Boolean)
    .join(" ");

  const enhanceChild = () => {
    if (!React.isValidElement(children)) return children;
    if (children.type === React.Fragment) return children;

    return React.cloneElement(children as React.ReactElement<Record<string, unknown>>, {
      id: htmlFor ?? (children.props as { id?: string }).id,
      "aria-required": required || undefined,
      "aria-invalid": hasError || undefined,
    });
  };

  return (
    <div className={classes}>
      <div className="portal-ui-field__label-row">
        <label className="portal-ui-field__label" htmlFor={htmlFor}>
          {label}
        </label>
        {required ? (
          <span className="portal-ui-field__required">Obrigatório</span>
        ) : null}
      </div>

      {enhanceChild()}

      {hint && !hasError ? (
        <p className="portal-ui-field__hint">{hint}</p>
      ) : null}

      {hasError ? (
        <div className="portal-ui-field__error" role="alert">
          {error!.map((e, i) => (
            <div key={i}>{e}</div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
