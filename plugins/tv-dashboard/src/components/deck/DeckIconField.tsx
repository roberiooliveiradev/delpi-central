import { FieldLabel } from "@delpi/plugin-ui/index";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type Props = {
  id?: string;
  icon: LucideIcon;
  label: string;
  hint?: string;
  children: ReactNode;
  className?: string;
  compact?: boolean;
};

/** Campo compacto com ícone na faixa de configuração (aba Tela / Programação). */
export function DeckIconField({
  id,
  icon: Icon,
  label,
  hint,
  children,
  className,
  compact = true,
}: Props) {
  return (
    <div
      className={[
        "td-deck-icon-field",
        compact ? "td-deck-icon-field--compact" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="td-deck-icon-field__head">
        <span className="td-deck-icon-field__icon" aria-hidden="true">
          <Icon size={16} strokeWidth={2} />
        </span>
        <FieldLabel
          htmlFor={id}
          label={label}
          hint={hint}
          className="td-deck-icon-field__label"
        />
      </div>
      {children}
    </div>
  );
}
