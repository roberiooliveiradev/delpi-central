import { fireEvent, render, screen } from "@testing-library/react";
import { Scissors } from "lucide-react";
import { describe, expect, it, vi } from "vitest";

import { ContextMenu } from "./ContextMenu";
import { ContextMenuDivider } from "./ContextMenuDivider";
import { ContextMenuItem } from "./ContextMenuItem";
import { ContextMenuToolbar } from "./ContextMenuToolbar";
import { ContextMenuToolbarButton } from "./ContextMenuToolbarButton";

describe("ContextMenu", () => {
  it("renderiza itens e dispara onSelect", () => {
    const onCut = vi.fn();
    const onClose = vi.fn();

    render(
      <ContextMenu open position={{ x: 120, y: 80 }} onClose={onClose} aria-label="Menu de teste">
        <ContextMenuToolbar aria-label="Atalhos">
          <ContextMenuToolbarButton label="Recortar" icon={Scissors} onClick={onCut} />
        </ContextMenuToolbar>
        <ContextMenuDivider />
        <ContextMenuItem label="Colar" shortcut="Ctrl+V" disabled />
      </ContextMenu>,
    );

    expect(screen.getByRole("menu", { name: "Menu de teste" })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /Colar/i })).toHaveProperty("disabled", true);

    fireEvent.click(screen.getByRole("button", { name: "Recortar" }));
    expect(onCut).toHaveBeenCalledTimes(1);
  });
});
