import { SectionHintLabel, FormatPaneSection } from "@delpi/plugin-ui/index";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type Props = {
  title: string;
  hint?: string;
  icon?: LucideIcon;
  compact?: boolean;
  /** Painel lateral — seções recolhíveis estilo PowerPoint. */
  pane?: boolean;
  defaultOpen?: boolean;
  children: ReactNode;
};

export function DeckPropertySection({
  title,
  hint,
  icon: Icon,
  compact = false,
  pane = false,
  defaultOpen = true,
  children,
}: Props) {
  if (pane) {
    return (
      <FormatPaneSection title={title} defaultOpen={defaultOpen}>
        <div className="td-deck-inspector__section-body">{children}</div>
      </FormatPaneSection>
    );
  }

  return (
    <section
      className={[
        "td-deck-inspector__section",
        compact ? "td-deck-inspector__section--compact" : null,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <h4 className="td-deck-inspector__section-title">
        {Icon ? <Icon size={14} aria-hidden="true" /> : null}
        {hint ? <SectionHintLabel label={title} hint={hint} /> : title}
      </h4>
      <div className="td-deck-inspector__section-body">{children}</div>
    </section>
  );
}
