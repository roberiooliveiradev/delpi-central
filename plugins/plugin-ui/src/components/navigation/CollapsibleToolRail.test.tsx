import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Gauge, LayoutGrid } from "lucide-react";
import { CollapsibleToolRail } from "./CollapsibleToolRail";

afterEach(cleanup);

const groups = [
  { id: "primary", label: "Ferramentas", items: [
    { id: "a", label: "Análise", icon: <Gauge size={16}/>, statusText: "Ativo" },
    { id: "b", label: "Painel", icon: <LayoutGrid size={16}/>, disabled: true },
  ] },
  { id: "future", label: "Próximos", collapsible: true, defaultOpen: false,
    items: [{ id: "c", label: "Futuro", icon: <Gauge size={16}/> }] },
];

describe("CollapsibleToolRail", () => {
  it("shows active item, callback and disabled states without domain coupling", () => {
    const onSelect = vi.fn();
    render(<CollapsibleToolRail groups={groups} activeId="a" expanded onExpandedChange={vi.fn()} onSelect={onSelect} ariaLabel="Ferramentas" />);
    expect(screen.getByRole("navigation", { name: "Ferramentas" })).toBeTruthy();
    const active = screen.getByRole("button", { name: "Análise" });
    expect(active.getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(active);
    expect(onSelect).toHaveBeenCalledWith("a");
    fireEvent.click(screen.getByRole("button", { name: "Painel" }));
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("button", { name: "Futuro" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Próximos" }));
    expect(screen.getByRole("button", { name: "Futuro" })).toBeTruthy();
  });
  it("collapses via controlled callback and keeps accessible labels", () => {
    const onExpandedChange = vi.fn();
    const { rerender } = render(<CollapsibleToolRail groups={groups} activeId="a" expanded onExpandedChange={onExpandedChange} onSelect={vi.fn()} ariaLabel="Ferramentas" />);
    fireEvent.click(screen.getByRole("button", { name: "Recolher ferramentas" }));
    expect(onExpandedChange).toHaveBeenCalledWith(false);
    rerender(<CollapsibleToolRail groups={groups} activeId="a" expanded={false} onExpandedChange={onExpandedChange} onSelect={vi.fn()} ariaLabel="Ferramentas" />);
    expect(screen.getByRole("button", { name: "Análise" }).getAttribute("title")).toContain("Ativo");
    expect(screen.getByRole("button", { name: "Expandir ferramentas" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Análise" }).getAttribute("aria-pressed")).toBe("true");
  });
  it("appends item description to the native title tooltip", () => {
    render(<CollapsibleToolRail expanded onExpandedChange={vi.fn()} onSelect={vi.fn()} ariaLabel="Ferramentas"
      groups={[{ id: "g", items: [{ id: "a", label: "Análise", icon: <Gauge size={16}/>, statusText: "Ativo", description: "Abre a análise de capacidade." }] }]} />);
    expect(screen.getByRole("button", { name: "Análise" }).getAttribute("title"))
      .toBe("Análise — Ativo — Abre a análise de capacidade.");
  });
});
