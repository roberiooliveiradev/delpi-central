import { NativeSelectControl, type NativeSelectOption } from "@delpi/plugin-ui";

type TdRibbonSelectProps = {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly NativeSelectOption[];
  disabled?: boolean;
  className?: string;
  "aria-label"?: string;
};

/** Select nativo compacto da ribbon do deck (sem FormFieldShell). */
export function TdRibbonSelect({
  id,
  value,
  onChange,
  options,
  disabled,
  className = "td-deck-ribbon__select",
  "aria-label": ariaLabel,
}: TdRibbonSelectProps) {
  return (
    <NativeSelectControl
      id={id}
      value={value}
      onChange={onChange}
      options={options}
      disabled={disabled}
      className={className}
      aria-label={ariaLabel}
    />
  );
}
