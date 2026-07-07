import { HintAction } from "@delpi/plugin-ui";
import type { LucideIcon } from "lucide-react";

type Props = {
  icon: LucideIcon;
  label: string;
  hint?: string;
  onClick: () => void;
  disabled?: boolean;
  primary?: boolean;
};

/** Botão principal alto do ribbon (ex.: Nova tela), como Novo slide no PowerPoint. */
export function DeckRibbonLargeButton({
  icon: Icon,
  label,
  hint,
  onClick,
  disabled,
  primary,
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

  if (!hint) return button;

  return (
    <HintAction hint={hint} ariaLabel={`Ajuda: ${label}`} placement="bottom">
      {button}
    </HintAction>
  );
}
