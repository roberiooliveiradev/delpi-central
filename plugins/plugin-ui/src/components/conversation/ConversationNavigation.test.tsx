import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ConversationNavigation } from "./ConversationNavigation";

afterEach(cleanup);

describe("ConversationNavigation", () => {
  it("does not invent persisted history when backend is unavailable", () => {
    render(<ConversationNavigation />);
    expect(screen.getByText(/O histórico estará disponível quando as conversas forem persistidas/)).toBeTruthy();
    expect(screen.queryByRole("list")).toBeNull();
    expect((screen.getByRole("button", { name: "Nova conversa" }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: "Pesquisar conversas" }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("groups only authorized supplied items, with pinned before recent before older", () => {
    const select = vi.fn();
    render(<ConversationNavigation status="ready" onSelectConversation={select}
      pinned={[{ id: "pin", title: "Planejamento fixado" }]}
      recent={[{ id: "recent", title: "Análise recente", active: true }]}
      older={[{ id: "old", title: "Conversa anterior" }]}
    />);
    const headings = screen.getAllByRole("heading").map(el => el.textContent);
    expect(headings).toEqual(["Fixadas", "Recentes", "Anteriores"]);
    const active = screen.getByRole("button", { name: "Análise recente" });
    expect(active.getAttribute("aria-current")).toBe("page");
    fireEvent.click(screen.getByRole("button", { name: "Planejamento fixado" }));
    expect(select).toHaveBeenCalledExactlyOnceWith("pin");
  });

  it("omits empty groups even when a real list is available", () => {
    render(<ConversationNavigation status="ready"
      recent={[{ id: "r", title: "Conversa real" }]}
      onSelectConversation={vi.fn()} />);
    expect(screen.getByRole("heading", { name: "Recentes" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Fixadas" })).toBeNull();
    expect(screen.queryByRole("heading", { name: "Anteriores" })).toBeNull();
  });

  it("does not expose fake select controls without a selection callback", () => {
    render(<ConversationNavigation status="ready"
      recent={[{ id: "hidden", title: "Não navegável" }]} />);
    expect(screen.queryByText("Não navegável")).toBeNull();
    expect(screen.queryByRole("list")).toBeNull();
  });

  it("distinguishes confirmed empty from pending and error", () => {
    const { rerender } = render(<ConversationNavigation status="authorized_empty" />);
    expect(screen.getByText("Nenhuma conversa encontrada.")).toBeTruthy();
    rerender(<ConversationNavigation status="loading" />);
    expect(screen.getByRole("status")).toBeTruthy();
    rerender(<ConversationNavigation status="error" />);
    expect(screen.getByRole("alert")).toBeTruthy();
  });
});
