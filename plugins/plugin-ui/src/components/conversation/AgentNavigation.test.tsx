import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AgentNavigation } from "./AgentNavigation";

afterEach(cleanup);

describe("AgentNavigation", () => {
  it("does not invent approved agents, capabilities or launch actions", () => {
    render(<AgentNavigation />);
    expect(screen.getByText(/Agentes estarão disponíveis após a integração autorizada/)).toBeTruthy();
    expect(screen.queryByRole("list")).toBeNull();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("renders only supplied authorized projection and emits a navigation intent", () => {
    const select = vi.fn();
    render(<AgentNavigation status="ready" agents={[{ id: "approved-1", name: "Especialista autorizado", description: "Descrição aprovada", selected: true }]} onSelectAgent={select} />);
    expect(screen.getByRole("heading", { name: "Especialistas disponíveis" })).toBeTruthy();
    expect(screen.getByText("Descrição aprovada")).toBeTruthy();
    const button = screen.getByRole("button", { name: "Especialista autorizado" });
    expect(button.getAttribute("aria-current")).toBe("page");
    fireEvent.click(button);
    expect(select).toHaveBeenCalledTimes(1);
    expect(select).toHaveBeenCalledWith("approved-1");
    expect(screen.queryByRole("button", { name: /executar|instalar|favoritar/i })).toBeNull();
  });

  it("does not leak a supplied list without a selection contract", () => {
    render(<AgentNavigation status="ready" agents={[{ id: "inert", name: "Não publicado" }]} />);
    expect(screen.queryByText("Não publicado")).toBeNull();
    expect(screen.queryByRole("list")).toBeNull();
  });

  it("keeps loading, authorized empty and failed states distinct", () => {
    const retry = vi.fn();
    const { rerender } = render(<AgentNavigation status="loading" />);
    expect(screen.getByRole("status")).toBeTruthy();
    rerender(<AgentNavigation status="authorized_empty" />);
    expect(screen.getByText("Nenhum agente disponível.")).toBeTruthy();
    rerender(<AgentNavigation status="error" />);
    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Tentar novamente" })).toBeNull();
    rerender(<AgentNavigation status="error" onRetry={retry} />);
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(retry).toHaveBeenCalledTimes(1);
  });

  it("renders untrusted-looking metadata as inert text", () => {
    const name = "<img src=x onerror=alert(1)>";
    const { container } = render(<AgentNavigation status="ready" agents={[{ id: "1", name }]} onSelectAgent={vi.fn()} />);
    expect(screen.getByRole("button", { name }).textContent).toBe(name);
    expect(container.querySelector("img")).toBeNull();
  });
});
