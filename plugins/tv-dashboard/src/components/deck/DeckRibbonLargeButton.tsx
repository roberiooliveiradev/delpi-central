import { HintAction } from "@delpi/plugin-ui/index";
import type { LucideIcon } from "lucide-react";
import type { ReactElement } from "react";

import { DeckKeyTip } from "../DeckKeyTip";

type Props = {
  icon: LucideIcon;
  label: string;
  hint?: string;
  onClick: () => void;
  disabled?: boolean;
  primary?: boolean;
  /** KeyTip F → aba → esta letra. */
  keyTip?: string;
};

/** Botão principal alto do ribbon (ex.: Nova tela), como Novo slide no PowerPoint. */
export function DeckRibbonLargeButton({
  icon: Icon,
  label,
  hint,
  onClick,
  disabled,
  primary,
  keyTip,
}: Props) {
  const button = (
    <button
      type="button"
      className={["td-ribbon-large-btn", primary ? "td-ribbon-large-btn--primary" : null]
        .filter(Boolean)
        .join(" ")}
      disabled={disabled}
      onClick={onClick}
      aria-label={label}
    >
      <Icon size={22} aria-hidden="true" />
      <span>{label}</span>
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
      {withHint as ReactElement}
    </DeckKeyTip>
  );
}
