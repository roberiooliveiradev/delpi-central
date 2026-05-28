import { describe, expect, it } from "vitest";

import {
  shouldSuppressMarkdownForPresentation,
  type PresentationPair,
} from "./chatPresentation";

describe("shouldSuppressMarkdownForPresentation", () => {
  it("suprime markdown tabular quando há gráfico", () => {
    const pair: PresentationPair = {
      primary: { type: "chart", title: "Indicador" },
      table: { type: "table", title: "Indicador" },
    };

    expect(
      shouldSuppressMarkdownForPresentation(
        "| A | B |\n|---|---|\n| 1 | 2 |",
        pair,
      ),
    ).toBe(true);
  });

  it("mantém texto curto sem tabela", () => {
    const pair: PresentationPair = {
      primary: { type: "chart", title: "Indicador" },
      table: null,
    };

    expect(
      shouldSuppressMarkdownForPresentation("Consulta concluída.", pair),
    ).toBe(false);
  });
});
