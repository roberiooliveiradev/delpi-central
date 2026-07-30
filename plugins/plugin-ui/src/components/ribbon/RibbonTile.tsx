import type { LucideIcon } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { HintAction } from "../help/HintAction";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type RibbonTileProps = {
  icon: LucideIcon;
  label: string;
  hint?: string;
  active?: boolean;
  disabled?: boolean;
  className?: string;
  iconSize?: number;
  onClick?: () => void;
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children" | "onClick" | "disabled" | "className">;

export function ribbonTileBemClasses(prefix = "delpi-ui"): {
  root: string;
  rootActive: string;
  icon: string;
  label: string;
} {
  const base = `${prefix}-ribbon-tile`;
  const ui = "delpi-ui-ribbon-tile";
  return {
    root: delpiUiClass(base, ui),
    rootActive: delpiUiClass(`${base}--active`, `${ui}--active`),
    icon: delpiUiClass(`${base}__icon`, `${ui}__icon`),
    label: delpiUiClass(`${base}__label`, `${ui}__label`),
  };
}

const DEFAULT_CN = ribbonTileBemClasses();

/**
 * Tile de ribbon: ícone encima + rótulo (padrão visual do insert do TV Dashboard).
 */
export function RibbonTile({
  icon: Icon,
  label,
  hint,
  active = false,
  disabled = false,
  className,
  iconSize = 18,
  onClick,
  type = "button",
  ...rest
}: RibbonTileProps) {
  const button = (
    <button
      type={type}
      className={[
        DEFAULT_CN.root,
        active ? DEFAULT_CN.rootActive : "",
        className ?? "",
      ]
        .filter(Boolean)
        .join(" ")}
      disabled={disabled}
      aria-label={label}
      aria-pressed={active || undefined}
      onClick={onClick}
      {...rest}
    >
      <span className={DEFAULT_CN.icon} aria-hidden>
        <Icon size={iconSize} strokeWidth={1.75} />
      </span>
      <span className={DEFAULT_CN.label}>{label}</span>
    </button>
  );

  if (!hint || disabled) return button;

  return (
    <HintAction hint={hint} ariaLabel={`Ajuda: ${label}`} placement="bottom">
      {button}
    </HintAction>
  );
}

export type RibbonTilesProps = {
  children: ReactNode;
  compact?: boolean;
  /** Linhas no grid de fluxo em coluna (padrão 1). */
  rows?: 1 | 2;
  className?: string;
  "aria-label"?: string;
};

export function ribbonTilesBemClasses(prefix = "delpi-ui"): {
  root: string;
  rootCompact: string;
  rootRows2: string;
} {
  const base = `${prefix}-ribbon-tiles`;
  const ui = "delpi-ui-ribbon-tiles";
  return {
    root: delpiUiClass(base, ui),
    rootCompact: delpiUiClass(`${base}--compact`, `${ui}--compact`),
    rootRows2: delpiUiClass(`${base}--rows-2`, `${ui}--rows-2`),
  };
}

const TILES_CN = ribbonTilesBemClasses();

/** Grid horizontal de {@link RibbonTile}. */
export function RibbonTiles({
  children,
  compact = false,
  rows = 1,
  className,
  "aria-label": ariaLabel,
}: RibbonTilesProps) {
  return (
    <div
      className={[
        TILES_CN.root,
        compact ? TILES_CN.rootCompact : "",
        rows === 2 ? TILES_CN.rootRows2 : "",
        className ?? "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="group"
      aria-label={ariaLabel}
    >
      {children}
    </div>
  );
}
