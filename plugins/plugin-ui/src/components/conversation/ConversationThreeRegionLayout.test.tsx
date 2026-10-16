import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ConversationThreeRegionLayout } from "./ConversationThreeRegionLayout";
afterEach(cleanup);

describe("ConversationThreeRegionLayout", () => {
  it("preserves the center while side regions toggle", () => {
    const { container } = render(
      <ConversationThreeRegionLayout
        center={<span>Central</span>}
        left={<p>Histórico indisponível</p>}
        right={<p>Sem detalhes</p>}
      />,
    );
    const center = screen.getByText("Central");
    expect(screen.getByRole("navigation", { name: "Conversas" })).toBeTruthy();
    expect(screen.queryByRole("complementary")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
    expect(screen.getByRole("complementary", { name: "Contexto da conversa" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Ocultar conversas" }));
    expect(screen.queryByRole("navigation", { name: "Conversas" })).toBeNull();
    expect(container.contains(center)).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Abrir conversas" }));
    expect(screen.getByRole("navigation", { name: "Conversas" })).toBeTruthy();
    expect(container.contains(center)).toBe(true);
  });

  it("does not present a context action without contextual content", () => {
    render(<ConversationThreeRegionLayout center={<p>Central</p>} left={<p>Left</p>} rightAvailable={false} />);
    expect(screen.queryByRole("button", { name: "Abrir contexto" })).toBeNull();
    expect(screen.queryByRole("complementary")).toBeNull();
  });

  it("does not create fake navigation entries", () => {
    render(<ConversationThreeRegionLayout center={<p>Central</p>} left={<p>Histórico ainda não disponível</p>} />);
    expect(screen.queryByRole("button", { name: "Nova conversa" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Pesquisar" })).toBeNull();
  });
});
