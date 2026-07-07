import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

export type TabHintCellProps = {
  label: string;
  hint: string;
  active?: boolean;
  disabled?: boolean;
  icon?: LucideIcon;
  onSelect: () => void;
  cellClassName?: string;
  tabClassName?: string;
  tabActiveClassName?: string;
  hintPlacement?: "top" | "bottom";
  children?: ReactNode;
};

/**
 * Aba + ícone de ajuda como irmãos (evita botão aninhado em botão).
 * Estilize via className; o pacote só fornece estrutura e acessibilidade.
 */
export function TabHintCell({
  label,
  hint,
  active = false,
  disabled = false,
  icon: Icon,
  onSelect,
  cellClassName = "delpi-ui-tab-cell",
  tabClassName = "delpi-ui-tab",
  tabActiveClassName = "delpi-ui-tab--active",
  hintPlacement = "bottom",
  children,
}: TabHintCellProps) {
  const tabClass = [tabClassName, active ? tabActiveClassName : ""].filter(Boolean).join(" ");

  return (
    <div className={cellClassName} role="presentation">
      <button
        type="button"
        role="tab"
        className={tabClass}
        aria-selected={active}
        disabled={disabled}
        onClick={onSelect}
      >
        {children ?? (
          <>
            {Icon ? <Icon size={15} aria-hidden="true" /> : null}
            {label}
          </>
        )}
      </button>
      <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} placement={hintPlacement} />
    </div>
  );
}
