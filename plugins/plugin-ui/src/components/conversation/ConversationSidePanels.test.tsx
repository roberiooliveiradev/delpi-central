import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ConversationSidebar } from "./ConversationSidebar";
import { ConversationSidebarSearch } from "./ConversationSidebarSearch";
import { ConversationContextPanel } from "./ConversationContextPanel";
afterEach(cleanup);

describe("ConversationSidebar and search", () => {
  it("shows all planned navigation controls but gates missing contracts", () => {
    render(<ConversationSidebar />);
    expect((screen.getByRole("button", { name: "Nova conversa" }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: "Pesquisar conversas" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    expect((screen.getByRole("button", { name: "Opções" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.queryByRole("list")).toBeNull();
  });
  it("dispatches only callbacks supplied by the host", () => {
    const onNewConversation = vi.fn();
    const onSearch = vi.fn();
    const onOptions = vi.fn();
    const onSelectConversation = vi.fn();
    render(<ConversationSidebar
      onNewConversation={onNewConversation}
      onSearch={onSearch}
      onOptions={onOptions}
      history={[{ id: "authorized-1", title: "Conversa autorizada", active: true }]}
      onSelectConversation={onSelectConversation}
    />);
    fireEvent.click(screen.getByRole("button", { name: "Nova conversa" }));
    fireEvent.click(screen.getByRole("button", { name: "Pesquisar conversas" }));
    fireEvent.click(screen.getByRole("button", { name: "Opções" }));
    fireEvent.click(screen.getByRole("button", { name: /Conversa autorizada/ }));
    expect(onNewConversation).toHaveBeenCalledTimes(1);
    expect(onSearch).toHaveBeenCalledTimes(1);
    expect(onOptions).toHaveBeenCalledTimes(1);
    expect(onSelectConversation).toHaveBeenCalledWith("authorized-1");
  });
  it("does not generate a local search when no backend callback exists", () => {
    render(<ConversationSidebarSearch />);
    expect((screen.getByRole("button", { name: "Pesquisar conversas" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.queryByRole("searchbox")).toBeNull();
  });
});

describe("ConversationContextPanel", () => {
  it("renders truthful empty details/evidence/activity sections", () => {
    render(<ConversationContextPanel />);
    expect(screen.getByRole("heading", { name: "Detalhes" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Evidências" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Atividades" })).toBeTruthy();
    expect(screen.getByText(/Selecione uma mensagem para ver mais informações/)).toBeTruthy();
    expect(screen.queryByText(/Nenhuma evidência adicional/)).toBeNull();
  });
  it("renders supplied authorized projections without inventing others", () => {
    render(<ConversationContextPanel details={<span>Detalhe autorizado</span>} />);
    expect(screen.getByText("Detalhe autorizado")).toBeTruthy();
    expect(screen.queryByText(/Selecione uma mensagem para ver mais informações/)).toBeNull();
  });
  it("renders custom sections and skips ones without content", () => {
    render(<ConversationContextPanel
      sections={[
        { id: "files", title: "Arquivos", content: <span>relatorio.pdf</span> },
        { id: "links", title: "Links" },
      ]}
    />);
    expect(screen.getByRole("heading", { name: "Arquivos" })).toBeTruthy();
    expect(screen.getByText("relatorio.pdf")).toBeTruthy();
    // An empty section keeps its heading but renders no body — and the
    // default message-scoped trio is fully replaced.
    expect(screen.getByRole("heading", { name: "Links" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Detalhes" })).toBeNull();
    expect(screen.queryByText(/Selecione uma mensagem/)).toBeNull();
  });
  it("shows only the host empty state when no section carries content", () => {
    render(<ConversationContextPanel
      sections={[]}
      emptyState="Nenhum contexto adicional vinculado a esta conversa."
    />);
    expect(screen.getByText(/Nenhum contexto adicional vinculado/)).toBeTruthy();
    expect(screen.queryByRole("heading")).toBeNull();
  });
});
