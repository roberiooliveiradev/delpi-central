import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ChartNoAxesColumnIncreasing, PackageSearch } from "lucide-react";
import { CollapsibleToolRail, NavigationCard, navigationCardBemClasses } from "./workspace-controls";

afterEach(cleanup);

describe("workspace-controls public entrypoint", () => {
  it("exports a selected featured card with a click callback", () => {
    const onClick = vi.fn();
    render(<NavigationCard
      classNames={navigationCardBemClasses("sample")}
      title="Selecionar origem"
      description="Exemplo neutro"
      icon={<PackageSearch size={25} />}
      density="featured"
      selected
      onClick={onClick}
    />);
    const card = screen.getByRole("button", { name: "Selecionar origem" });
    expect(card.getAttribute("data-density")).toBe("featured");
    expect(card.getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(card);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("uses independent controlled rail state via the closed entrypoint", () => {
    const select = vi.fn();
    render(<CollapsibleToolRail
      ariaLabel="Ferramentas"
      groups={[{ id: "tools", items: [{ id: "report", label: "Relatório", icon: <ChartNoAxesColumnIncreasing /> }] }]}
      expanded={false}
      activeId="report"
      onExpandedChange={vi.fn()}
      onSelect={select}
    />);
    const item = screen.getByRole("button", { name: "Relatório" });
    expect(item.getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(item);
    expect(select).toHaveBeenCalledWith("report");
  });
});
