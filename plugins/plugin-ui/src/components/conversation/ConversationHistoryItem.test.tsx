import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ConversationHistoryItem } from "./ConversationHistoryItem";

afterEach(cleanup);

describe("ConversationHistoryItem", () => {
  const item = { id: "opaque-1", title: "Análise operacional", active: true };
  it("renders a real supplied title with active semantics and dispatches only intent", () => {
    const onSelect = vi.fn();
    render(<ConversationHistoryItem item={item} onSelect={onSelect} />);
    const button = screen.getByRole("button", { name: "Análise operacional" });
    expect(button.getAttribute("aria-current")).toBe("page");
    fireEvent.click(button);
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith("opaque-1");
    expect(screen.queryByRole("button", { name: /fixar|excluir|renomear/i })).toBeNull();
  });

  it("does not enable selections without a supplied callback", () => {
    render(<ConversationHistoryItem item={item} />);
    expect((screen.getByRole("button", { name: item.title }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("disables pending and stale selections, including double click", () => {
    const onSelect = vi.fn();
    const { rerender } = render(<ConversationHistoryItem item={item} pending onSelect={onSelect} />);
    const button = screen.getByRole("button", { name: item.title });
    expect(button.getAttribute("aria-busy")).toBe("true");
    fireEvent.doubleClick(button);
    expect(onSelect).not.toHaveBeenCalled();
    rerender(<ConversationHistoryItem item={item} stale onSelect={onSelect} />);
    expect((screen.getByRole("button", { name: item.title }) as HTMLButtonElement).disabled).toBe(true);
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("renders untrusted-looking titles as inert text", () => {
    const title = "<img src=x onerror=alert(1)>";
    const { container } = render(<ConversationHistoryItem item={{ id: "2", title }} onSelect={vi.fn()} />);
    expect(screen.getByRole("button", { name: title }).textContent).toBe(title);
    expect(container.querySelector("img")).toBeNull();
  });
});
