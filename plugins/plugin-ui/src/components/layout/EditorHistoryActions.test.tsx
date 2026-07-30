import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import {
  appendShortcutHint,
  EditorHistoryActions,
  editorModKeyLabel,
} from "./EditorHistoryActions";

describe("EditorHistoryActions", () => {
  it("appendShortcutHint não duplica", () => {
    expect(appendShortcutHint("Desfaz. Atalho: Ctrl+Z.", "Ctrl+Z")).toBe(
      "Desfaz. Atalho: Ctrl+Z.",
    );
    expect(appendShortcutHint("Desfaz.", "Ctrl+Z")).toBe("Desfaz. (Ctrl+Z)");
  });

  it("desabilita e dispara undo/redo", () => {
    const onUndo = vi.fn();
    const onRedo = vi.fn();
    render(
      <EditorHistoryActions
        canUndo
        canRedo={false}
        onUndo={onUndo}
        onRedo={onRedo}
        undoLabel="Desfazer"
        redoLabel="Refazer"
        undoHint="Desfaz"
        redoHint="Refaz"
        ariaLabel="Histórico"
        showShortcutHints={false}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Desfazer" }));
    expect(onUndo).toHaveBeenCalledTimes(1);
    expect(
      (screen.getByRole("button", { name: "Refazer" }) as HTMLButtonElement).disabled,
    ).toBe(true);
    expect(document.querySelector(".delpi-ui-editor-history")).toBeTruthy();
  });

  it("editorModKeyLabel retorna string", () => {
    expect(["Ctrl", "⌘"]).toContain(editorModKeyLabel());
  });
});
