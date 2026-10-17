import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { NavigationActions } from "./NavigationActions";
import { ConversationSidebar } from "./ConversationSidebar";
import { ConversationThreeRegionLayout } from "./ConversationThreeRegionLayout";

afterEach(cleanup);
describe("NavigationActions", () => {
  it("keeps write/search-adjacent actions disabled without contracted callbacks", () => {
    render(<><NavigationActions action="new" /><NavigationActions action="options" /></>);
    expect((screen.getByRole("button", { name: "Nova conversa" }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: "Opções" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.queryByRole("button", { name: "Pesquisar conversas" })).toBeNull();
  });
  it("dispatches only supplied intents and keeps icon-only accessible", () => {
    const onNew = vi.fn();
    const onOptions = vi.fn();
    render(<><NavigationActions action="new" collapsed onAction={onNew} /><NavigationActions action="options" collapsed onAction={onOptions} /></>);
    fireEvent.click(screen.getByRole("button", { name: "Nova conversa" }));
    fireEvent.click(screen.getByRole("button", { name: "Opções" }));
    expect(onNew).toHaveBeenCalledTimes(1);
    expect(onOptions).toHaveBeenCalledTimes(1);
    expect(screen.queryByText("Nova conversa")).toBeNull();
  });
  it("renders exactly one semantic shell toggle per state", () => {
    const onToggle = vi.fn();
    const { rerender } = render(<NavigationActions action="toggle" expanded onAction={onToggle} />);
    const collapse = screen.getByRole("button", { name: "Recolher conversas" });
    expect(collapse.getAttribute("aria-expanded")).toBe("true");
    fireEvent.click(collapse);
    expect(onToggle).toHaveBeenCalledTimes(1);
    rerender(<NavigationActions action="toggle" expanded={false} onAction={onToggle} />);
    expect(screen.getAllByRole("button")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Expandir conversas" }).getAttribute("aria-expanded")).toBe("false");
  });
  it("reuses the extracted buttons inside one sidebar, not a second toolbar", () => {
    render(<ConversationSidebar />);
    expect(screen.getAllByRole("button", { name: "Nova conversa" })).toHaveLength(1);
    expect(screen.getAllByRole("button", { name: "Opções" })).toHaveLength(1);
    expect((screen.getByRole("button", { name: "Pesquisar conversas" }) as HTMLButtonElement).disabled).toBe(true);
  });
  it("preserves center while the same toggle collapses and expands the shell", () => {
    const { container } = render(<ConversationThreeRegionLayout left={<span>Navegação</span>} center={<p>Conversa preservada</p>} />);
    const center = screen.getByText("Conversa preservada");
    fireEvent.click(screen.getByRole("button", { name: "Recolher conversas" }));
    fireEvent.click(screen.getByRole("button", { name: "Expandir conversas" }));
    expect(container.contains(center)).toBe(true);
    expect(screen.getAllByRole("button", { name: "Recolher conversas" })).toHaveLength(1);
  });
});
