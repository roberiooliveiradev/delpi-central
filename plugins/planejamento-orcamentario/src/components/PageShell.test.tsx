import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { PageShell } from "./PageShell";

afterEach(() => {
  cleanup();
});

describe("PageShell", () => {
  it("mostra só voltar e logo Delpi — sem título/subtítulo visíveis", () => {
    render(
      <PageShell
        title="Meus centros de custo"
        subtitle="Escolha um centro para elaborar o orçamento."
        backRoute="home"
      >
        <p>conteúdo</p>
      </PageShell>,
    );

    expect(screen.getByRole("link", { name: /voltar/i })).toBeTruthy();
    expect(screen.getByRole("img", { name: /delpi/i })).toBeTruthy();
    expect(screen.queryByText("Escolha um centro para elaborar o orçamento.")).toBeNull();
    const heading = screen.getByRole("heading", { level: 1, name: "Meus centros de custo" });
    expect(heading.className).toContain("po-sr-only");
  });

  it("na home sem backRoute ainda exibe a logo", () => {
    render(
      <PageShell title="Planejamento Orçamentário">
        <p>home</p>
      </PageShell>,
    );
    expect(screen.queryByRole("link", { name: /voltar/i })).toBeNull();
    expect(screen.getByRole("img", { name: /delpi/i })).toBeTruthy();
  });
});
