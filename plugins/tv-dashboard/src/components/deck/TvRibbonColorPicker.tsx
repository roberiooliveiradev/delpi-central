import { HintAction, RibbonColorPicker, type ColorPickerVariant } from "@delpi/plugin-ui/index";

type TvRibbonColorPickerProps = {
  hint?: string;
  label: string;
  ariaLabel?: string;
  value?: string;
  onChange: (color: string) => void;
  inline?: boolean;
  /** fill → Sem fundo; outline → Sem contorno; text → Automático. */
  variant?: ColorPickerVariant;
  showNoFill?: boolean;
  onNoFill?: () => void;
  showAutomatic?: boolean;
  contrastBackground?: string | null;
  onAutomatic?: (color: "#000000" | "#ffffff") => void;
};

/** Seletor de cor do ribbon tv-dashboard — delega ao componente canônico do plugin-ui. */
export function TvRibbonColorPicker({
  hint,
  label,
  ariaLabel,
  value,
  onChange,
  inline,
  variant,
  showNoFill,
  onNoFill,
  showAutomatic,
  contrastBackground,
  onAutomatic,
}: TvRibbonColorPickerProps) {
  const picker = (
    <RibbonColorPicker
      label={label}
      ariaLabel={ariaLabel ?? label}
      value={value}
      onChange={onChange}
      variant={variant}
      showNoFill={showNoFill}
      onNoFill={onNoFill}
      showAutomatic={showAutomatic}
      contrastBackground={contrastBackground}
      onAutomatic={onAutomatic}
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
