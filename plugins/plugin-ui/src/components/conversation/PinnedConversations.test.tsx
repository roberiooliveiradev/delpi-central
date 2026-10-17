import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PinnedConversations } from "./PinnedConversations";
import { ConversationNavigation } from "./ConversationNavigation";

afterEach(cleanup);

describe("PinnedConversations", () => {
  const items = [{ id: "p1", title: "Conversa realmente fixada", active: true }];
  it("does not display pinned heading for absent items or absent selection contract", () => {
    const { rerender } = render(<PinnedConversations items={[]} onSelectConversation={vi.fn()} />);
    expect(screen.queryByRole("heading", { name: "Fixadas" })).toBeNull();
    rerender(<PinnedConversations items={items} />);
    expect(screen.queryByText(items[0].title)).toBeNull();
  });
  it("reuses the history row and dispatches only a selection intent", () => {
    const select = vi.fn();
    render(<PinnedConversations items={items} onSelectConversation={select} />);
    expect(screen.getByRole("heading", { name: "Fixadas" })).toBeTruthy();
    const row = screen.getByRole("button", { name: items[0].title });
    expect(row.getAttribute("aria-current")).toBe("page");
    fireEvent.click(row);
    expect(select).toHaveBeenCalledTimes(1);
    expect(select).toHaveBeenCalledWith("p1");
    expect(screen.queryByRole("button", { name: /desafixar|fixar|excluir|renomear/i })).toBeNull();
  });
  it("appears only above real recent and older groups in the composed navigation", () => {
    render(<ConversationNavigation status="ready" pinned={items}
      recent={[{ id: "r", title: "Recente" }]}
      older={[{ id: "o", title: "Anterior" }]}
      onSelectConversation={vi.fn()} />);
    expect(screen.getAllByRole("heading").map(el => el.textContent)).toEqual(["Fixadas", "Recentes", "Anteriores"]);
  });
});
