import { HintAction } from "@delpi/plugin-ui";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type Props = {
  icon: LucideIcon;
  label: string;
  hint?: string;
  onClick: () => void;
  disabled?: boolean;
  active?: boolean;
  children?: ReactNode;
};

/** Botão vertical do ribbon (ícone + rótulo), como Inserir no PowerPoint. */
export function DeckRibbonTile({
  icon: Icon,
  label,
  hint,
  onClick,
  disabled,
  active,
  children,
}: Props) {
  const button = (
    <button
      type="button"
      className={["td-ribbon-tile", active ? "td-ribbon-tile--active" : null].filter(Boolean).join(" ")}
      disabled={disabled}
      onClick={onClick}
      aria-label={label}
    >
      <span className="td-ribbon-tile__icon">
        <Icon size={18} aria-hidden="true" />
      </span>
      <span className="td-ribbon-tile__label">{label}</span>
      {children}
    </button>
  );

  if (!hint) return button;

  return (
    <HintAction hint={hint} ariaLabel={`Ajuda: ${label}`} placement="bottom">
      {button}
    </HintAction>
  );
}
