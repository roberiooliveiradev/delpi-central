import { FilterX } from "lucide-react";

import { ActionButton } from "./ActionButton";
import { IconButton } from "./IconButton";

export type ClearFiltersButtonDensity = "default" | "compact";
export type ClearFiltersButtonVariant = "labeled" | "icon";

export type ClearFiltersButtonProps = {
  onClick: () => void;
  /** Texto do botão (padrão: «Limpar filtros») — também vira o `aria-label`. */
  label?: string;
  disabled?: boolean;
  /** `compact` para headers densos de FilterBar. */
  density?: ClearFiltersButtonDensity;
  /**
   * `labeled` (padrão): botão com ícone + texto.
   * `icon`: quadrado só-ícone em tom âmbar — o controle canônico de
   * «limpar filtros» das toolbars de listagem (UX V3).
   */
  variant?: ClearFiltersButtonVariant;
  className?: string;
  "aria-label"?: string;
};

const DEFAULT_LABEL = "Limpar filtros";

/**
 * Ação canônica para descartar filtros ativos — mais destaque que `ghost`.
 * CSS: `styles/action-controls.css` (`.delpi-ui-clear-filters-btn*` e
 * `.delpi-ui-icon-btn--amber` para a variante icon).
 */
export function ClearFiltersButton({
  onClick,
  label = DEFAULT_LABEL,
  disabled = false,
  density = "default",
  variant = "labeled",
  className,
  "aria-label": ariaLabel,
}: ClearFiltersButtonProps) {
  if (variant === "icon") {
    return (
      <IconButton
        tone="amber"
        onClick={onClick}
        disabled={disabled}
        aria-label={ariaLabel ?? label}
        className={className}
      >
        <FilterX size={16} aria-hidden="true" />
      </IconButton>
    );
  }

  const rootClass = [
    "delpi-ui-clear-filters-btn",
    density === "compact" ? "delpi-ui-clear-filters-btn--compact" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <ActionButton
      variant="default"
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel ?? label}
      className={rootClass}
    >
      <FilterX size={density === "compact" ? 14 : 16} aria-hidden="true" />
      {label}
    </ActionButton>
  );
}
