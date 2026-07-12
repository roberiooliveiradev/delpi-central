import type { ReactNode } from "react";

import {
  ColorPickerPopoverTrigger,
  type ColorPickerPopoverTriggerProps,
  type ColorPickerVariant,
} from "./ColorPickerPopover";

export type RibbonColorPickerProps = Omit<
  ColorPickerPopoverTriggerProps,
  "triggerLabel" | "triggerAriaLabel" | "triggerClassName" | "className"
> & {
  label: string;
  ariaLabel?: string;
  hint?: ReactNode;
  /** Classes extras no gatilho (ex.: `--inline`). */
  className?: string;
  /**
   * fill → Sem fundo; outline → Sem contorno; text → Automático.
   * Sem variant, mantém o comportamento explícito via showNoFill/showAutomatic.
   */
  variant?: ColorPickerVariant;
};

/**
 * Seletor de cor compacto para faixas ribbon (tv-dashboard e demais MFEs).
 * Usa o mesmo popover/diálogo canônico dos menus de forma.
 */
export function RibbonColorPicker({
  label,
  ariaLabel,
  className,
  variant,
  ...props
}: RibbonColorPickerProps) {
  return (
    <ColorPickerPopoverTrigger
      {...props}
      variant={variant}
      triggerClassName={["delpi-ui-color-picker-trigger--ribbon", className].filter(Boolean).join(" ")}
      triggerLabel={label}
      triggerAriaLabel={ariaLabel ?? label}
    />
  );
}
