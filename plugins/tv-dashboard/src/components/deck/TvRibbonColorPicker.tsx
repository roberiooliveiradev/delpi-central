import { HintAction, RibbonColorPicker, type ColorPickerVariant } from "@delpi/plugin-ui/index";
import { useState } from "react";

import { readRecentComunicadoColors, rememberComunicadoColor } from "../../utils/comunicadoRecentColors";

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
  const [recentColors, setRecentColors] = useState(readRecentComunicadoColors);

  const handleChange = (color: string) => {
    setRecentColors(rememberComunicadoColor(color));
    onChange(color);
  };

  const picker = (
    <RibbonColorPicker
      label={label}
      ariaLabel={ariaLabel ?? label}
      value={value}
      onChange={handleChange}
      variant={variant}
      showNoFill={showNoFill}
      onNoFill={onNoFill}
      showAutomatic={showAutomatic}
      contrastBackground={contrastBackground}
      onAutomatic={onAutomatic}
      recentColors={recentColors}
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
