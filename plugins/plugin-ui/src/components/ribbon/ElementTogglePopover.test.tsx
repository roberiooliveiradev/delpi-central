import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { Tag } from "lucide-react";

import { ElementTogglePopover } from "./ElementTogglePopover";

describe("ElementTogglePopover", () => {
  it("off: mostra Adicionar e Opções {nome} disabled", () => {
    const onAdd = vi.fn();
    const onRemove = vi.fn();
    const onOpenOptions = vi.fn();
    const { container } = render(
      <ElementTogglePopover
        icon={Tag}
        label="Legenda"
        presence={{ enabled: false, onAdd, onRemove, onOpenOptions }}
      />,
    );
    const root = container.querySelector(".delpi-ui-element-toggle") as HTMLElement;
    fireEvent.click(within(root).getByRole("button", { name: "Legenda" }));
    const menu = screen.getByRole("menu", { name: "Ações do elemento" });
    expect(within(menu).getByRole("menuitem", { name: /Adicionar/i })).toBeTruthy();
    expect(
      (within(menu).getByRole("menuitem", { name: /Opções Legenda/i }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    fireEvent.click(within(menu).getByRole("menuitem", { name: /Adicionar/i }));
    expect(onAdd).toHaveBeenCalledTimes(1);
  });

  it("on: Remover e Opções {nome} habilitados", () => {
    const onAdd = vi.fn();
    const onRemove = vi.fn();
    const onOpenOptions = vi.fn();
    const { container } = render(
      <ElementTogglePopover
        icon={Tag}
        label="Rótulos"
        active
        presence={{ enabled: true, onAdd, onRemove, onOpenOptions }}
      />,
    );
    const root = container.querySelector(".delpi-ui-element-toggle") as HTMLElement;
    fireEvent.click(within(root).getByRole("button", { name: "Rótulos" }));
    const menu = screen.getByRole("menu", { name: "Ações do elemento" });
    expect(within(menu).getByRole("menuitem", { name: /Remover/i })).toBeTruthy();
    const options = within(menu).getByRole("menuitem", {
      name: /Opções Rótulos/i,
    }) as HTMLButtonElement;
    expect(options.disabled).toBe(false);
    fireEvent.click(options);
    expect(onOpenOptions).toHaveBeenCalledTimes(1);
  });

  it("portal bare evita borda dupla do shape-menu", () => {
    const { container } = render(
      <ElementTogglePopover
        icon={Tag}
        label="Eixos"
        presence={{
          enabled: true,
          onAdd: () => undefined,
          onRemove: () => undefined,
          onOpenOptions: () => undefined,
        }}
      />,
    );
    const root = container.querySelector(".delpi-ui-element-toggle") as HTMLElement;
    fireEvent.click(within(root).getByRole("button", { name: "Eixos" }));
    const menu = screen.getByRole("menu");
    expect(menu.className).toContain("delpi-ui-popover-surface");
    expect(menu.closest(".delpi-ui-shape-menu__panel")).toBeNull();
  });
});
