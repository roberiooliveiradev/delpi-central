import { FieldLabel, NativeTextControl } from "@delpi/plugin-ui/index";

import { DS_FILTER_BOX } from "./filterChrome";

type DateFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  id?: string;
  hint?: string;
};

export function DateField({ label, value, onChange, id, hint }: DateFieldProps) {
  const inputId = id ?? `tm-date-${label.replace(/\s+/g, "-").toLowerCase()}`;
  return (
    <label className={DS_FILTER_BOX} htmlFor={inputId}>
      <FieldLabel className="tm-field__label" label={label} hint={hint} />
      <NativeTextControl
        id={inputId}
        type="date"
        value={value}
        onChange={onChange}
      />
    </label>
  );
}
