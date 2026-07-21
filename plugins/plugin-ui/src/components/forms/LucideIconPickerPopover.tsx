import { useRef, type CSSProperties, type RefObject } from "react";

import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import type { AnchoredPanelPlacement } from "../shape/anchoredPanelCoords";

import {
  LucideIconPicker,
  type LucideIconPickerLabels,
  type LucideIconPickerProps,
} from "./LucideIconPicker";

export type LucideIconPickerPopoverProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Âncora do portal (botão/tile do host). */
  anchorRef: RefObject<HTMLElement | null>;
  value?: string | null;
  onChange: (iconName: string | null) => void;
  curatedOnly?: boolean;
  nameFormat?: "kebab" | "pascal";
  maxResults?: number;
  title?: string;
  labels?: LucideIconPickerLabels;
  /** Exibe «Remover ícone» no rodapé (padrão true). */
  showClear?: boolean;
  className?: string;
  pickerClassName?: string;
  style?: CSSProperties;
  portalScopeClassName?: string;
  density?: "comfortable" | "compact";
  preferredPlacement?: AnchoredPanelPlacement;
  ariaLabel?: string;
};

/**
 * Popover canônico da biblioteca Lucide (catálogo completo + busca).
 * Use em Inserir e Trocar — não duplique grade curta vs. painel embutido.
 */
export function LucideIconPickerPopover({
  open,
  onOpenChange,
  anchorRef,
  value,
  onChange,
  curatedOnly = false,
  nameFormat = "pascal",
  maxResults,
  title,
  labels,
  showClear = true,
  className,
  pickerClassName,
  style,
  portalScopeClassName,
  density = "compact",
  preferredPlacement = "bottom",
  ariaLabel,
}: LucideIconPickerPopoverProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  if (!open) return null;

  const dismiss = () => onOpenChange(false);

  const pickerProps: LucideIconPickerProps = {
    value,
    onChange,
    onClose: dismiss,
    curatedOnly,
    nameFormat,
    maxResults,
    title: title ?? ariaLabel,
    labels,
    showClear,
    className: pickerClassName,
    style,
    embedded: false,
  };

  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      density={density}
      preferredPlacement={preferredPlacement}
      portalScopeClassName={portalScopeClassName}
      className={["delpi-ui-lucide-icon-picker-popover", className].filter(Boolean).join(" ")}
      onDismiss={dismiss}
    >
      <LucideIconPicker {...pickerProps} />
    </AnchoredPanelPortal>
  );
}
