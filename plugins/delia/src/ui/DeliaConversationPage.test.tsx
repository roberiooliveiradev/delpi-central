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
    expect(screen.getByRole("region", { name: "Conversas" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
    expect(screen.getByRole("heading", { name: "Detalhes" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Evidências" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Atividades" })).toBeTruthy();
    expect(screen.getByRole("dialog", { name: "Contexto da conversa" })).toBeTruthy();
    expect(container.contains(message)).toBe(true);
  });  it("uses a single category rail in collapsed state and preserves conversation", () => {
    const { container } = render(<DeliaConversationPage conversation={<p>Centro permanece</p>} />);
    const center = screen.getByText("Centro permanece");
    fireEvent.click(screen.getByRole("button", { name: "Recolher conversas" }));
    expect(screen.getByRole("navigation", { name: "Conversas" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Conversas" })).toBeTruthy();
    for (const name of ["Plugins"]) {
      expect((screen.getByRole("button", { name }) as HTMLButtonElement).disabled).toBe(true);
    }
    expect(container.contains(center)).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Conversas" }));
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    expect(container.contains(center)).toBe(true);
  });

  it("shows unavailable Projects preview without remounting the active conversation", () => {
    const { container } = render(<DeliaConversationPage conversation={<p>Turno preservado</p>} />);
    const stableCenter = screen.getByText("Turno preservado");
    fireEvent.click(screen.getByRole("button", { name: "Recolher conversas" }));
    const projectCategory = screen.getByRole("button", { name: "Projetos" });
    expect((projectCategory as HTMLButtonElement).disabled).toBe(false);
    fireEvent.click(projectCategory);
    expect(screen.getByRole("navigation", { name: "Projetos" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Projetos" })).toBeTruthy();
    expect(screen.getByText(/Projetos estarão disponíveis após a integração autorizada/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Novo projeto" })).toBeNull();
    expect(container.contains(stableCenter)).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Recolher conversas" }));
    fireEvent.click(screen.getByRole("button", { name: "Conversas" }));
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    expect(container.contains(stableCenter)).toBe(true);
  });

  it("shows Agents as unavailable without remounting the conversation", () => {
    const { container } = render(<DeliaConversationPage conversation={<p>Conversa mantida</p>} />);
    const center = screen.getByText("Conversa mantida");
    fireEvent.click(screen.getByRole("button", { name: "Recolher conversas" }));
    const button = screen.getByRole("button", { name: "Agentes" });
    expect((button as HTMLButtonElement).disabled).toBe(false);
    fireEvent.click(button);
    expect(screen.getByRole("navigation", { name: "Agentes" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Agentes" })).toBeTruthy();
    expect(screen.getByText(/Agentes estarão disponíveis após a integração autorizada/)).toBeTruthy();
    expect(screen.queryByRole("list")).toBeNull();
    expect(container.contains(center)).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Recolher conversas" }));
    fireEvent.click(screen.getByRole("button", { name: "Conversas" }));
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    expect(container.contains(center)).toBe(true);
  });

});
