import { NativeSelectControl } from "@delpi/plugin-ui/index";

import type { SelectOption } from "./types";

type Props = {
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  ariaLabel: string;
  placeholder?: string;
};

export function TableMemberSelect({
  value,
  options,
  onChange,
  ariaLabel,
  placeholder = "Selecione…",
}: Props) {
  return (
    <NativeSelectControl
      className="pac-field__control"
      value={value}
      onChange={onChange}
      options={options}
      placeholderOption={placeholder}
      aria-label={ariaLabel}
    />
  );
}
