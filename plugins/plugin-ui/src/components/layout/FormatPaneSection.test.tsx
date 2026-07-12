import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FormatPaneSection } from "./FormatPaneSection";

describe("FormatPaneSection", () => {
  it("renderiza título e conteúdo", () => {
    render(
      <FormatPaneSection title="Lista de camadas">
        <p>Itens</p>
      </FormatPaneSection>,
    );
    expect(screen.getByText("Lista de camadas")).toBeTruthy();
    expect(screen.getByText("Itens")).toBeTruthy();
  });

  it("expõe ícone de balão no título quando há hint", () => {
    render(
      <FormatPaneSection title="Ordem de construção" hint="Aparecer um a um na TV.">
        <p>Ações</p>
      </FormatPaneSection>,
    );
    expect(screen.getByLabelText("Ajuda: Ordem de construção")).toBeTruthy();
  });
});
