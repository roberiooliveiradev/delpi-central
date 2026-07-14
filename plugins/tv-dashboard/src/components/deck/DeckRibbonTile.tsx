import { HintAction } from "@delpi/plugin-ui/index";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { DeckKeyTip } from "../DeckKeyTip";

type Props = {
  icon: LucideIcon;
  label: string;
  hint?: string;
  onClick: () => void;
  disabled?: boolean;
  active?: boolean;
  children?: ReactNode;
  /** KeyTip F → aba → esta letra. */
  keyTip?: string;
};

/** Botão vertical da faixa (ícone + rótulo). */
export function DeckRibbonTile({
  icon: Icon,
  label,
  hint,
  onClick,
  disabled,
  active,
  children,
  keyTip,
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

  const withHint = hint ? (
    <HintAction hint={hint} ariaLabel={`Ajuda: ${label}`} placement="bottom">
      {button}
    </HintAction>
  ) : (
    button
  );

  if (!keyTip) return withHint;

  return (
    <DeckKeyTip letter={keyTip} scope="actions">
      {withHint}
    </DeckKeyTip>
  );
}
