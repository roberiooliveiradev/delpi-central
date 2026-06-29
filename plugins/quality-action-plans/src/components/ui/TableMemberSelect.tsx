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
    <select
      className="pac-field__control"
      value={value}
      aria-label={ariaLabel}
      onChange={(event) => onChange(event.target.value)}
    >
      <option value="">{placeholder}</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
