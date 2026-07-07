import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ContentCard, contentCardBemClasses } from "./ContentCard";

describe("ContentCard", () => {
  it("renderiza header, descrição e corpo", () => {
    render(
      <ContentCard
        title="Leitura executiva"
        description="Resumo integrado"
        headerRight={<span>Mensal</span>}
        classNames={contentCardBemClasses("si")}
      >
        <p>Conteúdo</p>
      </ContentCard>,
    );

    expect(screen.getByText("Leitura executiva")).toBeTruthy();
    expect(screen.getByText("Resumo integrado")).toBeTruthy();
    expect(screen.getByText("Conteúdo")).toBeTruthy();
  });
});
