import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ConversationThreeRegionLayout } from "./ConversationThreeRegionLayout";
afterEach(cleanup);
describe("ConversationThreeRegionLayout R2", () => {
  it("retains the left navigation as a rail while the center remains mounted", () => {
    const { container } = render(
      <ConversationThreeRegionLayout left={({ collapsed }) => <span>{collapsed ? "Rail" : "Menu"}</span>}
        right={<span>Projeções</span>}
        center={(controls) => <header>{controls.leftToggle} <span>Conversa estável</span> {controls.rightToggle}</header>} />,
    );
    const center = screen.getByText("Conversa estável");
    expect(screen.getByRole("navigation", { name: "Conversas" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Recolher conversas" }));
    expect(screen.getByRole("navigation", { name: "Conversas" })).toBeTruthy();
    expect(screen.getByText("Rail")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Expandir conversas" })).toBeTruthy();
    expect(container.contains(center)).toBe(true);
  });
  it("opens a floating context dialog without adding a right-hand column", () => {
    const { container } = render(<ConversationThreeRegionLayout
      left={<span>Menu</span>} right={<span>Contexto real</span>}
      center={({ rightToggle }) => <header>{rightToggle}</header>} />);
    fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
    expect(screen.getByRole("dialog", { name: "Contexto da conversa" })).toBeTruthy();
    expect(screen.getByText("Contexto real")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-conversation-three-region__right")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Fechar painel de contexto" }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });
  it("hides context control when unavailable", () => {
    render(<ConversationThreeRegionLayout rightAvailable={false} right={<span>Hidden</span>}
      center={({ rightToggle }) => <header>{rightToggle}</header>} />);
    expect(screen.queryByRole("button", { name: "Abrir contexto" })).toBeNull();
  });
});
