import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { NavigationCategoryPanel } from "./NavigationCategoryPanel";

afterEach(cleanup);

describe("NavigationCategoryPanel", () => {
  it("renders authorized consumer content without its own navigation, header or toggle", () => {
    const { container } = render(
      <NavigationCategoryPanel category="conversations">
        <span>Conteúdo autorizado</span>
      </NavigationCategoryPanel>,
    );
    expect(screen.getByText("Conteúdo autorizado")).toBeTruthy();
    expect(screen.getByRole("region", { name: "Conversas" })).toBeTruthy();
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(screen.queryByRole("button")).toBeNull();
    expect(container.querySelectorAll(".delpi-ui-navigation-category-panel")).toHaveLength(1);
  });

  it("shows unavailable rather than fabricating category data", () => {
    render(<NavigationCategoryPanel category="agents" state="contract_unavailable">
      <span>Não deve aparecer</span>
    </NavigationCategoryPanel>);
    expect(screen.getByText(/disponível após sua integração/)).toBeTruthy();
    expect(screen.queryByText("Não deve aparecer")).toBeNull();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("distinguishes real loading from confirmed empty", () => {
    const { rerender } = render(<NavigationCategoryPanel category="projects" state="loading" />);
    expect(screen.getByRole("status").textContent).toContain("Carregando projetos");
    rerender(<NavigationCategoryPanel category="projects" state="authorized_empty" />);
    expect(screen.queryByRole("status")).toBeNull();
    expect(screen.getByText("Nenhum conteúdo disponível nesta categoria.")).toBeTruthy();
  });

  it("offers retry only when supplied by the host", () => {
    const retry = vi.fn();
    const { rerender } = render(<NavigationCategoryPanel category="plugins" state="error" />);
    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Tentar novamente" })).toBeNull();
    rerender(<NavigationCategoryPanel category="plugins" state="error" onRetry={retry} />);
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(retry).toHaveBeenCalledTimes(1);
  });
});
