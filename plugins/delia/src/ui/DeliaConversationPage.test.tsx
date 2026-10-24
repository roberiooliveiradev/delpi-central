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
    expect(screen.getByRole("button", { name: "Conversas" })).toBeTruthy();
    expect((screen.getByRole("button", { name: "Nova conversa" }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: "Pesquisar conversas" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByRole("region", { name: "Conversas" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Abrir contexto" }));
    expect(screen.getByRole("heading", { name: "Detalhes" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Evidências" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Atividades" })).toBeTruthy();
    // RIGHTRAIL: the global panel is an integrated complementary region,
    // not a floating dialog over the conversation.
    expect(screen.getByRole("complementary", { name: "Contexto da conversa" })).toBeTruthy();
    expect(container.contains(message)).toBe(true);
  });  it("uses a single category rail in collapsed state and preserves conversation", () => {
    const { container } = render(<DeliaConversationPage conversation={<p>Centro permanece</p>} />);
    const center = screen.getByText("Centro permanece");
    fireEvent.click(screen.getByRole("button", { name: "Recolher conversas" }));
    expect(screen.queryByRole("navigation", { name: "Conversas" })).toBeNull();
    expect(screen.getByRole("button", { name: "Conversas" })).toBeTruthy();
    expect((screen.getByRole("button", { name: "Plugins" }) as HTMLButtonElement).disabled).toBe(false);
    expect(container.contains(center)).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Conversas" }));
    expect(screen.queryByRole("heading", { name: "Recentes" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    expect(container.contains(center)).toBe(true);
  });

  it("shows unavailable Projects preview without remounting the active conversation", () => {
    const { container } = render(<DeliaConversationPage conversation={<p>Turno preservado</p>} />);
    const stableCenter = screen.getByText("Turno preservado");
    expect(screen.getByRole("button", { name: "Projetos" })).toBeTruthy();
    const projectCategory = screen.getByRole("button", { name: "Projetos" });
    expect((projectCategory as HTMLButtonElement).disabled).toBe(false);
    fireEvent.click(projectCategory);
    expect(screen.getByRole("navigation", { name: "Projetos" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Projetos" })).toBeTruthy();
    expect(screen.getByText(/Projetos estarão disponíveis após a integração autorizada/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Novo projeto" })).toBeNull();
    expect(container.contains(stableCenter)).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Conversas" }));
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    expect(container.contains(stableCenter)).toBe(true);
  });

  it("shows Agents as unavailable without remounting the conversation", () => {
    const { container } = render(<DeliaConversationPage conversation={<p>Conversa mantida</p>} />);
    const center = screen.getByText("Conversa mantida");
    const button = screen.getByRole("button", { name: "Agentes" });
    expect((button as HTMLButtonElement).disabled).toBe(false);
    fireEvent.click(button);
    expect(screen.getByRole("navigation", { name: "Agentes" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Agentes" })).toBeTruthy();
    expect(screen.getByText(/Agentes estarão disponíveis após a integração autorizada/)).toBeTruthy();
    expect(screen.queryByRole("list")).toBeNull();
    expect(container.contains(center)).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Conversas" }));
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    expect(container.contains(center)).toBe(true);
  });

  it("shows Plugins as Portal-dependent preview while preserving the active conversation", () => {
    const { container } = render(<DeliaConversationPage conversation={<p>Conversa intacta</p>} />);
    const center = screen.getByText("Conversa intacta");
    expect(screen.getByRole("button", { name: "Plugins" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Plugins" }));
    expect(screen.getByRole("navigation", { name: "Plugins" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Plugins" })).toBeTruthy();
    expect(screen.getByText(/Aplicações estarão disponíveis após a integração autorizada com o Portal/)).toBeTruthy();
    expect(screen.queryByRole("list")).toBeNull();
    expect(screen.queryByRole("button", { name: /Instalar|Conectar/i })).toBeNull();
    expect(container.contains(center)).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Conversas" }));
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    expect(container.contains(center)).toBe(true);
  });

  it("E02 composes a persistent rail and one expanded panel without remounting the workspace", () => {
    const { container } = render(<DeliaConversationPage conversation={<input aria-label="Rascunho persistente" defaultValue="Não perder" />} />);
    const draft = screen.getByRole("textbox", { name: "Rascunho persistente" });
    expect(container.querySelectorAll(".delpi-ui-conversation-three-region__category-rail")).toHaveLength(1);
    expect(container.querySelectorAll(".delpi-ui-conversation-three-region__left")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Agentes" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Conversas" })).toBeTruthy();
    expect(screen.getAllByRole("button", { name: "Recolher conversas" })).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Recolher conversas" }));
    expect(container.querySelectorAll(".delpi-ui-conversation-three-region__category-rail")).toHaveLength(1);
    expect(container.querySelectorAll(".delpi-ui-conversation-three-region__left")).toHaveLength(0);
    expect(screen.getAllByRole("button", { name: "Expandir conversas" })).toHaveLength(1);
    expect(container.contains(draft)).toBe(true);
    expect((draft as HTMLInputElement).value).toBe("Não perder");
    fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
    expect(container.querySelectorAll(".delpi-ui-conversation-three-region__left")).toHaveLength(1);
    expect(container.contains(draft)).toBe(true);
  });

  it("E03 changes categories in-place without closing the expanded panel or remounting the draft", () => {
    const { container } = render(<DeliaConversationPage conversation={<input aria-label="Draft E03" defaultValue="Ainda presente" />} />);
    const draft = screen.getByRole("textbox", { name: "Draft E03" });
    const rail = container.querySelector(".delpi-ui-conversation-three-region__category-rail");
    expect(rail).toBeTruthy();
    for (const [name, message] of [
      ["Projetos", /Projetos estarão disponíveis/],
      ["Agentes", /Agentes estarão disponíveis/],
      ["Plugins", /Aplicações estarão disponíveis/],
    ] as const) {
      fireEvent.click(screen.getByRole("button", { name }));
      expect(screen.getByRole("region", { name })).toBeTruthy();
      expect(screen.getByText(message)).toBeTruthy();
      expect(screen.getByRole("button", { name }).getAttribute("aria-current")).toBe("page");
      expect(screen.getAllByRole("button", { name: "Recolher conversas" })).toHaveLength(1);
      expect(container.querySelector(".delpi-ui-conversation-three-region__category-rail")).toBe(rail);
      expect(container.contains(draft)).toBe(true);
      expect((draft as HTMLInputElement).value).toBe("Ainda presente");
    }
    fireEvent.click(screen.getByRole("button", { name: "Conversas" }));
    expect(screen.getByRole("region", { name: "Conversas" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    expect(container.contains(draft)).toBe(true);
  });

  it("E03 selects a category on the collapsed rail without expanding automatically", () => {
    const { container } = render(<DeliaConversationPage conversation={<p>Turno E03</p>} />);
    const center = screen.getByText("Turno E03");
    fireEvent.click(screen.getByRole("button", { name: "Recolher conversas" }));
    fireEvent.click(screen.getByRole("button", { name: "Agentes" }));
    expect(screen.queryByRole("region", { name: "Agentes" })).toBeNull();
    expect(screen.getByRole("button", { name: "Agentes" }).getAttribute("aria-current")).toBe("page");
    expect(screen.getAllByRole("button", { name: "Expandir conversas" })).toHaveLength(1);
    expect(container.contains(center)).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
    expect(screen.getByRole("region", { name: "Agentes" })).toBeTruthy();
    expect(screen.getByText(/Agentes estarão disponíveis após a integração autorizada/)).toBeTruthy();
    expect(container.contains(center)).toBe(true);
  });


  it("RIGHTRAIL: global context opens as an integrated right rail without overlay or light-dismiss", () => {
    const { container } = render(<DeliaConversationPage contextOpen={true} conversation={<p>Conversa real</p>} />);
    const rail = container.querySelector(".delpi-ui-conversation-three-region__right-rail");
    expect(rail).toBeTruthy();
    expect(rail?.getAttribute("data-open")).toBe("true");
    expect(rail?.getAttribute("role")).toBe("complementary");
    expect(container.querySelector(".delpi-ui-conversation-three-region__context-popover")).toBeNull();
    fireEvent.pointerDown(container.querySelector(".delpi-ui-conversation-three-region__center")!);
    expect(rail?.getAttribute("data-open")).toBe("true");
  });

});
