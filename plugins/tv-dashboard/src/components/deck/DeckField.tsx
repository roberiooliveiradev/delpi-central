import { FieldLabel } from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";

type Props = {
  id?: string;
  label: string;
  hint?: string;
  children: ReactNode;
  className?: string;
};

export function DeckField({ id, label, hint, children, className }: Props) {
  return (
    <div className={["td-field", className].filter(Boolean).join(" ")}>
      <FieldLabel htmlFor={id} label={label} hint={hint} className="td-field__label" />
      {children}
    </div>
  );
}
