import { useId } from "react";

import { FieldLabel } from "@delpi/plugin-ui";
import { SelectControl } from "./SelectControl";
import type { SelectOption } from "./selectTypes";

type SelectFieldProps = {
  id?: string;
  label: string;
  hint?: string;
  options: readonly SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  searchable?: boolean;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  allowEmpty?: boolean;
  emptyLabel?: string;
};

export function SelectField({
  id,
  label,
  hint,
  options,
  value,
  onChange,
  placeholder = "Selecione…",
  searchable = false,
  disabled = false,
  required = false,
  className,
  allowEmpty = false,
  emptyLabel = "—",
}: SelectFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;

  const rootClass = ["ds-filter-box", className].filter(Boolean).join(" ");

  return (
    <div className={rootClass}>
      <label htmlFor={fieldId}>
        <FieldLabel className="tm-field__label" label={label} hint={hint} />
        {required ? <span className="ds-field__required"> *</span> : null}
      </label>
      <SelectControl
        id={fieldId}
        options={options}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        searchable={searchable}
        disabled={disabled}
        allowEmpty={allowEmpty}
        emptyLabel={emptyLabel}
        ariaLabel={label}
      />
    </div>
  );
}
