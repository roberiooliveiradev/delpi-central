import { SectionHintLabel } from "@delpi/plugin-ui";
import type { ReactNode } from "react";

type Props = {
  label: string;
  hint?: string;
  wide?: boolean;
  children: ReactNode;
};

/** Grupo do ribbon estilo PowerPoint: controles em cima, legenda embaixo. */
export function DeckRibbonGroup({ label, hint, wide, children }: Props) {
  return (
    <div
      className={["td-deck-ribbon__group", wide ? "td-deck-ribbon__group--wide" : null]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="td-deck-ribbon__body">{children}</div>
      <div className="td-deck-ribbon__caption">
        {hint ? (
          <SectionHintLabel label={label} hint={hint} className="td-deck-ribbon__caption-text" />
        ) : (
          <span className="td-deck-ribbon__caption-text">{label}</span>
        )}
      </div>
    </div>
  );
}
