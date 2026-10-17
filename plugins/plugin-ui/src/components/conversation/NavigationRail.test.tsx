import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { NavigationRail } from "./NavigationRail";

afterEach(cleanup);
describe("NavigationRail", () => {
  it("renders four category icons without inventing available backend catalogs", () => {
    render(<NavigationRail />);
    for (const name of ["Conversas", "Projetos", "Agentes", "Plugins"]) {
      const button = screen.getByRole("button", { name });
      expect((button as HTMLButtonElement).disabled).toBe(true);
    }
    expect(screen.queryByRole("navigation")).toBeNull();
  });

  it("routes only allowed category intentions and marks the selected icon", () => {
    const onSelectCategory = vi.fn();
    render(<NavigationRail activeCategory="conversations"
      availableCategories={["conversations"]}
      onSelectCategory={onSelectCategory} />);
    const conversations = screen.getByRole("button", { name: "Conversas" });
    expect(conversations.getAttribute("aria-current")).toBe("page");
    fireEvent.click(conversations);
    expect(onSelectCategory).toHaveBeenCalledOnce();
    expect(onSelectCategory).toHaveBeenCalledWith("conversations");
    fireEvent.click(screen.getByRole("button", { name: "Projetos" }));
    expect(onSelectCategory).toHaveBeenCalledOnce();
  });

  it("does not allow a category without an actual callback", () => {
    render(<NavigationRail availableCategories={["agents", "plugins"]} />);
    expect((screen.getByRole("button", { name: "Agentes" }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: "Plugins" }) as HTMLButtonElement).disabled).toBe(true);
  });
});
