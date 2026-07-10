import { NativeSelectControl, type NativeSelectOption } from "@delpi/plugin-ui/index";

type CxInlineSelectProps = {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly NativeSelectOption[];
  disabled?: boolean;
  placeholderOption?: string;
  className?: string;
  "aria-label"?: string;
};

/** Select compacto (toolbar / pergunta) — mantém classe `cx-select`. */
export function CxInlineSelect({
  id,
  value,
  onChange,
  options,
  disabled,
  placeholderOption,
  className = "cx-select",
  "aria-label": ariaLabel,
}: CxInlineSelectProps) {
  return (
    <NativeSelectControl
      id={id}
      value={value}
      onChange={onChange}
      options={options}
      disabled={disabled}
      placeholderOption={placeholderOption}
      className={className}
      aria-label={ariaLabel}
    />
  );
}
