import { SectionHintLabel } from "@delpi/plugin-ui";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type Props = {
  title: string;
  hint?: string;
  icon?: LucideIcon;
  children: ReactNode;
};

export function DeckPropertySection({ title, hint, icon: Icon, children }: Props) {
  return (
    <section className="td-deck-inspector__section">
      <h4 className="td-deck-inspector__section-title">
        {Icon ? <Icon size={14} aria-hidden="true" /> : null}
        {hint ? <SectionHintLabel label={title} hint={hint} /> : title}
      </h4>
      <div className="td-deck-inspector__section-body">{children}</div>
    </section>
  );
}
