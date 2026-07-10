import { HintAction, RibbonColorPicker } from "@delpi/plugin-ui/index";

type TvRibbonColorPickerProps = {
  hint?: string;
  label: string;
  ariaLabel?: string;
  value?: string;
  onChange: (color: string) => void;
  inline?: boolean;
  showNoFill?: boolean;
  onNoFill?: () => void;
};

/** Seletor de cor do ribbon tv-dashboard — delega ao componente canônico do plugin-ui. */
export function TvRibbonColorPicker({
  hint,
  label,
  ariaLabel,
  value,
  onChange,
  inline,
  showNoFill,
  onNoFill,
}: TvRibbonColorPickerProps) {
  const picker = (
    <RibbonColorPicker
      label={label}
      ariaLabel={ariaLabel ?? label}
      value={value}
      onChange={onChange}
      showNoFill={showNoFill}
      onNoFill={onNoFill}
      className={inline ? "delpi-ui-color-picker-trigger--inline" : undefined}
    />
  );

  if (!hint) {
    return picker;
  }

  return (
    <HintAction hint={hint} ariaLabel={`Ajuda: ${label}`}>
      {picker}
    </HintAction>
  );
}
