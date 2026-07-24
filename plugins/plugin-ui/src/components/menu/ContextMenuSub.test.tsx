import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { Layers } from "lucide-react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ContextMenu } from "./ContextMenu";
import { ContextMenuItem } from "./ContextMenuItem";
import { ContextMenuSub } from "./ContextMenuSub";

describe("ContextMenuSub", () => {
  afterEach(async () => {
    cleanup();
    /* Esvazia close delay (120ms) / updates React pendentes após unmount. */
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 150));
    });
  });

  it("abre no hover e dispara onSelect do item filho", () => {
    const onFront = vi.fn();

    render(
      <ContextMenu open position={{ x: 80, y: 60 }} onClose={() => undefined} aria-label="Menu">
        <ContextMenuSub label="Organizar" icon={Layers}>
          <ContextMenuItem label="Trazer para a frente" onSelect={onFront} />
        </ContextMenuSub>
      </ContextMenu>,
    );

    const trigger = screen.getByRole("menuitem", { name: /Organizar/i });
    expect(trigger.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByRole("menu", { name: "Organizar" })).toBeNull();

    fireEvent.mouseEnter(trigger.parentElement!);
    expect(trigger.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByRole("menu", { name: "Organizar" })).toBeTruthy();

    fireEvent.click(screen.getByRole("menuitem", { name: /Trazer para a frente/i }));
    expect(onFront).toHaveBeenCalledTimes(1);
  });

  it("ArrowRight abre e ArrowLeft fecha o submenu", async () => {
    render(
      <ContextMenu open position={{ x: 80, y: 60 }} onClose={() => undefined} aria-label="Menu">
        <ContextMenuSub label="Agrupar">
          <ContextMenuItem label="Agrupar seleção" onSelect={() => undefined} />
        </ContextMenuSub>
      </ContextMenu>,
    );

    const trigger = screen.getByRole("menuitem", { name: /Agrupar/i });
    trigger.focus();
    fireEvent.keyDown(trigger, { key: "ArrowRight" });
    expect(await screen.findByRole("menu", { name: "Agrupar" })).toBeTruthy();

    const panel = screen.getByRole("menu", { name: "Agrupar" });
    fireEvent.keyDown(panel, { key: "ArrowLeft" });
    expect(screen.queryByRole("menu", { name: "Agrupar" })).toBeNull();
  });

  it("não abre quando disabled", () => {
    render(
      <ContextMenu open position={{ x: 80, y: 60 }} onClose={() => undefined} aria-label="Menu">
        <ContextMenuSub label="Alinhar" disabled>
          <ContextMenuItem label="Esquerda" onSelect={() => undefined} />
        </ContextMenuSub>
      </ContextMenu>,
    );

    const trigger = screen.getByRole("menuitem", { name: /Alinhar/i });
    fireEvent.mouseEnter(trigger.parentElement!);
    fireEvent.keyDown(trigger, { key: "ArrowRight" });
    expect(screen.queryByRole("menu", { name: "Alinhar" })).toBeNull();
  });

  it("flyout usa position fixed após abrir (ajuste ao viewport)", () => {
    render(
      <ContextMenu open position={{ x: 80, y: 60 }} onClose={() => undefined} aria-label="Menu">
        <ContextMenuSub label="Girar">
          <ContextMenuItem label="Girar 90°" onSelect={() => undefined} />
        </ContextMenuSub>
      </ContextMenu>,
    );

    fireEvent.mouseEnter(screen.getByRole("menuitem", { name: /Girar/i }).parentElement!);
    const panel = screen.getByRole("menu", { name: "Girar" });
    expect(panel.style.position).toBe("fixed");
    expect(panel.style.top).not.toBe("");
    expect(panel.style.left).not.toBe("");
  });
});
