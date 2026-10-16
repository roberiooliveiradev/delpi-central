import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { DeliaConversationPage } from "./DeliaConversationPage";
afterEach(cleanup);
describe("DeliaConversationPage", () => {
  it("renders one unified layout without fabricating conversation history", () => {
    const { container } = render(<DeliaConversationPage conversation={<p>Mensagem real</p>} />);
    const message = screen.getByText("Mensagem real");
    expect(container.querySelectorAll(".delpi-ui-conversation-three-region")).toHaveLength(1);
    expect(screen.getByRole("navigation", { name: "Conversas" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Nova conversa" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Pesquisar" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
    expect(screen.getByRole("complementary", { name: "Contexto da conversa" })).toBeTruthy();
    expect(container.contains(message)).toBe(true);
  });
});
