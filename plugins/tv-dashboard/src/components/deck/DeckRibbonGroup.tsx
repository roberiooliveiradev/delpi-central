import { SectionHintLabel } from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";

type Props = {
  label: string;
  hint?: string;
  wide?: boolean;
  /**
   * `below` — legenda abaixo dos controles (padrão da faixa).
   * `above` — subtítulo no painel embutido.
   * `none` — sem caption (accordion já titulou a seção).
   */
  captionPlacement?: "below" | "above" | "none";
  children: ReactNode;
};

/** Grupo da faixa: controles em cima, legenda embaixo. */
export function DeckRibbonGroup({
  label,
  hint,
  wide,
  captionPlacement = "below",
  children,
}: Props) {
  const caption =
    captionPlacement === "none" ? null : (
      <div
        className={[
          "td-deck-ribbon__caption",
          captionPlacement === "above" ? "td-deck-ribbon__caption--above" : null,
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {hint ? (
          <SectionHintLabel label={label} hint={hint} className="td-deck-ribbon__caption-text" />
        ) : (
          <span className="td-deck-ribbon__caption-text">{label}</span>
        )}
      </div>
    );

  return (
    <div
      className={[
        "td-deck-ribbon__group",
        wide ? "td-deck-ribbon__group--wide" : null,
        captionPlacement === "none" ? "td-deck-ribbon__group--no-caption" : null,
        captionPlacement === "above" ? "td-deck-ribbon__group--caption-above" : null,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {captionPlacement === "above" ? caption : null}
      <div className="td-deck-ribbon__body">{children}</div>
      {captionPlacement === "below" ? caption : null}
    </div>
  );
}
