import {
  SuppliesSelectField,
  SuppliesTextField,
} from "../../app/suppliesUi";
import {
  SUPPLIERS_CONTENT as C,
  supplierFieldMaxLengthHint,
} from "./content";
import type { SupplierFieldSpec } from "./types";

type SupplierFieldInputProps = {
  spec: SupplierFieldSpec;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  /** Marca "*" no label quando a inclusão exige o campo. */
  showRequiredMark?: boolean;
  /** Hint customizado (ex.: ajuda de edição). */
  hint?: string;
};

/**
 * Input de um campo do SUPPLIER_FIELD_REGISTRY — usado por criação e edição.
 * Aplica digitsOnly/uppercase/maxLength declarados no spec.
 */
export function SupplierFieldInput({
  spec,
  value,
  onChange,
  disabled,
  showRequiredMark,
  hint,
}: SupplierFieldInputProps) {
  const label =
    showRequiredMark && spec.required ? `${spec.label} *` : spec.label;

  if (spec.options) {
    return (
      <SuppliesSelectField
        label={label}
        value={value}
        options={spec.options}
        allowEmpty
        emptyLabel={C.fieldEmptyOption}
        onChange={onChange}
        disabled={disabled}
      />
    );
  }

  return (
    <SuppliesTextField
      label={label}
      hint={hint ?? supplierFieldMaxLengthHint(spec.maxLength)}
      value={value}
      onChange={(raw) => {
        let next = raw;
        if (spec.digitsOnly) next = next.replace(/\D/g, "");
        if (spec.uppercase) next = next.toUpperCase();
        onChange(next.slice(0, spec.maxLength));
      }}
      disabled={disabled}
    />
  );
}
