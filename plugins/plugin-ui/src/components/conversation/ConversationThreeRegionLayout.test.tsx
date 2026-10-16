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
    const collapse = screen.getByRole("button", { name: "Recolher conversas" });
    expect(collapse.className).toContain("delpi-ui-conversation-three-region__rail-toggle");
    expect(collapse.getAttribute("aria-expanded")).toBe("true");
    fireEvent.click(collapse);
    expect(screen.getByRole("navigation", { name: "Conversas" })).toBeTruthy();
    expect(screen.getByText("Rail")).toBeTruthy();
    const expand = screen.getByRole("button", { name: "Expandir conversas" });
    expect(expand.className).toContain("delpi-ui-conversation-three-region__rail-toggle");
    expect(expand.getAttribute("aria-expanded")).toBe("false");
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
  it("keeps floating surface mounted for exit motion but inaccessible while closed", () => {
    const { container } = render(
      <ConversationThreeRegionLayout
        left={({ collapsed }) => <span>{collapsed ? "Rail" : "Sidebar"}</span>}
        right={<span>Detalhes autorizados</span>}
        center={({ rightToggle }) => <header>{rightToggle}</header>}
      />,
    );
    const surface = container.querySelector(".delpi-ui-conversation-three-region__context-popover");
    expect(surface).toBeTruthy();
    expect(surface?.getAttribute("data-open")).toBe("false");
    expect(surface?.getAttribute("aria-hidden")).toBe("true");
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
    expect(surface?.getAttribute("data-open")).toBe("true");
    expect(screen.getByRole("dialog", { name: "Contexto da conversa" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Fechar painel de contexto" }));
    expect(surface?.getAttribute("data-open")).toBe("false");
    expect(surface?.getAttribute("aria-hidden")).toBe("true");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.queryByText("Detalhes autorizados")).toBeNull();
  });

});
