import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { Scissors } from "lucide-react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ContextMenu } from "./ContextMenu";
import { ContextMenuDivider } from "./ContextMenuDivider";
import { ContextMenuItem } from "./ContextMenuItem";
import { ContextMenuToolbar } from "./ContextMenuToolbar";
import { ContextMenuToolbarButton } from "./ContextMenuToolbarButton";

afterEach(() => {
  cleanup();
});

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
        <ContextMenuItem
          label="Excluir"
          hint="Remove o item selecionado."
          destructive
          onSelect={() => undefined}
        />
      </ContextMenu>,
    );

    expect(screen.getByRole("menu", { name: "Menu de teste" })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /Colar/i })).toHaveProperty("disabled", true);
    expect(screen.getByRole("button", { name: "Ajuda: Excluir" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Recortar" }));
    expect(onCut).toHaveBeenCalledTimes(1);
  });

  it("hintTrigger label não renderiza botão ? separado", () => {
    const onSelect = vi.fn();
    render(
      <ContextMenu open position={{ x: 40, y: 40 }} onClose={() => undefined} aria-label="Menu">
        <ContextMenuItem
          label="Editar"
          hint="Abre o formulário."
          hintTrigger="label"
          onSelect={onSelect}
        />
        <ContextMenuItem
          label="Arquivar"
          hint="Arquiva a versão."
          hintTrigger="label"
          destructive
          disabled
          onSelect={() => undefined}
        />
      </ContextMenu>,
    );

    expect(screen.queryByRole("button", { name: "Ajuda: Editar" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Ajuda: Arquivar" })).toBeNull();
    expect(screen.getByRole("menuitem", { name: /Editar/i })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /Arquivar/i })).toHaveProperty("disabled", true);

    fireEvent.click(screen.getByRole("menuitem", { name: /Editar/i }));
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it("sem hint não cria gatilho de ajuda", () => {
    render(
      <ContextMenu open position={{ x: 40, y: 40 }} onClose={() => undefined} aria-label="Menu sem ajuda">
        <ContextMenuItem label="Copiar" onSelect={() => undefined} />
      </ContextMenu>,
    );
    const menu = screen.getByRole("menu", { name: "Menu sem ajuda" });
    expect(menu.querySelector(".delpi-ui-help-tooltip__trigger")).toBeNull();
  });

  it("fecha ao clicar fora (captura, mesmo com stopPropagation)", () => {
    const onClose = vi.fn();

    render(
      <div>
        <button
          type="button"
          data-testid="outside"
          onPointerDown={(event) => event.stopPropagation()}
        >
          fora
        </button>
        <ContextMenu open position={{ x: 40, y: 40 }} onClose={onClose} aria-label="Menu">
          <ContextMenuItem label="Copiar" onSelect={() => undefined} />
        </ContextMenu>
      </div>,
    );

    document
      .querySelector('[data-testid="outside"]')!
      .dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
