import type { ReactNode } from "react";

import { ColorPickerPopoverTrigger, type ColorPickerPopoverTriggerProps } from "./ColorPickerPopover";

export type RibbonColorPickerProps = Omit<
  ColorPickerPopoverTriggerProps,
  "triggerLabel" | "triggerAriaLabel"
> & {
  label: string;
  ariaLabel?: string;
  hint?: ReactNode;
};

/**
 * Seletor de cor compacto para faixas ribbon (tv-dashboard e demais MFEs).
 * Usa o mesmo popover/diálogo canônico dos menus de forma.
 */
export function RibbonColorPicker({
  label,
  ariaLabel,
  className,
  ...props
}: RibbonColorPickerProps) {
  return (
    <ColorPickerPopoverTrigger
      {...props}
      className={["delpi-ui-color-picker-trigger--ribbon", className].filter(Boolean).join(" ")}
      triggerLabel={label}
      triggerAriaLabel={ariaLabel ?? label}
      showNoFill={props.showNoFill ?? false}
    />
  );
}
