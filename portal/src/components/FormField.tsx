// src/components/FormField.tsx

import React from "react";

type Props = {
  label: string;
  required?: boolean;
  error?: string[] | undefined;
  htmlFor?: string;
  children: React.ReactNode;
};

export const FormField = ({
  label,
  required,
  error,
  htmlFor,
  children,
}: Props) => {
  const hasError = error && error.length > 0;

  return (
    <div className="form-field">
      <div className="form-label-row">
        <label htmlFor={htmlFor}>{label}</label>

        {required && (
          <span
            className="form-required-badge"
            title="Campo obrigatório"
          >
            REQUIRED
          </span>
        )}
      </div>

      {React.cloneElement(children as any, {
        id: htmlFor,
        "aria-required": required || undefined,
        "aria-invalid": hasError ? true : undefined,
      })}

      {hasError && (
        <div className="field-error">
          {error!.map((e, i) => (
            <div key={i}>{e}</div>
          ))}
        </div>
      )}
    </div>
  );
};