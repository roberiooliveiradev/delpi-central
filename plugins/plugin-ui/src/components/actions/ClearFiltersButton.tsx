import { FilterX } from "lucide-react";

import { ActionButton } from "./ActionButton";

export type ClearFiltersButtonDensity = "default" | "compact";

export type ClearFiltersButtonProps = {
  onClick: () => void;
  /** Texto do botão (padrão: «Limpar filtros»). */
  label?: string;
  disabled?: boolean;
  /** `compact` para headers densos de FilterBar. */
  density?: ClearFiltersButtonDensity;
  className?: string;
  "aria-label"?: string;
};

const DEFAULT_LABEL = "Limpar filtros";

/**
 * Ação canônica para descartar filtros ativos — mais destaque que `ghost`.
 * CSS: `styles/action-controls.css` (`.delpi-ui-clear-filters-btn*`).
 */
export function ClearFiltersButton({
  onClick,
  label = DEFAULT_LABEL,
  disabled = false,
  density = "default",
  className,
  "aria-label": ariaLabel,
}: ClearFiltersButtonProps) {
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
