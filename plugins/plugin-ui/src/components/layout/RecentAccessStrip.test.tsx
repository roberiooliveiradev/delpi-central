import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { hubChipRowBemClasses } from "./HubChipRow";
import {
  RecentAccessStrip,
  createDashboardRecentAccessStrip,
} from "./RecentAccessStrip";
import { routeChipBemClasses } from "./RouteChip";

const CLASS_NAMES = {
  row: hubChipRowBemClasses("cm"),
  chip: routeChipBemClasses("cm"),
};

describe("RecentAccessStrip", () => {
  it("omite a faixa sem items", () => {
    const { container } = render(
      <RecentAccessStrip items={[]} onSelect={() => undefined} classNames={CLASS_NAMES} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renderiza chips e dispara onSelect", () => {
    const onSelect = vi.fn();
    render(
      <RecentAccessStrip
        classNames={CLASS_NAMES}
        items={[
          { id: "overview", label: "Visão geral" },
          { id: "help", label: "Ajuda" },
        ]}
        onSelect={onSelect}
      />,
    );
    expect(screen.getByText("Últimos acessos")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Visão geral/ }));
    expect(onSelect).toHaveBeenCalledWith("overview");
  });

  it("respeita maxVisible", () => {
    render(
      <RecentAccessStrip
        classNames={CLASS_NAMES}
        maxVisible={1}
        items={[
          { id: "a", label: "Primeiro" },
          { id: "b", label: "Segundo" },
        ]}
        onSelect={() => undefined}
      />,
    );
    expect(screen.getByText("Primeiro")).toBeTruthy();
    expect(screen.queryByText("Segundo")).toBeNull();
  });

  it("createDashboardRecentAccessStrip usa dual-class", () => {
    const Strip = createDashboardRecentAccessStrip({ prefix: "ds" });
    const { container } = render(
      <Strip items={[{ id: "home", label: "Início" }]} onSelect={() => undefined} />,
    );
    expect(container.querySelector(".delpi-ui-hub-chip-row")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-route-chip")).toBeTruthy();
  });
});
