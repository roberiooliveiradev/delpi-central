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
  const hasError = !!(error && error.length > 0);

  const enhanceChild = () => {
    if (!React.isValidElement(children)) return children;

    // Não clona Fragment
    if (children.type === React.Fragment) return children;

    return React.cloneElement(
      children as React.ReactElement<any>,
      {
        id: htmlFor,
        "aria-required": required || undefined,
        "aria-invalid": hasError || undefined,
      }
    );
  };

  return (
    <div className="form-field">
      <div className="form-label-row">
        <label htmlFor={htmlFor}>{label}</label>

        {required && (
          <span
            className="form-required-badge"
            
          >
            REQUIRED
          </span>
        )}
      </div>

      {enhanceChild()}

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