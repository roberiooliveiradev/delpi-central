import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ConversationThreeRegionLayout } from "./ConversationThreeRegionLayout";
afterEach(cleanup);
describe("ConversationThreeRegionLayout R1", () => {
  it("has exactly one toggle per region and no extra controls bar", () => {
    const { container } = render(
      <ConversationThreeRegionLayout left={<span>Menu</span>} right={<span>Projeções</span>}
        center={(controls) => (
          <div>
            <header>{controls.leftToggle} <span>DÉLIA</span> {controls.rightToggle}</header>
            <span>Conversa preservada</span>
          </div>
        )} />,
    );
    const central = screen.getByText("Conversa preservada");
    expect(container.querySelector(".delpi-ui-conversation-three-region__controls")).toBeNull();
    expect(screen.getAllByRole("button", { name: "Recolher conversas" })).toHaveLength(1);
    expect(screen.queryByRole("button", { name: "Abrir conversas" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
    expect(screen.getByRole("complementary", { name: "Contexto da conversa" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Abrir contexto" })).toBeNull();
    expect(screen.getAllByRole("button", { name: "Fechar painel de contexto" })).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Recolher conversas" }));
    expect(screen.queryByRole("navigation", { name: "Conversas" })).toBeNull();
    expect(screen.getAllByRole("button", { name: "Abrir conversas" })).toHaveLength(1);
    expect(container.contains(central)).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Abrir conversas" }));
    expect(screen.getByRole("navigation", { name: "Conversas" })).toBeTruthy();
    expect(container.contains(central)).toBe(true);
  });
  it("omits context control if unavailable", () => {
    render(<ConversationThreeRegionLayout left={<span>Menu</span>} rightAvailable={false}
      center={(controls) => <header>{controls.leftToggle}{controls.rightToggle}</header>} />);
    expect(screen.queryByRole("button", { name: "Abrir contexto" })).toBeNull();
  });
});
