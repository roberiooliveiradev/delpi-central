import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { DeliaConversationPage } from "./DeliaConversationPage";
afterEach(cleanup);
describe("DeliaConversationPage", () => {
  it("renders one unified layout without fabricating conversation history", () => {
    const { container } = render(<DeliaConversationPage conversation={(controls) => <div>{controls.leftToggle}{controls.rightToggle}<p>Mensagem real</p></div>} />);
    const message = screen.getByText("Mensagem real");
    expect(container.querySelectorAll(".delpi-ui-conversation-three-region")).toHaveLength(1);
    expect(screen.getByRole("navigation", { name: "Conversas" })).toBeTruthy();
    expect((screen.getByRole("button", { name: "Nova conversa" }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: "Pesquisar conversas" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
    expect(screen.getByRole("heading", { name: "Detalhes" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Evidências" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Atividades" })).toBeTruthy();
    expect(screen.getByRole("complementary", { name: "Contexto da conversa" })).toBeTruthy();
    expect(container.contains(message)).toBe(true);
  });
});
