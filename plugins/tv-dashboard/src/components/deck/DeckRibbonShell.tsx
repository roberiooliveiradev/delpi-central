import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  label?: string;
  embedded?: boolean;
  /**
   * band = altura fixa (Inserir/Home/Exibir).
   * fit = altura pelo conteúdo até o teto (Elemento/Dados) — evita cortar selects/campos.
   */
  density?: "band" | "fit";
};

export function DeckRibbonShell({
  children,
  label = "Controles de slide",
  embedded,
  density = "band",
}: Props) {
  return (
    <div
      className={[
        "td-deck-ribbon",
        "td-deck-ribbon--compact",
        density === "fit" ? "td-deck-ribbon--fit" : "td-deck-ribbon--band",
        embedded ? "td-deck-ribbon--embedded" : null,
      ]
        .filter(Boolean)
        .join(" ")}
      role="toolbar"
      aria-label={label}
    >
      {children}
    </div>
  );
}
