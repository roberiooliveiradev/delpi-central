import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { Tag } from "lucide-react";

import { ElementTogglePopover } from "./ElementTogglePopover";

describe("ElementTogglePopover", () => {
  it("off: mostra Adicionar e Opções disabled", () => {
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
    expect(within(menu).getByRole("menuitem", { name: "Adicionar" })).toBeTruthy();
    expect(
      (within(menu).getByRole("menuitem", { name: "Opções do item…" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    fireEvent.click(within(menu).getByRole("menuitem", { name: "Adicionar" }));
    expect(onAdd).toHaveBeenCalledTimes(1);
  });

  it("on: Remover e Opções habilitados", () => {
    const onAdd = vi.fn();
    const onRemove = vi.fn();
    const onOpenOptions = vi.fn();
    const { container } = render(
      <ElementTogglePopover
        icon={Tag}
        label="Legenda"
        active
        presence={{ enabled: true, onAdd, onRemove, onOpenOptions }}
      />,
    );
    const root = container.querySelector(".delpi-ui-element-toggle") as HTMLElement;
    fireEvent.click(within(root).getByRole("button", { name: "Legenda" }));
    const menu = screen.getByRole("menu", { name: "Ações do elemento" });
    expect(within(menu).getByRole("menuitem", { name: "Remover" })).toBeTruthy();
    const options = within(menu).getByRole("menuitem", {
      name: "Opções do item…",
    }) as HTMLButtonElement;
    expect(options.disabled).toBe(false);
    fireEvent.click(options);
    expect(onOpenOptions).toHaveBeenCalledTimes(1);
  });
});
