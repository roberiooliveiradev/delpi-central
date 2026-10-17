import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PluginNavigation } from "./PluginNavigation";

afterEach(cleanup);

describe("PluginNavigation", () => {
  it("does not invent applications, links or installer actions when catalog is unavailable", () => {
    render(<PluginNavigation />);
    expect(screen.getByText(/após a integração autorizada com o Portal/)).toBeTruthy();
    expect(screen.queryByRole("list")).toBeNull();
    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.queryByRole("link")).toBeNull();
  });

  it("only dispatches the opaque identity of a host-provided authorized application", () => {
    const onOpenApplication = vi.fn();
    render(<PluginNavigation status="ready"
      items={[{ id: "authorized-1", title: "Aplicação publicada", description: "Descrição aprovada", external: true, selected: true }]}
      onOpenApplication={onOpenApplication} />);
    expect(screen.getByRole("heading", { name: "Disponíveis para você" })).toBeTruthy();
    expect(screen.getByText("Descrição aprovada")).toBeTruthy();
    const item = screen.getByRole("button", { name: "Aplicação publicada" });
    expect(item.getAttribute("aria-current")).toBe("page");
    fireEvent.click(item);
    expect(onOpenApplication).toHaveBeenCalledTimes(1);
    expect(onOpenApplication).toHaveBeenCalledWith("authorized-1");
    expect(screen.queryByRole("link")).toBeNull();
    expect(screen.queryByRole("button", { name: /instalar|conectar|executar/i })).toBeNull();
  });

  it("does not expose a catalog without an approved selection callback", () => {
    render(<PluginNavigation status="ready" items={[{ id: "x", title: "Não navegável" }]} />);
    expect(screen.queryByText("Não navegável")).toBeNull();
    expect(screen.queryByRole("list")).toBeNull();
  });

  it("distinguishes loading, authoritative empty and an error retry", () => {
    const onRetry = vi.fn();
    const { rerender } = render(<PluginNavigation status="loading" />);
    expect(screen.getByRole("status")).toBeTruthy();
    rerender(<PluginNavigation status="authorized_empty" />);
    expect(screen.getByText("Nenhuma aplicação disponível.")).toBeTruthy();
    rerender(<PluginNavigation status="error" />);
    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Tentar novamente" })).toBeNull();
    rerender(<PluginNavigation status="error" onRetry={onRetry} />);
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("treats untrusted-looking catalog labels as inert data", () => {
    const label = "<img src=x onerror=alert(1)>";
    const { container } = render(<PluginNavigation status="ready"
      items={[{ id: "safe-1", title: label }]} onOpenApplication={vi.fn()} />);
    expect(screen.getByRole("button", { name: label }).textContent).toBe(label);
    expect(container.querySelector("img")).toBeNull();
  });
});
